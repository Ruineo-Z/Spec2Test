# Spec2Test Backend

> AI-powered API documentation testing tool backend

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🎯 Project Overview

Spec2Test is an intelligent API documentation testing tool that automatically analyzes API specifications (OpenAPI, Markdown) and generates comprehensive test cases using Large Language Models (LLMs). The backend provides robust APIs for document analysis, test generation, execution, and result reporting.

## ✨ Key Features

- **📄 Multi-format Document Support**: OpenAPI JSON/YAML, Markdown documentation
- **🤖 AI-Powered Analysis**: Intelligent document parsing and quality assessment
- **🧪 Smart Test Generation**: Automatic generation of normal, boundary, and error test cases
- **⚡ Async Test Execution**: Concurrent test running with real-time progress tracking
- **📊 Comprehensive Reporting**: Detailed analysis with failure patterns and improvement suggestions
- **🔄 Dual LLM Support**: Cloud-based (Gemini) and local (Ollama) LLM integration
- **🚀 High Performance**: Async architecture with Celery task queue

## 🏗️ Architecture

### 4-Layer Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    API Interface Layer                      │
│                   (FastAPI Routes)                         │
├─────────────────────────────────────────────────────────────┤
│                 Core Business Modules                      │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐  │
│  │  Document   │    Test     │    Test     │   Report    │  │
│  │  Analyzer   │  Generator  │  Executor   │  Analyzer   │  │
│  └─────────────┴─────────────┴─────────────┴─────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                  Shared Components                         │
│        (LLM Clients, Storage, HTTP Client)                │
├─────────────────────────────────────────────────────────────┤
│                   Data Model Layer                         │
│              (SQLAlchemy Models & Schemas)                │
└─────────────────────────────────────────────────────────────┘
```

### Core Modules
- **Document Analyzer**: Parses and validates API documentation
- **Test Generator**: Creates comprehensive test cases using LLM
- **Test Executor**: Runs tests against target APIs
- **Report Analyzer**: Analyzes results and generates insights

## 🛠️ Technology Stack

- **Web Framework**: FastAPI 0.104+
- **Database**: PostgreSQL with SQLAlchemy 2.0+
- **Task Queue**: Celery with Redis
- **LLM Integration**: Google Gemini + Ollama
- **Data Validation**: Pydantic 2.5+
- **Testing**: pytest with async support
- **Code Quality**: Black, isort, flake8, mypy

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- (Optional) Ollama for local LLM

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/deepractice-ai/spec2test.git
   cd spec2test/spec2test-backend
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Set up database**
   ```bash
   # Create database and run migrations
   alembic upgrade head
   ```

6. **Start services**
   ```bash
   # Start the API server
   uvicorn app.main:app --reload

   # Start Celery worker (in another terminal)
   celery -A app.tasks.celery_app worker --loglevel=info
   ```

## 📖 API Documentation

Once the server is running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

```
POST   /api/v1/documents/              # Upload document
GET    /api/v1/documents/{id}          # Get document info
POST   /api/v1/documents/{id}/analyze  # Analyze document
POST   /api/v1/tests/generate          # Generate test cases
POST   /api/v1/tests/{id}/execute      # Execute tests
GET    /api/v1/reports/{id}            # Get report
GET    /api/v1/tasks/{task_id}         # Check task status
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test types
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
```

## 🔧 Development

### Code Quality
```bash
# Format code
black app tests
isort app tests

# Lint code
flake8 app tests
mypy app

# Pre-commit hooks
pre-commit install
pre-commit run --all-files
```

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## 📊 Monitoring

- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:9090/metrics (if enabled)
- **Celery Monitoring**: Use Flower or Celery events

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the excellent web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) for powerful ORM capabilities
- [Celery](https://docs.celeryq.dev/) for distributed task processing
- [Google Gemini](https://ai.google.dev/) for advanced LLM capabilities

## 📞 Support

- **Documentation**: [https://spec2test.deepractice.ai](https://spec2test.deepractice.ai)
- **Issues**: [GitHub Issues](https://github.com/deepractice-ai/spec2test/issues)
- **Email**: support@deepractice.ai

---

**Made with ❤️ by the DeepPractice.ai Team**
