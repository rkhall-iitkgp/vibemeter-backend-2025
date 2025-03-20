import pandas as pd
import random

def preprocess_leave_dataset(file_path):
    # Read the CSV file
    df = pd.read_csv(file_path)

    # Ensure the required columns exist
    if 'Leave_Start_Date' in df.columns and 'Leave_End_Date' in df.columns:
        # Convert Leave_Start_Date and Leave_End_Date to YYYY-MM-DD format
        df['Leave_Start_Date'] = pd.to_datetime(df['Leave_Start_Date'], errors='coerce').dt.strftime('%Y-%m-%d')
        df['Leave_End_Date'] = pd.to_datetime(df['Leave_End_Date'], errors='coerce').dt.strftime('%Y-%m-%d')

        # Handle rows where the date conversion failed
        if df['Leave_Start_Date'].isnull().any() or df['Leave_End_Date'].isnull().any():
            print("Warning: Some dates could not be converted and are set to NaT.")

    else:
        print("Error: Required columns 'Leave_Start_Date' or 'Leave_End_Date' not found in the dataset.")
        return

    # Save the cleaned dataset back to a CSV file
    output_file_path = file_path.replace('.csv', '_cleaned.csv')
    df.to_csv(output_file_path, index=False)
    print(f"Processed dataset saved to {output_file_path}")

def preprocess_activity_tracker_dataset(file_path):
    # Read the CSV file
    df = pd.read_csv(file_path)

    # Ensure the required columns exist
    if 'Date' in df.columns :
        # Convert Leave_Start_Date and Leave_End_Date to YYYY-MM-DD format
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.strftime('%Y-%m-%d')

        # Handle rows where the date conversion failed
        if df['Date'].isnull().any() or df['Date'].isnull().any():
            print("Warning: Some dates could not be converted and are set to NaT.")

    else:
        print("Error: Required columns 'Date' not found in the dataset.")
        return

    # Save the cleaned dataset back to a CSV file
    output_file_path = file_path.replace('.csv', '_cleaned.csv')
    df.to_csv(output_file_path, index=False)
    print(f"Processed dataset saved to {output_file_path}")
# Example usage

def generate_user_table():
    # Read all the required datasets
    activity_tracker = pd.read_csv('activity_tracker_dataset_cleaned.csv')
    leave_dataset = pd.read_csv('leave_dataset_cleaned.csv')
    onboarding_dataset = pd.read_csv('onboarding_dataset.csv')
    performance_dataset = pd.read_csv('performance_dataset.csv')
    rewards_dataset = pd.read_csv('rewards_dataset.csv')
    vibemeter_dataset = pd.read_csv('vibemeter_dataset.csv')

    # Create a set to store unique Employee_IDs
    employee_ids = set()

    # Loop over all datasets and fetch Employee_ID
    for dataset in [activity_tracker, leave_dataset, onboarding_dataset, performance_dataset, rewards_dataset, vibemeter_dataset]:
        if 'Employee_ID' in dataset.columns:
            employee_ids.update(dataset['Employee_ID'].dropna().unique())

    # Create a new DataFrame for user.csv
    user_data = {
        'Employee_ID': list(employee_ids),
        'Email': [f'User_{i}@email.com' for i in range(1, len(employee_ids) + 1)],
        'Password': [f'Pass{random.randint(1000, 9999)}' for _ in range(len(employee_ids))]
    }
    user_df = pd.DataFrame(user_data)

    # Save the user data to a CSV file
    user_df.to_csv('user.csv', index=False)
    print("User data saved to user.csv")

    # Combine or process the datasets as needed
    print("Datasets loaded successfully.")
if __name__ == "__main__":
    preprocess_leave_dataset('leave_dataset.csv')
    preprocess_activity_tracker_dataset('activity_tracker_dataset.csv')
    generate_user_table()