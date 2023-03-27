import json
import pickle
from statistics import mean
import numpy as np
import itertools
from os.path import exists
from sklearn.model_selection import KFold
import karateclub as kc
from data_preprocessor import prepare_files, load_prepared_data
from classifier import CfgClassifier
from train_model import run_fold


# Returns all possible permutations of the given parameter grid
def permutations(grid):
	keys, values = zip(*grid.items())
	return [dict(zip(keys, v)) for v in itertools.product(*values)]

# Prepare the data for the hyperparameter tuning process
def prepare_data():
    # Define the hyperparameters to be optimized
    graph2vec_param_grid = {
        "dimensions": [8, 64, 128, 256],
        "min_count": [4, 16, 32, 64],
        "epochs": [15, 20, 25],
        "wl_iterations": [2, 3, 4],
    }
    nn_param_grid = {
        "hidden_layers_width": [4, 24, 64],
        "malicious_bias": [2.0, 3.0],
        "learning_rate": [0.1, 0.01, 0.001],
        "max_epochs": [150, 200],
    }

    # Generate all possible permutations of hyperparameters
    graph2vec_permutations = permutations(graph2vec_param_grid)
    nn_permutations = permutations(nn_param_grid)

    # Prepare the required data if it does not exist
    if not exists("inputs/inputs.obj"):
        prepare_files()
    else:
        print("Prepared files already exist.")

    # Load prepared data for malicious and non-malicious
    malicious, non_malicious = load_prepared_data() 

    # Concatenate malicious and non-malicious data
    X = malicious + non_malicious
    y = np.concatenate((np.ones(len(malicious)), np.zeros(len(non_malicious))))

    return X, y, graph2vec_permutations, nn_permutations, non_malicious, malicious

# Run the hyperparameter tuning process
def runfold(X, y, n_splits, graph2vec_permutations, nn_permutations,non_malicious, malicious):
    # Store scores for each fold and permutation
    scores = []
    for _ in range(len(graph2vec_permutations)*len(nn_permutations)):
        scores.append([])
    # Split the data into K equally sized folds using KFold
    # The primary loop is over the folds rather than over the permutations because
    # This way we can reuse the same graph2vec instances for all permutations where
    # The graph2vec params are the same but the nn's aren't in each fold.
    kf = KFold(n_splits=n_splits, shuffle=True)
    for fold_i, (train_indices, test_indices) in enumerate(kf.split(X)):
        print("Running fold", fold_i+1, "of", n_splits, "...")
        # Split the data into training and testing sets
        train_graphs = [X[index] for index in train_indices]
        train_labels = [y[index] for index in train_indices]
        test_graphs = [X[index] for index in test_indices]
        test_labels = [y[index] for index in test_indices]
        
        for graph2vec_i, graph2vec_params in enumerate(graph2vec_permutations):
            # Initialize graph2vec algorithm to learn graph embeddings
            graph2vec = kc.Graph2Vec(**graph2vec_params)
            # Fit the graph2vec algorithm on the training data
            graph2vec.fit(train_graphs)
        
            # Get graph embeddings for train and test data
            train_graph_vecs = graph2vec.get_embedding()
            test_graph_vecs = graph2vec.infer(test_graphs)
            
            for nn_i, nn_params in enumerate(nn_permutations):
                perm_i = graph2vec_i*len(nn_permutations)+nn_i
                print("Fold:", fold_i+1, "/", n_splits, ", Permutation:", perm_i+1, "/", len(nn_permutations)*len(graph2vec_permutations))
                
                
                # Initialize the Neural Network classifier
                nn = CfgClassifier(graph2vec_params["dimensions"], nn_params["hidden_layers_width"])
                
                # Compensate for class imbalance and add some bias to reduce false negatives
                malicious_weight = float(len(non_malicious)) / float(len(malicious)) * nn_params["malicious_bias"]
                learning_rate = nn_params["learning_rate"]
                max_epochs = nn_params["max_epochs"]
                
                # Training loop
                last_f1, last_recall, last_accuracy = 0.0, 0.0, 0.0
                for epoch in range(max_epochs):
                    # Run one training epoch with the current learning rate and weights
                    _, test_metrics = nn.run_epoch(train_graph_vecs, train_labels , test_graph_vecs, test_labels,  learning_rate, malicious_weight)
                    f1, recall, accuracy = test_metrics
                    # Decrease learning rate
                    learning_rate *= 0.995
                    # If performance decreases, decrease learning rate even more
                    if last_f1 > f1:
                        learning_rate *= 0.9
                    last_f1 = f1
                    last_recall = recall
                    last_accuracy = accuracy
                
                scores[perm_i].append((last_f1, last_recall, last_accuracy))
    return scores, graph2vec_permutations, nn_permutations, non_malicious, malicious


