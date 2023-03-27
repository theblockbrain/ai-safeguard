#!/usr/bin/env python3
import karateclub as kc # a library for graph embedding algorithms
from classifier import CfgClassifier # custom classifier using Neural Network

#  Train the model on the given training data and test it on the given test data
def run_fold(train_graphs, test_graphs, train_labels, test_labels, hyperparameters):
    # Embed the training graphs using graph2vec
    print("Embedding graphs using graph2vec...")
    graph2vec = kc.graph_embedding.Graph2Vec(**hyperparameters["graph2vec"])
    # Fit the graph2vec algorithm on the training data
    graph2vec.fit(train_graphs) # Learn the embedding of the training graphs
    print("Done embedding graphs.")
    
    # Get graph embeddings for train and test data
    train_graph_vecs = graph2vec.get_embedding() # Access the existing embedding stored in the model
    test_graph_vecs = graph2vec.infer(test_graphs) # Get the embedding of a new set of graphs using the existing model
    
    # Initialize the Neural Network classifier
    nn = CfgClassifier(hyperparameters["graph2vec"]["dimensions"], hyperparameters["hidden_layers_width"])
    
    # Compensate for class imbalance and add some bias to reduce false negatives
    malicious_weight = float(train_labels.count(0.0)) / float(train_labels.count(1.0)) * hyperparameters["malicious_bias"]
    learning_rate = hyperparameters["learning_rate"]
    max_epochs = hyperparameters["max_epochs"]
    
    # Training loop
    last_f1, last_recall, last_accuracy = 0.0, 0.0, 0.0
    print("Training Neural Network...")
    for epoch in range(max_epochs):
        print("Epoch: {}".format(epoch + 1))
        print("Learning rate: {:.3f}".format(learning_rate))
        
        # Run one training epoch with the current learning rate and weights
        train_metrics, test_metrics = nn.run_epoch(train_graph_vecs, train_labels, test_graph_vecs, test_labels, learning_rate, malicious_weight)
        train_f1, train_recall, train_accuracy = train_metrics
        test_f1, test_recall, test_accuracy = test_metrics
        # Print performance metrics
        print("Test performance: f1:{:.3f}, recall:{:.3f}, accuracy:{:.3f}".format(test_f1, test_recall, test_accuracy))
        print("Train performance: f1:{:.3f}, recall:{:.3f}, accuracy:{:.3f}".format(train_f1, train_recall, train_accuracy))
        
        # Decrease learning rate
        learning_rate *= 0.995
        # If performance decreases, decrease learning rate even more
        if last_f1 > test_f1:
            learning_rate *= 0.9
        last_f1, last_recall, last_accuracy = test_f1, test_recall, test_accuracy
    
    print("Done training Neural Network.")
    # Return performance metrics
    return (last_f1, last_recall, last_accuracy, graph2vec, nn)