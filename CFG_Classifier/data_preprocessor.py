#!/usr/bin/env python3
import networkx as nx
import pygraphviz as pgv
import os
import pickle

# Takes a folder path and loads all DOT files in the folder 
# into a list of directed graphs.
def load_folder(path):
	graphs = []
	for file_name in os.listdir(path):
		if file_name.endswith(".dot"):
			graphs.append(load_file(path+file_name))
		print(f"Loaded {len(graphs)} graphs from folder {path}")
	return graphs

# Takes a file path and loads the DOT file into a directed 
# graph using the pgv.AGraph and nx.DiGraph libraries. It then converts 
# the node labels to consecutive integers for further processing.
def load_file(path):
	# Load the dot-file with pygraphviz and convert to networkx
	G = nx.DiGraph(pgv.AGraph(path, directed=True))
	print(f"Loaded {path} as a directed graph with {len(G.nodes)} nodes and {len(G.edges)} edges")
	# Nodes must be indexed by consecutive integers for graph2vec
	return nx.convert_node_labels_to_integers(G)
 
# Prepares the input files for the machine learning model.
def prepare_files():
	print("Loading files... ")
	malicious = load_folder("CFG Classifier/inputs/malicious/")
	non_malicious = load_folder("CFG Classifier/inputs/non_malicious/")
	
	with open("CFG Classifier/inputs/inputs.obj", "wb") as f:
		pickle.dump({"malicious":malicious,"non_malicious":non_malicious}, f)
	
	print("Files are ready.")

# Loads the previously prepared input files for the machine learning model.
def load_prepared_data():
	print("Loading files... ")
	with open("CFG Classifier/inputs/inputs.obj", "rb") as f:
		data = pickle.load(f)
	return (data["malicious"], data["non_malicious"])