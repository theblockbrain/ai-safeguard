import web3
import pyevmasm
from web3 import Web3

def detect_proxy(bytecode, address, rpc_url):
    # Create a Web3 object with the specified RPC endpoint
    rpc_node = Web3(web3.providers.rpc.HTTPProvider(rpc_url))

    # Disassemble the bytecode into a list of EVM instructions using pyevmasm
    ops = list(pyevmasm.evmasm.disassemble_all(bytecode))

    # Check if the bytecode is of type ERC1167
    if is_erc1167(bytecode, ops):
        return "ERC1167"

    # Check for other known proxy types
    if is_erc1967_logic(address, rpc_node):
        return "ERC1967-logic"
    if is_erc1967_beacon(address, rpc_node):
        return "ERC1967-beacon"
    if is_erc897(address, rpc_node):
        return "ERC897"
    if is_open_zepplin(address, rpc_node):
        return "OpenZepplin"
    if is_erc1822(address, rpc_node):
        return "ERC1822"
    if is_gnosis(address, rpc_node):
        return "Gnosis"
    if is_comptroller(address, rpc_node):
        return "Comptroller"

    # If no known proxy type is detected, return None
    return None


def is_gnosis(address, rpc_node):
    # Try to call the function with signature 0xa619486e at the contract's address
    # with an empty data field. If a ContractLogicError is thrown, it means the function
    # doesn't exist and the contract is not of type Gnosis.
    try:
        rpc_node.eth.call({"to": address, "data": "0xa619486e00000000000000000000000000000000000000000000000000000000"})
        return True
    except web3.exceptions.ContractLogicError:
        return False


def is_comptroller(address, rpc_node):
    # Try to call the function with signature 0xbb82aa5e at the contract's address
    # with an empty data field. If a ContractLogicError is thrown, it means the function
    # doesn't exist and the contract is not of type Comptroller.
    try:
        rpc_node.eth.call({"to": address, "data": "0xbb82aa5e00000000000000000000000000000000000000000000000000000000"})
        return True
    except web3.exceptions.ContractLogicError:
        return False


def is_erc897(address, rpc_node):
    # Try to call the function with signature 0x5c60da1b at the contract's address
    # with an empty data field. If a ContractLogicError is thrown, it means the function
    # doesn't exist and the contract is not of type ERC897.
    try:
        rpc_node.eth.call({"to": address, "data": "0x5c60da1b00000000000000000000000000000000000000000000000000000000"})
        return True
    except web3.exceptions.ContractLogicError:
        return False

def is_erc1967_logic(address, rpc_node):
	# Check if the value at the specified key in the contract's storage is non-zero.
    # If so, the contract is an ERC1967 proxy with logic contract.
	return rpc_node.eth.get_storage_at(Web3.to_checksum_address(address), 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc).hex() != "0x0000000000000000000000000000000000000000000000000000000000000000"

def is_erc1967_beacon(address, rpc_node):
    # Check if the value at the specified key in the contract's storage is non-zero.
    # If so, the contract is an ERC1967 proxy with beacon contract.
    return rpc_node.eth.get_storage_at(Web3.to_checksum_address(address), 0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50).hex() != "0x0000000000000000000000000000000000000000000000000000000000000000"


def is_open_zepplin(address, rpc_node):
    # Check if the value at the specified key in the contract's storage is non-zero.
    # If so, the contract is an OpenZepplin proxy.
    return rpc_node.eth.get_storage_at(Web3.to_checksum_address(address), 0x7050c9e0f4ca769c69bd3a8ef740bc37934f8e2c036e5a723fd8ee048ed3f8c3).hex() != "0x0000000000000000000000000000000000000000000000000000000000000000"


def is_erc1822(address, rpc_node):
    # Check if the value at the specified key in the contract's storage is non-zero.
    # If so, the contract is an ERC1822 proxy.
    return rpc_node.eth.get_storage_at(Web3.to_checksum_address(address), 0xc5f16f0fcc639fa48a6947836d9850f504798523bf8c9a3a87d5876cf622bcf7).hex() != "0x0000000000000000000000000000000000000000000000000000000000000000"


def is_erc1167(bytecode, ops):
    # Check if the bytecode matches the pattern of an ERC1167 proxy.
    # An ERC1167 proxy has the following structure:
    # - First nine bytes: 363d3d373d3d3d363d
    # - 10th instruction has an operand
    # - Middle section: 5af43d82803e903d91
    # - Last four bytes: 57fd5bf3
    if bytecode[:9] != bytes.fromhex("363d3d373d3d3d363d"):
        return False
    if bytecode[-4:] != bytes.fromhex("57fd5bf3"):
        return False
    if not ops[9].has_operand:
        return False
    if not ops[-5].has_operand:
        return False
    middle_offset = 9 + ops[9].size
    if bytecode[middle_offset:middle_offset+9] != bytes.fromhex("5af43d82803e903d91"):
        return False
    return True