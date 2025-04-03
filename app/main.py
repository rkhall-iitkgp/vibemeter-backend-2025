from fastapi import FastAPI, WebSocket
from app.api.endpoints import actions, employee, report, analysis, auth, survey, questions, focus_group
from app.api.endpoints.employeeDashboard import vibemeter, profile, dashboard
from app.sockets import chat
from app.utils.db import Base, engine
from fastapi.middleware.cors import CORSMiddleware


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
app.include_router(employee.router, prefix="/api/employee", tags=["Employee"])
app.include_router(report.router, prefix="/api/report", tags=["Report"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
app.include_router(vibemeter.router, prefix="/api/vibemeter", tags=["Vibemeter"])
app.include_router(profile.router, prefix="/api/profile", tags=["Profile"])
app.include_router(
    dashboard.router, prefix="/api/dashboard", tags=["EmployeeDashboard"]
)
app.include_router(actions.router, prefix="/api/actions", tags=["Action"])
app.include_router(survey.router, prefix="/api/survey", tags=["Survey"])
app.include_router(questions.router, prefix="/api/question", tags=["Question"])
app.include_router(focus_group.router, prefix="/api/groups", tags=["FocusGroup"])

# Create database tables
Base.metadata.create_all(bind=engine)


# WebSocket endpoint for real-time chat
@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await chat.handle_websocket(websocket)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
