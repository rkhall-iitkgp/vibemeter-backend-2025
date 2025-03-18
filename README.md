# Conversational Bot for Employee Engagement

This project implements a FastAPI backend that includes:
- **REST API endpoints** for fetching employee feedback, generating reports, and running analysis.
- **WebSocket support** for real-time conversational interactions.
- **ML modules** for analyzing sentiment and aggregating feedback data.

## Project Structure

- **app/**: Main application package.
  - **api/endpoints/**: REST endpoints.
  - **sockets/**: WebSocket handlers.
  - **ml/**: Machine learning modules.
  - **utils/**: Utility functions.
  - **data/**: Placeholder for datasets.
- **requirements.txt**: Python dependencies.
- **Dockerfile**: Container configuration.
- **setup.sh**: Bash script to create this structure.

## Running the Application

1. Install dependencies: \`pip install -r requirements.txt\`
2. Run the server: \`uvicorn app.main:app --reload\`
