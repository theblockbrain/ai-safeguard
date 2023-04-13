import os
import sys, pyevmasm
from web3 import Web3
from utils.generate_cfg import generate_control_flow_graph
from evm_parser import evm_cfg
from utils import visualization
from utils.infer_models import audit_contract
from utils.scrape_bytecode import scrape_bytecode
from utils.signatures_evm import get_signatures
import logging
import coloredlogs

# create logger
# output colored logs to the console for level and message only
logger = logging.getLogger(__name__)
coloredlogs.install(level='INFO', logger=logger, fmt='[%(levelname)s]: %(message)s')

# print the help message
def help():
    print("=================================================================================================================")
    print("                                                 NB-EVM Parser                                                   ")
    print("=================================================================================================================")
    print("Usage: python3 main.py <contract_address> <--rpc> <node_url> [--bytecode] [--cfg] [--disasm] [--sigs] [--help]")
    print("Usage: python3 main.py <contact_address> [--audit]")
    print("")
    print("Examples:")
    print("python3 main.py 0x1234567890abcdef --rpc http://localhost:8545 --bytecode --cfg --disasm")
    print("python3 main.py 0x1234567890abcdef --audit")
    print("")
    print("Required:")
    print("<contract_address> : specify the contract address to parse")
    print("--rpc : specify the rpc node to use needed to scrape the bytecode from the blockchain")
    print("<node_url> : specify the url of the rpc node to use")
    print("")
    print("Options:")
    print("--bytecode : scrape bytecode from the specified node")
    print("--cfg : generate the control flow graph of the contract")
    print("--disasm : disassemble the bytecode")
    print("--sigs : extract the signatures of the contract")
    print("--audit : audit the contract")
    print("--help : show this message")
    print("")
    print("Note: The bytecode file is required for the --cfg, --disasm, and --sigs flags.")
    print("      Use the --bytecode flag to scrape bytecode first.")
    print("      The bytecode file will be saved to the contracts/<contract_address> directory.")
    print("")
    print("=================================================================================================================")
    exit(0)

# check if the user provided the correct input
def validate_input():
    # check if user provided a contract address
    if len(sys.argv) < 2:
        logger.error("No contract address provided.")
        help()
    if len(sys.argv) == 2 and sys.argv[1] == "--help":
        help()
    if len(sys.argv) == 2 and sys.argv[1] == "--audit":
        logger.error("No contract address provided.")
        help()
    if len(sys.argv) < 3:
        logger.error("No flags provided.")
        help()
    if len(sys.argv) > 2 and len(sys.argv) < 4 and sys.argv[2] != "--audit":
        logger.error("No rpc node provided.")
        logger.error("Use the --rpc flag to specify an rpc node to use (required for bytecode scraping)")
        logger.error("Example: python3 main.py 0x1234567890abcdef --rpc http://localhost:8545")
        help()

    # check if user provided an rpc node
    if "--rpc" in sys.argv and len(sys.argv) < 4:
        logger.error("No rpc node provided.")
        logger.error("Use the --rpc flag to specify an rpc node to use (required for bytecode scraping)")
        logger.error("Example: python3 main.py 0x1234567890abcdef --rpc http://localhost:8545")
        help()
    if "--rpc" in sys.argv and len(sys.argv) == 4:
        logger.error("No flags provided.")
        help()

    # check if the user used invalid flags
    for arg in sys.argv:
        if arg.startswith("--") and arg not in ["--rpc", "--bytecode", "--cfg", "--disasm", "--sigs", "--audit" , "--help"]:
            logger.error(f"Invalid flag {arg}")
            help()

# parse the command line arguments
def parse_arguments():
    # get the contract address from the command line arguments
    contract_address = sys.argv[1]
    if not Web3.is_address(contract_address):
        # use logger instead of print
        logger.error("Invalid contract address.")
    contract_dir="contracts/"+contract_address+"/"

    # check if the user wants to see the help message
    if "--help" in sys.argv:
        help()

    # get the node from the command line arguments
    if "--rpc" in sys.argv:
        node = sys.argv[sys.argv.index("--rpc")+1]
        if node is not None:
            web3 = Web3(Web3.HTTPProvider(node))
            if not web3.is_connected():
                logger.error("Invalid node.")
                logger.error("Use the --rpc flag to specify an rpc node to use (required for bytecode scraping)")
                logger.error("Example: python3 main.py 0x1234567890abcdef --rpc http://localhost:8545")
                help()

    # check if the user wants to scrape bytecode
    if "--bytecode" in sys.argv:
        scrape_bytecode(contract_address, node)
        logger.info("Bytecode scraped.")

    # check if the user wants to generate a control flow graph
    if "--cfg" in sys.argv:
        # check if the bytecode file exists
        if not os.path.exists(contract_dir+contract_address+".bin"):
            logger.error("Bytecode file does not exist.")
            logger.error("Use the --bytecode flag to scrape bytecode first.")
            exit(1)
        generate_control_flow_graph(contract_dir+contract_address+".bin",contract_dir+contract_address+".dot")

    # check if the user wants to generate a disassembly
    if "--disasm" in sys.argv:
        # check if the bytecode file exists
        if not os.path.exists(contract_dir+contract_address+".bin"):
            logger.error("Bytecode file does not exist.")
            logger.error("Use the --bytecode flag to scrape bytecode first.")
            exit(1)
        with open(contract_dir+contract_address+".bin", mode="r") as file:
            evm_bytecode = file.read()
        disassembly = pyevmasm.evmasm.disassemble(evm_bytecode)
        with open(contract_dir+contract_address+".asm", mode="w") as file:
            file.write(disassembly)
        logger.info("Disassembly saved.")

    # check if the user wants to generate a list of function signatures
    if "--sigs" in sys.argv:
        # check if the bytecode file exists
        if not os.path.exists(contract_dir+contract_address+".bin"):
            logger.error("Bytecode file does not exist.")
            logger.error("Use the --bytecode flag to scrape bytecode first.")
            exit(1)
        with open(contract_dir+contract_address+".bin", mode="r") as file:
            evm_bytecode = file.read()
        signatures = get_signatures(evm_bytecode)
        with open(contract_dir+contract_address+".sigs", mode="w") as file:
            for sig in signatures:
                file.write(sig + "\n")
        logger.info("Function signatures saved.")
    
    # check if the user wants to audit the contract
    if "--audit" in sys.argv:
        # check if the .dot file exists
        if not os.path.exists(contract_dir+contract_address+".dot"):
            logger.error("Control flow graph file does not exist.")
            logger.error("Use the --cfg flag to generate a control flow graph first.")
            exit(1)
        #if it does, run the audit using the path to the .dot file
        result= audit_contract(contract_dir+contract_address+".dot")
        # convert to %
        result = result * 100
        # print info message if higher than 50% then malicious else non malicious and print percentage
        if result > 50:
            logger.info("Contract address: {}".format(contract_address))
            logger.info("Result: {:f}%".format(result))
            logger.error("Contract is malicious")
        else:
            logger.info("Contract address: {}".format(contract_address))
            logger.info("Result: {:f}%".format(result))
            logger.info("Contract is non malicious")

# Main function
def main():
    validate_input()
    parse_arguments()

# Run the main function
if __name__ == "__main__":
    main()
    