# Saves the best performing model to disk
def save_best_model(scores, graph2vec_permutations, nn_permutations, non_malicious, malicious):
    # Sort the permutations by performance
    scores_sorted = []
    for i in range(len(scores)):
        scores_sorted.append(i)

    # Sort by average f1 score
    scores_sorted.sort(key=lambda v: mean(map(lambda x: x[0], scores[v])))

    for j, i in enumerate(scores_sorted):
        current_scores = scores[i]
        f1_scores = list(map(lambda x: x[0],current_scores))
        recall_scores = list(map(lambda x: x[1],current_scores))
        accuracy_scores = list(map(lambda x: x[2],current_scores))
        graph2vec_perm_index = i // len(nn_permutations)
        nn_perm_index = i % len(nn_permutations)
        
        print("=================================================================================")
        print("[      F1] min:{:.3f}, max:{:.3f}, median:{:.3f}, stdev:{:.3f}".format(min(f1_scores), max(f1_scores), np.median(f1_scores), np.std(f1_scores)))
        print("[  Recall] min:{:.3f}, max:{:.3f}, median:{:.3f}, stdev:{:.3f}".format(min(recall_scores), max(recall_scores), np.median(recall_scores), np.std(recall_scores)))
        print("[Accuracy] min:{:.3f}, max:{:.3f}, median:{:.3f}, stdev:{:.3f}".format(min(accuracy_scores), max(accuracy_scores), np.median(accuracy_scores), np.std(accuracy_scores)))
        print("=================================================================================")
        print(graph2vec_permutations[graph2vec_perm_index])
        print(nn_permutations[nn_perm_index])
        print("=================================================================================")
        
        if j+1 == len(scores_sorted):
            data = nn_permutations[nn_perm_index]
            data["graph2vec"] = graph2vec_permutations[graph2vec_perm_index]
            with open('hyperparameters.json', 'w') as f:
                json.dump(data, f)
            
            # create model from the best hyperparameters and save it to disk
            graphs = []
            labels = []

            # Add the malicious graphs to the lists with label 1.0
            for g in malicious:
                graphs.append(g)
                labels.append(1.0)

            # Add the non-malicious graphs to the lists with label 0.0
            for g in non_malicious:
                graphs.append(g)
                labels.append(0.0)
            
            _, _, _, graph2vec, nn = run_fold(graphs, [], labels, [], data)
            # Write the best to "model_best_param.obj" as a pickled object
            with open("models/model_best_param.obj", "wb") as f:
                pickle.dump({"graph2vec": graph2vec, "nn": nn}, f)


def main():
    n_splits = 5
    X, y, graph2vec_permutations, nn_permutations, non_malicious, malicious = prepare_data()
    print("Data preparation completed.")
    run_fold_scores, graph2vec_permutations, nn_permutations, non_malicious, malicious = runfold(X, y, n_splits, graph2vec_permutations, nn_permutations, non_malicious, malicious)
    print("Fold run completed.")
    save_best_model(run_fold_scores, graph2vec_permutations, nn_permutations, non_malicious, malicious)
    print("Best model saved.")
    
if __name__ == "__main__":
    main()
