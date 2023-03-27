import json

# This function returns the hyperparameters of the model
def get_hyperparameters():
	with open("CFG Classifier/hyperparameters.json","r") as f:
		return json.load(f)
