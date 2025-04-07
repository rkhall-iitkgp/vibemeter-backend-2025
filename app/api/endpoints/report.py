import os

from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.utils.reportgen import make_report

router = APIRouter()


@router.get("/")
async def get_daily_report():
    title = "Employee Engagement & Satisfaction Report"
    subtitle = "Daily Analysis - 2025-10-01"
    metrics = {
        "title": "Employee Engagement Score",
        "score": 78,
        "change": 5.3,
    }
    issues = {
        "issues": [
            "Workload: Heavy workload affecting wellness",
            "Recognition: Insufficient recognition systems",
            "Compensation: Concerns about fair compensation",
            "Work-Life: Work-life balance issues",
            "Career Growth: Limited career advancement",
            "Team Culture: Team dynamic challenges",
            "Leadership: Leadership effectiveness",
        ],
        "issue_count": [15, 12, 14, 11, 13, 10, 12],
    }
    high_concern_employee = {
        "high_concern_employees": [
            ["Ankan", "Leadership Training", "Needs Urgent Attention!"],
            ["Ankan", "Morality", "-28%"],
            ["Ankan", "Engagement", "-40%"],
            ["Ankan", "Leave Impact", "+38%"],
            ["Ankan", "Morality", "-18%"],
        ]
    }
    vibeMeterData = {
        "chart_data": {
            "scores": [
                {"month": "Jan", "score": 65},
                {"month": "Feb", "score": 67},
                {"month": "Mar", "score": 72},
                {"month": "Apr", "score": 78},
                {"month": "May", "score": 75},
                {"month": "Jun", "score": 85},
            ],
            "average": 78,
            "percentageChange": 5.3,
        }
    }
    # Generate the report using the provided data
    make_report(title, subtitle, metrics, issues, high_concern_employee, vibeMeterData)
    # Path to the generated PDF
    pdf_path = "employee_dashboard.pdf"

    # Check if the file exists
    if not os.path.exists(pdf_path):
        return {"error": "Report generation failed or file not found"}

    # Return the PDF file as a response
    return FileResponse(
        path=pdf_path, filename="employee_dashboard.pdf", media_type="application/pdf"
    )
