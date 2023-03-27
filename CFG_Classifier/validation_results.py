#!/usr/bin/env python3
from matplotlib import pyplot as plt
from cross_validation import run_k_fold_validation
import numpy as np
import matplotlib.pyplot as plt

# Results of K-Fold cross-validation
def results(malicious, non_malicious, hyperparameters):
    f1_scores, recall_scores, accuracy_scores= run_k_fold_validation(malicious, non_malicious, hyperparameters)
    # Print the results of K-Fold cross-validation
    print("==================================== SUMMARY ====================================")
    print("[      F1] min:{:.3f}, max:{:.3f}, median:{:.3f}, stdev:{:.3f}".format(min(f1_scores), max(f1_scores), np.median(f1_scores), np.std(f1_scores)))
    print("[  Recall] min:{:.3f}, max:{:.3f}, median:{:.3f}, stdev:{:.3f}".format(min(recall_scores), max(recall_scores), np.median(recall_scores), np.std(recall_scores)))
    print("[Accuracy] min:{:.3f}, max:{:.3f}, median:{:.3f}, stdev:{:.3f}".format(min(accuracy_scores), max(accuracy_scores), np.median(accuracy_scores), np.std(accuracy_scores)))
    print("=================================================================================")
    # Plot the F1, Recall and Accuracy scores
    plt.plot(f1_scores, label='F1')
    plt.plot(recall_scores, label='Recall')
    plt.plot(accuracy_scores, label='Accuracy')
    plt.legend()
    plt.title('Model Results')
    plt.xlabel('Fold Number')
    plt.ylabel('Score')
    plt.show()
    print("=================================================================================")
    # Create boxplots for the performance metrics
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(10, 5))
    ax1.boxplot(f1_scores)
    ax1.set_title('F1 Scores')
    ax2.boxplot(recall_scores)
    ax2.set_title('Recall Scores')
    ax3.boxplot(accuracy_scores)
    ax3.set_title('Accuracy Scores')
    plt.show()