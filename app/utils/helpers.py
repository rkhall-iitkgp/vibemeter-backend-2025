import json
import os
import random
import smtplib
import string

import pandas as pd

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = 587
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


def format_response(data):
    # Helper to format API responses consistently
    return {"data": data, "status": "success"}


def send_verification_email(email: str, token: str):
    verification_link = f"http://localhost:8000/api/auth/verify/{token}"

    message = f"Subject: Verify Your Email\n\nClick the link to verify your email: {verification_link}"

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, email, message)
    except Exception as e:
        print(f"Error sending email: {e}")


def generate_random_id():
    # Generate 10 random alphanumeric characters
    return "".join(random.choices("ABCDEF" + string.digits, k=10))


def extract_columns_by_employee_id(
    file_path: str,
    employee_id: str,
    columns: list = ["Employee_ID", "P_bin", "B_bin", "E_bin", "W_bin", "V_bin"],
):
    """
    Extract specific columns from a CSV file for a given Employee ID and return them as a JSON array.

    :param file_path: The path to the CSV file.
    :param columns: The list of column names to extract.
    :param employee_id: The Employee ID to search for.
    :return: A JSON array of the extracted values for the specified Employee ID.
    """
    # Read the CSV file into a DataFrame
    df = pd.read_csv(file_path, header=0)

    # Filter the DataFrame to include only the specified columns
    print(df.columns)
    print(df[columns])
    filtered_df = df[columns]

    # Search for the row where Employee_ID matches the provided employee_id
    row_data = filtered_df[filtered_df["Employee_ID"] == employee_id]

    # If no data is found, return an appropriate message
    if row_data.empty:
        return json.dumps({"error": "Employee ID not found"})

    # Convert the row data to a dictionary (since there should be only one row, take the first one)
    row_dict = row_data.iloc[0].to_dict()

    # Return the row data as a JSON object
    return json.dumps(row_dict, indent=4)
