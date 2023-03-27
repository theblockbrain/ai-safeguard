#!/usr/bin/env python3
from matplotlib import pyplot as plt
from data_preprocessor import load_prepared_data, prepare_files # custom functions for loading and splitting the data
from os.path import exists
import validation_results
from hyperparameters import get_hyperparameters

if __name__ == "__main__":
	if not exists("CFG Classifier/inputs/inputs.obj"):
		prepare_files()
	else:
		print("Files already prepared.")

	malicious, non_malicious = load_prepared_data()
	
	validation_results.results(malicious, non_malicious, get_hyperparameters())
