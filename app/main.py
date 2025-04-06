from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints import (
    actions,
    admin_dashboard,
    analysis,
    auth,
    employee,
    focus_group,
    meetings,
    questions,
    report,
    schedule,
    suggestions,
    survey,
    ws,
)
from app.api.endpoints.employeeDashboard import dashboard, profile, vibemeter
from app.utils.db import Base, engine

app = FastAPI(title="Conversational Bot for Employee Engagement")

# allow all origins for now
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Include REST API routers
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(actions.router, prefix="/api/actions", tags=["Action"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
app.include_router(
    dashboard.router, prefix="/api/dashboard", tags=["EmployeeDashboard"]
)
app.include_router(employee.router, prefix="/api/employee", tags=["Employee"])
app.include_router(focus_group.router, prefix="/api/groups", tags=["FocusGroup"])
app.include_router(meetings.router, prefix="/api/meetings", tags=["Meetings"])
app.include_router(profile.router, prefix="/api/profile", tags=["Profile"])
app.include_router(questions.router, prefix="/api/question", tags=["Question"])
app.include_router(report.router, prefix="/api/report", tags=["Report"])
app.include_router(schedule.router, prefix="/api/schedule", tags=["Schedule"])
app.include_router(suggestions.router, prefix="/api/suggestions", tags=["Suggestions"])
app.include_router(survey.router, prefix="/api/survey", tags=["Survey"])
app.include_router(vibemeter.router, prefix="/api/vibemeter", tags=["Vibemeter"])
app.include_router(ws.router, prefix="/api/ws", tags=["WebSocket"])
app.include_router(suggestions.router, prefix="/api/suggestions", tags=["Suggestions"])
app.include_router(admin_dashboard.router, prefix="/api/admin", tags=["AdminMetrics"])

# Create database tables
Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
