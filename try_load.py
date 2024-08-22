import pickle

# Replace 'your_pickle_file.pkl' with the path to your pickle file
with open('new2.dsgn', 'rb') as file:
    data = pickle.load(file)

# Display the contents in a readable form
print(data)