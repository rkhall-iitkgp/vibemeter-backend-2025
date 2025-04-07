# Vibemeter Backend

## Overview
Vibemeter is a conversational bot platform designed for employee engagement analysis and feedback management. This FastAPI-based backend provides real-time interaction capabilities, comprehensive data analysis, and reporting features to help organizations better understand and improve employee satisfaction and engagement.

## Features
- **Conversational Interface**: Real-time chat interactions via WebSockets
- **Sentiment Analysis**: ML-powered analysis of employee feedback
- **Report Generation**: Automated generation of insights and trends
- **REST API**: Comprehensive endpoints for data access and management
- **Scalable Architecture**: Docker-ready deployment with configurable environments

## Project Structure
```
vibemeter-backend-2025/
├── app/                      # Main application package
│   ├── __init__.py
│   ├── config.py             # Configuration settings
│   ├── main.py               # Application entry point
│   ├── socket.py             # WebSocket implementation
│   ├── api/                  # API package
│   │   ├── __init__.py
│   │   └── endpoints/        # REST API endpoints
│   ├── data/                 # Data storage and management
│   ├── ml/                   # Machine learning modules
│   ├── models/               # Data models
│   └── utils/                # Utility functions
├── .env                      # Environment variables
├── .gitignore                # Git ignore patterns
├── docker-compose.yml        # Docker compose configuration
├── Dockerfile                # Docker container definition
├── Makefile                  # Make commands for common tasks
├── pyproject.toml            # Project metadata and dependencies
├── README.md                 # Project documentation
├── report-gen-fresh.py       # Report generation script
├── reportgen.py              # Report generation module
└── requirements.txt          # Python dependencies
```

## Prerequisites
- Python 3.8 or later
- pip (Python package manager)
- Docker and Docker Compose (for containerized deployment)

## Running the Application

There are two ways to set up and run the Vibemeter backend:

### 1. Local Development Setup

1. Clone the repository:
```bash
git clone https://github.com/your-organization/vibemeter-backend-2025.git
cd vibemeter-backend-2025
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env file with your configuration
```

5. Start the development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Using Docker

1. Clone the repository:
```bash
git clone https://github.com/your-organization/vibemeter-backend-2025.git
cd vibemeter-backend-2025
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env file with your configuration
```

3. Build and run with Docker Compose:
```bash
# Build and start the containers
docker-compose up --build

# Or run in background
docker-compose up -d
```

4. Alternatively, you can use the provided Makefile:
```bash
# Build and start the application
make build
make run
```

## API Documentation
Once the application is running, access the automatically generated API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## WebSocket Interface
The application provides WebSocket connections for real-time communication. Connect to:
```
ws://localhost:8000/ws/chat
```

## Report Generation
Generate employee engagement reports using:
```bash
python reportgen.py [options]
```

## Development

### Environment Variables
Key configuration options in `.env`:
- `DATABASE_URL`: Database connection string
- `API_KEY`: API authentication key
- `DEBUG`: Enable/disable debug mode
- `MODEL_PATH`: Path to ML models

### Adding New Endpoints
Place new endpoints in `app/api/endpoints/` directory following the FastAPI router pattern.

### ML Model Updates
Machine learning models are stored in the `app/ml/` directory. Update models by:
1. Placing new model files in appropriate subdirectories
2. Updating configuration in `app/config.py`

## Deployment
The application can be deployed using:

### Docker Deployment
```bash
docker build -t vibemeter-backend .
docker run -p 8000:8000 vibemeter-backend
```

### CI/CD Pipeline
The project includes GitHub Actions workflows in `.github/workflows/`:
- `ci.yml`: Runs tests and linting on pull requests
- `deploy.yml`: Handles deployment to production environments


## Contributing
1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -m 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit a pull request


## Support
For questions and support, please open an issue or contact the development team.