# FounderCap

[![CI](https://github.com/AINative-Studio/foundercap/actions/workflows/ci.yml/badge.svg)](https://github.com/AINative-Studio/foundercap/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/AINative-Studio/foundercap/branch/main/graph/badge.svg?token=YOUR-TOKEN-HERE)](https://codecov.io/gh/AINative-Studio/foundercap)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Startup Funding Tracker & Dashboard Automation

## Overview

FounderCap is a web-based dashboard and automated agent that tracks startup funding and status updates from LinkedIn, Crunchbase, and Google Alerts. It synchronizes data between Airtable (source of truth) and ZeroDB (optimized data store), providing real-time dashboard visualization and analytics for program managers.

## Features

- **Automated Data Collection**: Scrapes data from LinkedIn, Crunchbase, and Google Alerts
- **Change Detection**: Identifies meaningful updates and changes in startup data
- **Data Synchronization**: Keeps Airtable and ZeroDB in sync
- **Real-time Dashboard**: Provides up-to-date visualization and analytics
- **Automated Alerts**: Notifies users of important changes and updates

## Tech Stack

- **Backend**: Python with FastAPI
- **Database**: PostgreSQL
- **Caching**: Redis
- **Task Queue**: Celery
- **Frontend**: (To be determined)
- **Containerization**: Docker
- **CI/CD**: GitHub Actions

## Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL 13+
- Redis 6+
- Docker (optional)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/foundercap.git
   cd foundercap
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

4. Create a `.env` file and configure the environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Run database migrations:
   ```bash
   alembic upgrade head
   ```

### Running the Application

1. Start the development server:
   ```bash
   python -m foundercap.cli run --reload
   ```
   Or use the CLI directly:
   ```bash
   python -m app.cli run --reload
   ```

2. Access the API documentation at http://localhost:8000/docs

## Development

### Project Structure

```
foundercap/
├── app/                      # Application source code
│   ├── api/                  # API routes
│   ├── core/                 # Core functionality
│   ├── models/               # Database models
│   ├── services/             # Business logic services
│   ├── utils/                # Utility functions
│   ├── cli.py                # Command-line interface
│   └── main.py               # FastAPI application
├── tests/                    # Test files
├── alembic/                  # Database migrations
├── .env.example              # Example environment variables
├── .gitignore
├── pyproject.toml            # Project configuration
├── README.md                 # This file
└── setup.py                  # Package setup
```

### Code Style

We use the following tools to maintain code quality:

- **Black** for code formatting
- **isort** for import sorting
- **mypy** for static type checking
- **flake8** for linting

Run the following commands to ensure code quality:

```bash
black .
isort .
mypy .
flake8
```

### Testing

Run tests with pytest:

```bash
# Run all tests
pytest

# Run a specific test file
pytest tests/test_health.py -v

# Run tests with coverage report
pytest --cov=app --cov-report=term-missing
```

### Pre-commit Hooks

Install pre-commit hooks to automatically run code quality checks before each commit:

```bash
pre-commit install
```

### API Documentation

Once the application is running, you can access the following endpoints:

- **API Documentation**: http://localhost:8000/docs
- **Alternative Documentation**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/health
- **Services Health**: http://localhost:8000/api/v1/health/services

## Deployment

### Docker

Build and run the application using Docker:

```bash
# Build the Docker image
docker build -t foundercap .

# Run the container
docker run -d --name foundercap -p 8000:8000 --env-file .env foundercap
```

### Production

For production deployment, consider using:

- **Web Server**: Gunicorn with Uvicorn workers
- **Process Manager**: Systemd or Supervisor
- **Reverse Proxy**: Nginx or Traefik

Example Gunicorn command:

```bash
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Alembic](https://alembic.sqlalchemy.org/)
- [Pydantic](https://pydantic-docs.helpmanual.io/)
- [APScheduler](https://apscheduler.readthedocs.io/)

## Acknowledgments

- Built with ❤️ by AINative Studio
