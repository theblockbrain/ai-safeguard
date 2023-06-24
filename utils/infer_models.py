#!/usr/bin/env python3
import os
import pickle
import torch
import networkx as nx
import pygraphviz as pgv

def load_file(path):
	# Load the dot-file with pygraphviz and convert to networkx
	G = nx.DiGraph(pgv.AGraph(path, directed=True))
	# Nodes must be indexed by consecutive integers for graph2vec
	return nx.convert_node_labels_to_integers(G)

def audit_contract(path, token_type):
	# Get the list of all model files in the "models" folder
	if token_type == 'ERC-20':
		model_dir = 'models_erc20'
	elif token_type == 'ERC-721':
		model_dir = 'models_erc721'
	else:
		raise ValueError(f"Invalid token_type: {token_type}")

	model_files = [f for f in os.listdir(model_dir) if f.startswith("model") and f.endswith("obj")]

	# Initialize lists to store the graph2vec and nn models
	graph2vecs = []
	nns = []

	# Loop through all the model files
	for model_file in model_files:
		# Load the trained model from each file
		with open(os.path.join(model_dir, model_file), "rb") as f:
			data = pickle.load(f)
		
		# Extract the graph2vec and nn models from the loaded data
		graph2vec = data["graph2vec"]
		nn = data["nn"]
		
		# Append the models to their respective lists
		graph2vecs.append(graph2vec)
		nns.append(nn)

	graph = load_file(path)

	# Initialize list to store results from this graph for all models
	graph_results = []

	# Loop through all the models
	for i, graph2vec in enumerate(graph2vecs):
		# Infer the graph vector representation using the graph2vec model
		graph_vec = graph2vec.infer([graph])
		
		# Use the nn model to predict the result from the graph vector
		result = nns[i](torch.Tensor(graph_vec))
		
		# Append the result to the list
		graph_results.append(result[0][0])
	
	# Add the combined result of all models for this graph to the results list
	# Calculate the average result
	average_result = sum(graph_results) / len(graph_results)
	
	# Calculate the majority result
	majority_result = max(set(graph_results), key=graph_results.count)

	# Choose the final result as the majority or the average
	# result = majority_result # choose majority
	result = average_result # choose average

	return result