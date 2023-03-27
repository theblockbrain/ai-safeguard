from web3 import Web3
import os

def get_bytecode(contract_address, web3):
    bytecode = web3.eth.get_code(contract_address)
    return bytecode

def save_bytecode(contract_address, bytecode):
    directory = "contracts"
    contract_dir= directory+"/"+contract_address
    if not os.path.exists(directory):
        os.makedirs(directory)
    if not os.path.exists(contract_dir):
        os.makedirs(contract_dir)
    filename = contract_address + ".bin"
    with open(f"{contract_dir}/{filename}", "w") as f:
        f.write(bytecode.hex()[2:])
    return

def scrape_bytecode(contract_address, node):
    web3 = Web3(Web3.HTTPProvider(node))
    if web3.is_address(contract_address):
        contract_address = web3.to_checksum_address(contract_address)
        bytecode = get_bytecode(contract_address, web3)
        if bytecode:
            save_bytecode(contract_address, bytecode)
        else:
            print(f"No bytecode found for contract address {contract_address}")
    else:
        print(f"Invalid contract address: {contract_address}")