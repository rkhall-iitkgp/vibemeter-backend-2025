import json
import os
import re

import pandas as pd
from dotenv import load_dotenv
from fastapi import APIRouter
from google import genai

load_dotenv()


def extract_and_parse_json(text: str):
    """
    Extracts and parses JSON from a markdown-style code block (```json ... ```).
    Returns the parsed JSON if valid, else returns None.
    """
    # Regex to extract JSON inside ```json ... ```
    match = re.search(r"(?:```json)?\s*(\{.*\}|\[.*\])\s*(?:```)?", text, re.DOTALL)

    if not match:
        print("No JSON block found.")
        return None

    json_str = match.group(1)

    try:
        parsed = json.loads(json_str)
        return parsed
    except json.JSONDecodeError as e:
        print("Invalid JSON:", e)
        return None


router = APIRouter()


@router.get("")
def analyze_employee_targeting_csv():

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    csv_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), "../..", "data", "employee_targeting_results.csv"
        )
    )

    # Read the CSV file with error handling
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        return "Error: The CSV file was not found."
    except pd.errors.EmptyDataError:
        return "Error: The CSV file is empty or invalid."

    # Convert the DataFrame into a markdown table
    try:
        context = df.to_markdown(index=False)
    except ImportError:
        return "Error: The 'tabulate' library is required for markdown conversion. Install it using 'pip install tabulate'."

    system_prompt = (
        "You are an HR analyst tasked with analyzing employee issues and suggesting actionable steps. "
        "First, analyze the provided CSV data to identify and group employees according to the issues they are facing. "
        "Then, for each issue group, generate an action plan in the following JSON format: "
        "{ "
        "'title': 'Action Title', "
        "'purpose': 'Purpose of the Action', "
        "'metric': ['Metric 1', 'Metric 2', ...], "
        "'steps': [ "
        "{ "
        "'title': 'appropriate title for the action', "
        "'description': 'description of the action' "
        "}, "
        "{ "
        "'title': 'another title for the action', "
        "'description': 'another description of the action' "
        "} "
        "] "
        "} "
        "The action plan should be tailored to address the specific issue identified for the group and help employees improve their work life. "
        "For each group, suggest 3-5 practical steps. "
        "The metrics should be measurable indicators to evaluate the effectiveness of the action."
    )

    user_prompt = (
        "Below is the csv data converted into markdown format as context containing employee information and the issues they are experiencing: "
        f"{context} "
        "Please analyze this CSV data, group the employees according to the issues they are facing, and for each issue group, generate a corresponding action plan using the JSON format specified."
    )

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            system_prompt,
            user_prompt,
        ],
    )
    extracted_json = extract_and_parse_json(response.text)
    return extracted_json
