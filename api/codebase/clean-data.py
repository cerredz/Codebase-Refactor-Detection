import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import re
import nltk
import numpy as np
from nltk.corpus import stopwords
from multiprocessing import Pool, cpu_count
import time
from data_processing.data_processor import DataProcessor

# Precompile regex patterns
URL_PATTERN = re.compile(r'http\S+')
MENTION_HASHTAG_PATTERN = re.compile(r'@\w+|#\w+')
EMOJI_PATTERN = re.compile(r'[^\x00-\x7F]+')
PUNCT_PATTERN = re.compile(r'[^\w\s]')
QUOTES_PATTERN = re.compile(r'["\']')

#www pattern
WWW_PATTERN = re.compile(r'www\.\S+')

def clean_text(tweet):
    """Clean a single tweet text."""
    if not isinstance(tweet, str) or len(tweet) < 10:
        return None
    
    # Apply all regex operations
    tweet = URL_PATTERN.sub('', tweet)
    tweet = MENTION_HASHTAG_PATTERN.sub('', tweet)
    tweet = ' '.join(tweet.split())  # Remove extra whitespace
    tweet = EMOJI_PATTERN.sub('', tweet)
    tweet = PUNCT_PATTERN.sub('', tweet)
    tweet = QUOTES_PATTERN.sub('', tweet)
    tweet = WWW_PATTERN.sub('', tweet)

    # Final length check
    if len(tweet) < 10:
        return None
        
    return tweet

# process a chunk of the data
def process_chunk(chunk_data):
    """Process a chunk of the dataframe."""
    chunk, chunk_id, total_chunks = chunk_data
    
    # Extract columns
    sentiment_scores = chunk.iloc[:, 0]
    tweets = chunk.iloc[:, 5]
    
    # Apply cleaning to all tweets
    cleaned_tweets = [clean_text(tweet) for tweet in tweets]
    
    # Combine results where tweets weren't filtered out
    results = []
    for i, (score, clean_tweet) in enumerate(zip(sentiment_scores, cleaned_tweets)):
        if clean_tweet is not None:
            # Check if score is valid
            try:
                score = int(score / 2)
                if score in [0, 1, 2]:
                    results.append([score, clean_tweet])
            except (ValueError, TypeError):
                pass
    
    print(f"🟢 Processed chunk {chunk_id}/{total_chunks}")
    return results

# clean the data
def clean_data(read_file_path: str, write_file_path: str, chunk_size=10000, chunk_function=process_chunk):
    """Clean data using optimized batch processing."""
    try:
        start_time = time.time()
        
        data_processor = DataProcessor(read_file_path, write_file_path)
        chunks, num_processes = data_processor.setup_chunk_processing(chunk_size)
        results = data_processor.process_chunks(chunks, num_processes, chunk_function)
        
        # Combine results from all chunks
        all_cleaned_rows = []
        for chunk_results in results:
            all_cleaned_rows.extend(chunk_results)
        
        # Write all results at once
        if all_cleaned_rows:

            df = pd.DataFrame(all_cleaned_rows, columns=['sentiment', 'tweet'])

            shuffed_df = df.sample(frac = 1, random_state=42).reset_index(drop=True)

            shuffed_df.to_csv(write_file_path, index=False)

        
        elapsed_time = time.time() - start_time
        print(f"🟢 Cleaned {len(all_cleaned_rows)} rows in {elapsed_time:.2f} seconds")
        
    except Exception as e:
        print(f"Error cleaning data: {e}")


# show the label distribution of the data (how many positive, negative, neutral values we have)
def show_label_distribution(file_path: str):
    try:
        df = pd.read_csv(file_path)

        # count how many '0' we have in the first colum of every row
        dist_counts = df.iloc[:, 0].value_counts().to_dict()
        print('Negative Tweets: ', dist_counts.get(0,0,))
        print('Positive Tweets: ', dist_counts.get(2,0))

        total_tweets = sum(dist_counts.values())
        print('Total Tweets: ', total_tweets)
    
    except Exception as e:
        print(f"Error showing label distribution: {e}")


if __name__ == "__main__":
    clean_data("../data/data.csv", "../data/clean-data.csv")
    show_label_distribution("../data/clean-data.csv")