from datasets import load_dataset
import pandas as pd

def main():
    coverbench = load_dataset("google/coverbench")['eval']
    df = coverbench.to_pandas()
    df.to_csv('data/coverbench_dataset.csv', index=False)

if __name__ == '__main__':
    main()