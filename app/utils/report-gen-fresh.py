from reportgen import make_report


if __name__ == "__main__":
    title = "Employee Engagement & Satisfaction Report"
    subtitle = "Quarterly Analysis - Q2 2025"
    metrics = {
            "title": "Employee Engagement Score",
            "score": 78,
            "change": 5.3,
    }
                    
    issues = {"issues" : [
            "Workload: Heavy workload affecting wellness",
            "Recognition: Insufficient recognition systems",
            "Compensation: Concerns about fair compensation",
            "Work-Life: Work-life balance issues",
            "Career Growth: Limited career advancement",
            "Team Culture: Team dynamic challenges",
            "Leadership: Leadership effectiveness",
        ],
        
        # Extract values from the provided issues data
        "issue_count" : [15, 12, 14, 11, 13, 10, 12]
    }
    high_concern_employee =  {"high_concern_employees" : [
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