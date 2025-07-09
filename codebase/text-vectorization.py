import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from functools import partial
from data_processing.data_processor import DataProcessor
import pandas as pd
import time
from collections import Counter
import numpy as np
from scipy.sparse import csr_matrix
import json


def calculate_term_freq_old(data, dictionary, dict_size):
        tweets = data.iloc[:,1]
        sentiments = data.iloc[:,0]
        tfs = []

        for tweet, sentiment in zip(tweets, sentiments):
            curr_tf = [0] * dict_size
            words = tweet.split()
            word_counts = Counter(words)
            for word, count in word_counts.items():
                if word in dictionary:
                    curr_tf[dictionary[word]] = count
            
            tfs.append((sentiment, curr_tf))
        
        return tfs
                

def calculate_term_frequency(data, dictionary, dict_size):
    try:
        tweets = data.iloc[:,1].values
        sentiments = data.iloc[:,0].values
        indices = []
        indptr = [0]
        data_values = []

        
        # Process all tweets in a vectorized manner
        for i, tweet in enumerate(tweets):

            # Get word counts for the tweet
            word_counts = Counter(tweet.split())
            
            # Filter only words in dictionary
            valid_words = [(dictionary[word], count) for word, count in word_counts.items() 
                          if word in dictionary]
            
            # If valid words exist, add them to our sparse matrix construction
            if valid_words:
                # Sort by index for CSR format efficiency
                valid_words.sort(key=lambda x: x[0])
                
                # Extract indices and counts
                curr_indices, curr_counts = zip(*valid_words)
                indices.extend(curr_indices)
                data_values.extend(curr_counts)
            
            # Update indptr
            indptr.append(len(indices))
                
        # Create sparse matrix (num_tweets x dict_size)
        tf_matrix = csr_matrix((data_values, indices, indptr), 
                              shape=(len(tweets), dict_size))
        
        # Return as list of tuples (sentiment, sparse_vector)
        return tf_matrix, sentiments
    
    except Exception as e:
        print(e)
        raise

def calculate_inverse_document_frequency(dictionary, dict_size, tf_matrix):
    """Calculate IDF using the sparse matrix structure"""
    # Get document frequency for each term
    # Sum over binary occurrences (>0) for each column
    document_freq = np.array((tf_matrix > 0).sum(axis=0)).flatten()
    
    # Calculate IDF with smoothing to avoid division by zero
    # log(N/df) where N is document count
    N = tf_matrix.shape[0]  # Number of documents
    idfs = np.log(N / (document_freq + 1)) + 1  # +1 for smoothing
    
    return idfs

def calculate_tf_idf(tf_matrix, idfs):
    idfs_row = np.reshape(idfs, (1, -1))
    # Element-wise multiplication of each row with the idfs
    return tf_matrix.multiply(idfs_row)

def collect_unique_words(file_path, num_words=1000):
    # Load the entire CSV file at once
    df = pd.read_csv(file_path)
    
    # reduce unqiue words to the 20,000th most common words
    word_counts = Counter()
    for tweet in df.iloc[:,1].dropna():
        word_counts.update(tweet.split())

    # Get the top 20,000 most frequent words
    top_words = [word for word, count in word_counts.most_common(num_words)]

    return top_words

def save_tf_idf_matrix_with_labels(tf_idf_matrix, sentiments, output_file_path):
    """
    Save TF-IDF matrix with sentiment labels to CSV
    First column is sentiment, followed by all feature columns
    """
    # Check if tf_idf_matrix is already a numpy array or a sparse matrix
    if isinstance(tf_idf_matrix, np.ndarray):
        array = tf_idf_matrix
    else:
        # Convert to dense array
        array = tf_idf_matrix.toarray()
    
    # Create column names
    feature_names = [f'tws_{i}' for i in range(array.shape[1])]
    
    # Create DataFrame with all features
    df = pd.DataFrame(array, columns=feature_names)
    
    # Insert sentiment column at the beginning
    df.insert(0, "sentiment", sentiments)
    
    # Save to CSV
    df.to_csv(output_file_path, index=False)
    print(f"🟢 Saved the tf-idf matrix to {output_file_path}")

if __name__ == "__main__":
    # initialize the dictionary
    start_time = time.time()
    print(f"🟢 Starting the vectorization process...")

    # collect the unique words from the data
    dictionary = sorted(list(collect_unique_words("../data/clean-data.csv",4000)))
    dict_size = len(dictionary)

    # map each word to an index 
    word_to_index = {word: idx for idx, word in enumerate(dictionary)}
    calculate_tf_for_chunk = partial(calculate_term_frequency, dictionary=word_to_index, dict_size=dict_size)

    data = pd.read_csv("../data/clean-data.csv").dropna().head(50000)

    # calculate the term frequency for the data
    tf_matrix, sentiments = calculate_term_frequency(data, word_to_index, dict_size)
    print(f"🟢 Finished calculating the term frequency after {time.time() - start_time:.2f} seconds")

    # calculate the inverse document frequency for the data
    idfs = calculate_inverse_document_frequency(word_to_index, dict_size, tf_matrix)
    print(f"🟢 Finished calculating the inverse document frequency for {len(idfs)} tweets after {time.time() - start_time:.2f} seconds")
    
    # calculate the tf-idf for the data
    tf_idf_matrix = calculate_tf_idf(tf_matrix, idfs)
    print(f"🟢 Finished calculating the tf-idf after {time.time() - start_time:.2f} seconds")
    
    save_tf_idf_matrix_with_labels(tf_idf_matrix, sentiments, "../data/vector-data.csv")
    
    elapsed_time = time.time() - start_time
    print(f"🟢 Vectorized {len(data)} with {len(dictionary)} unique words in {elapsed_time:.2f} seconds")

