import sys, pyevmasm
from evm_parser import evm_cfg
from CFG_utils import visualization

def main(bytecode_file, dot_file, disasm_file = None):
    # Read the hex-encoded bytecode file
    with open(bytecode_file, mode="r") as file:
        evm_bytecode = bytes.fromhex(file.read())

    # If disassembly is desired, disassemble the bytecode and save it to the specified file
    if disasm_file != None:
        disassembly = pyevmasm.evmasm.disassemble(evm_bytecode)
        with open(disasm_file, mode="w") as file:
            file.write(disassembly)

    # Generate a control flow graph
    blocks = evm_cfg.create_basic_blocks(evm_bytecode)
    graph = visualization.generate_graph(blocks)

    # Save the graph to the specified .dot file
    with open(dot_file, mode="w") as file:
        graph.dot(file)

if __name__ == "__main__":
    if len(sys.argv) == 3:
        main(sys.argv[1], sys.argv[2])
    elif len(sys.argv) == 4:
        main(sys.argv[1], sys.argv[2], sys.argv[3])
    else: 
        print("Usage:", sys.argv[0], "EVM_BYTECODE_FILE OUTPUT_FILE [OUTPUT_DISASSEMBLY]")
        exit(1)
