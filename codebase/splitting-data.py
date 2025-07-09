import pandas as pd
import time
def split_data(file_path, train_size = .7, test_size = .1, val_size = .2):
    df = pd.read_csv(file_path)

    n = len(df)
    n_train = int(n * train_size)
    n_test = int(n * test_size)
    n_val = n - n_train - n_test 

    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    train_df = df.iloc[:n_train]
    test_df = df.iloc[n_train:n_train+n_test]
    val_df = df.iloc[n_train+n_test:]
    
    # save the data
    train_df.to_csv("../data/train-data.csv", index=False)
    test_df.to_csv("../data/test-data.csv", index=False)
    val_df.to_csv("../data/val-data.csv", index=False)


if __name__ == "__main__":
    start = time.time()
    split_data("../data/vector-data.csv")

    end = time.time()
    print(f"🟢 Finished splitting the data in {end - start:.2f} seconds")