from fastapi import FastAPI, WebSocket
from app.api.endpoints import employee, report, analysis
from app.sockets import chat

app = FastAPI(title="Conversational Bot for Employee Engagement")

# Include REST API routers
app.include_router(employee.router, prefix="/api/employee", tags=["Employee"])
app.include_router(report.router, prefix="/api/report", tags=["Report"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])

# WebSocket endpoint for real-time chat
@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await chat.handle_websocket(websocket)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
