import pickle
import numpy as np
from sklearn.model_selection import KFold
from train_model import run_fold

# Run K-Fold cross-validation
def run_k_fold_validation(malicious, non_malicious, hyperparameters, n_splits=10):
    # Concatenate malicious and non-malicious data into one array and assign binary labels
    X = malicious + non_malicious
    y = np.concatenate((np.ones(len(malicious)), np.zeros(len(non_malicious))))
    
    # Initialize lists to store the results of each fold    
    all_f1, all_recall, all_accuracy = [], [], []
    
    # Split the data into K equally sized folds using KFold
    kf = KFold(n_splits=n_splits, shuffle=True)
    for i, (train_indices, test_indices) in enumerate(kf.split(X)):
        print(f"Running fold {i+1} of {n_splits}...")
        
        # Split the data into training and testing sets
        train_graphs = [X[index] for index in train_indices]
        train_labels = [y[index] for index in train_indices]
        test_graphs = [X[index] for index in test_indices]
        test_labels = [y[index] for index in test_indices]
        
        # Train and evaluate the model for each fold
        last_f1, last_recall, last_accuracy, graph2vec, nn = run_fold(train_graphs, test_graphs, train_labels, test_labels, hyperparameters)
        # Save mode for each fold
        # Write the best to "model.obj" as a pickled object
        print("Saving model...")
        with open("models/model_fold_{}.obj".format(i+1), "wb") as f:
            pickle.dump({"graph2vec": graph2vec, "nn": nn}, f)
        print("Done saving model.")
        # Store the results for each fold
        all_f1.append(last_f1)
        all_recall.append(last_recall)
        all_accuracy.append(last_accuracy)
    print(f"Fold {i+1} complete.")
    
    # Return the results of K-Fold cross-validation
    return (all_f1, all_recall, all_accuracy)