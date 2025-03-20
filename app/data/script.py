import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
from tqdm import tqdm

load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")
TABLES_AND_FILES = {
    "user":"user.csv",
    "activity_tracker_dataset":"activity_tracker_dataset_cleaned.csv",
    "leave_dataset":"leave_dataset_cleaned.csv",
    "onboarding_dataset":"onboarding_dataset.csv",
    "performance_dataset":"performance_dataset.csv",
    "rewards_dataset":"rewards_dataset.csv",
    "vibemeter_dataset": "vibemeter_dataset.csv",
}

def populate_database():
    # Create a database connection
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            for table_name, file_path in TABLES_AND_FILES.items():
                print(f"Processing table: {table_name} with file: {file_path}")
                # Read the CSV file into a DataFrame
                df = pd.read_csv(file_path)

                # Convert column names to lowercase
                df.columns = map(str.lower, df.columns)

                # Insert data into the database table with progress bar
                for i in tqdm(range(0, len(df), 1000), desc=f"Inserting data into {table_name}"):
                    chunk = df.iloc[i:i+1000]
                    chunk.to_sql(table_name, con=conn, if_exists='append', index=False)

            print("All data successfully inserted into the database.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    populate_database()