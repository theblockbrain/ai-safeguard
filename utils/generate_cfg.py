from utils import evm_cfg
from utils import visualization

def generate_control_flow_graph(bytecode_file, dot_file):
    # Read the hex-encoded bytecode file
    with open(bytecode_file, mode="r") as file:
        evm_bytecode = bytes.fromhex(file.read())

    # Generate a control flow graph
    blocks = evm_cfg.create_basic_blocks(evm_bytecode)
    graph = visualization.generate_graph(blocks)

    # Save the graph to the specified .dot file
    with open(dot_file, mode="w") as file:
        graph.dot(file)

