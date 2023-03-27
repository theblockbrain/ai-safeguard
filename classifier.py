#!/usr/bin/env python3
import numpy
import torch 
import torch.nn as nn
import random
import sklearn.metrics as metrics
from torch.autograd import Variable
import torch.optim as optim

'''
A simple neural network in PyTorch to classify input data as benign or malicious.
The network has an input layer, one hidden layer (Leaky ReLU activation function), and an 
output layer (Sigmoid activation function). The network can be trained using stochastic gradient descent
(SGD) optimization. The training is done in batches of size 10, and the training data is shuffled at the 
beginning of each epoch. The performance of the network is measured by the recall, accuracy, and F1-score
and it is calculated on both the training data and the testing data.
'''
class CfgClassifier(nn.Module):
	# Initialize the model
	def __init__(self, input_dimensions, hidden_layers_width):
		super(CfgClassifier, self).__init__()
		# Define the first layer (linear)
		self.l1 = nn.Linear(input_dimensions, hidden_layers_width)
		# Define the second layer (Leaky ReLU)
		self.l2 = nn.LeakyReLU() 
		# Define the third and last layer
		self.l3 = nn.Linear(hidden_layers_width, 1) # Final layer has 1 output (0 or 1)	
	
	# Implement the forward pass of the model
	def forward(self, x):
		x = self.l1(x)
		x = self.l2(x)
		# Apply the sigmoid activation function to the output
		return torch.sigmoid(self.l3(x)) # Output is a probability between 0 and 1
	
	def run_epoch(self, train_graph_vecs, train_labels, test_graph_vecs, test_labels, learning_rate, malicious_weight):
		train_metrics = self.train(train_graph_vecs, train_labels, learning_rate, malicious_weight)
		test_metrics = self.test(test_graph_vecs, test_labels)
		return (train_metrics, test_metrics)
	
	# Train the model on a single batch of data
	def train_batch(self, data, labels, learning_rate, malicious_weight):
		var = Variable(data)
		# Create a tensor to store the weights of each example in the batch
		weights = torch.Tensor(data.size()[0],1) 
		# Assign a weight of malicious_weight to malicious examples, and a weight of 1.0 to benign examples
		for i in range(data.size()[0]):
			if labels[i] == 1.0:
				weights[i] = malicious_weight
			else:
				weights[i] = 1.0
		
		# Run the forward pass to get the model's predictions
		out = self(var)
		
		# Compute the loss using the binary cross-entropy loss, with the weights of each example taken into account
		criterion = nn.BCELoss(weight=weights)
		loss = criterion(out, labels)
		
		# Zero the gradients before the backward pass
		self.zero_grad()
		
		# Run backpropagation to update the model's parameters
		loss.backward()
		optimizer = optim.SGD(self.parameters(), lr=learning_rate)
		optimizer.step()
		
		# Return the model's predictions
		return out
	
	# Train the model on the entire training dataset
	def train(self, train_graph_vecs, train_labels, learning_rate, malicious_weight):
		# Shuffle the training data to mix up the batches
		# Zip the two lists into a single list of tuples
		temp = list(zip(train_graph_vecs, train_labels))
		# Randomly shuffle the list of tuples
		random.shuffle(temp)
		# Unzip the shuffled list of tuples back into the original lists
		a, b = zip(*temp)
		train_graph_vecs, train_labels = list(a), list(b)

		# Split dataset into batches
		batch_size = 10
		train_predictions_binary = []
		# For each batch of data, 
		for offset in range(0,len(train_graph_vecs), batch_size):
			# Convert the batch of data into a Tensor
			train_graph_vecs = numpy.array(train_graph_vecs)
			graphs = torch.Tensor(train_graph_vecs[offset:offset+batch_size])
			labels_list = train_labels[offset:offset+batch_size]
			# Convert the labels into a Tensor
			labels = torch.Tensor(labels_list).view(len(labels_list), 1)

			# Train the model on the current batch
			predictions = self.train_batch(graphs, labels, learning_rate, malicious_weight)

			# Normalize the predictions and store the results
			for prediction in predictions:
				# If the prediction is greater than 0.5, store 1.0, otherwise store 0.0
				if prediction > 0.5:
					train_predictions_binary.append(1.0)
				else:
					train_predictions_binary.append(0.0)

		# Calculate and print the metrics for the training data
		train_f1 = metrics.f1_score(train_labels, train_predictions_binary)
		train_accuracy = metrics.accuracy_score(train_labels, train_predictions_binary)
		train_recall = metrics.recall_score(train_labels, train_predictions_binary)
		return (train_f1, train_recall, train_accuracy)

	# Test the model on the test dataset
	def test(self, test_graph_vecs, test_labels):
		if len(test_graph_vecs) > 0:
			# Get the model's predictions on the test data
			prediction = self(torch.Tensor(test_graph_vecs))
			# Normalize the predictions to be either 1.0 or 0.0
			prediction_binary = []
			for value in prediction:
				if value > 0.5:
					prediction_binary.append(1.0)
				else:
					prediction_binary.append(0.0)
			
			# Calculate and print the metrics for the test data
			test_f1 = metrics.f1_score(test_labels, prediction_binary)
			test_recall = metrics.recall_score(test_labels, prediction_binary)
			test_accuracy = metrics.accuracy_score(test_labels, prediction_binary)
		else:
			test_f1, test_recall, test_accuracy = 0.0, 0.0, 0.0
			
		return (test_f1, test_recall, test_accuracy)