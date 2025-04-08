import json
import os
import re

import pandas as pd
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from google import genai
from sqlalchemy.orm import Session

from app.models.schema import FocusGroup
from app.utils.db import get_db

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


@router.get("/{id}")
def get_focus_group_suggestions(id: str, db: Session = Depends(get_db)):
    """
    Endpoint to get focus group suggestions from the Gemini API.
    """
    try:
        focus_group = (
            db.query(FocusGroup).filter(FocusGroup.focus_group_id == id).first()
        )
        if not focus_group:
            return {"error": "Focus group not found"}
    except Exception as e:
        return {"error": f"An error occurred while fetching the focus group: {str(e)}"}

    focus_group_data = {
        "name": focus_group.name,
        "description": focus_group.description,
        "metrics": focus_group.metrics,
    }
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    system_prompt = (
        "You are an HR analyst tasked with analyzing employee issues and suggesting actionable steps. "
        "Please analyze the provided Focus Group data and understand the description and metrics. "
        "Then, for each issue group, generate an action plan in the following JSON format with purpose relvant to the focus group: "
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
        "}"
    )

    user_prompt = (
        "Below is a JSON data of Focus Group containing employee information and the issues they are experiencing. "
        f"{focus_group_data} "
        "Please analyze this  data,generate a corresponding action plan using the JSON format specified."
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


@router.get("")
def generate_suggestions(db: Session = Depends(get_db)):
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    target_groups = db.query(FocusGroup).all()
    target_groups = [
        f"Name: {group.name}\n"
        f"Focus Group ID: {group.focus_group_id}\n"
        f"Description: {group.description}"
        for group in target_groups
    ]
    target_groups = "".join(
        [f"Group {i}:\n {group}\n\n\n" for i, group in enumerate(target_groups)]
    )

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
        "'target_group': {"
        "'name': 'Exactly match the name from the provided focus groups', "
        "'focus_group_id': 'Use the exact focus_group_id that corresponds to this group' "
        "}, "
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
        "Here are the focus groups you should target - use ONLY these exact names and IDs in your response:"
        f"{target_groups}"
        "The metrics should be measurable indicators to evaluate the effectiveness of the action. Metrix name should be 2-3 words long and atleast 20 letters"
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
    if not extracted_json:
        raise HTTPException(status_code=500, detail="Internal Server Error")
    return extracted_json


@router.get("/{focus_group_id}")
def generate_suggestions_by_id(focus_group_id=str, db: Session = Depends(get_db)):
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    target_group = (
        db.query(FocusGroup).filter(FocusGroup.focus_group_id == focus_group_id).first()
    )
    target_group = (
        f"Group Name; {target_group.name}\nDescription: {target_group.description}\n\n"
    )

    system_prompt = (
        "You are an HR analyst tasked with analyzing employee issues and suggesting actionable steps. "
        "Take a look at this target group:"
        f"{target_group}"
        "Then, for this issue group, generate an array of action plan whose each element is in the following JSON format: "
        "{ "
        "'title': 'Action Title', "
        "'purpose': 'Purpose of the Action', "
        "'target_group: 'Name of target group'"
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
        "For the given group, suggest 3-5 practical steps:"
        "The metrics should be measurable indicators to evaluate the effectiveness of the action."
    )

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[system_prompt],
    )
    print(response.text)
    extracted_json = extract_and_parse_json(response.text)
    if not extracted_json:
        raise HTTPException(status_code=500, detail="Internal Server Error")
    return extracted_json
