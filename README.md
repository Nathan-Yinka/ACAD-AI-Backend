# Acad AI Assessment Engine

A comprehensive Django-based REST API system for managing academic assessments, featuring real-time WebSocket support, automated grading, and a robust exam session management system.

**Repository:** [https://github.com/Nathan-Yinka/ACAD-AI-Backend.git](https://github.com/Nathan-Yinka/ACAD-AI-Backend.git)

## 📋 Table of Contents

- [Quick Start - Running the Application](#-quick-start---running-the-application)
- [Overview](#-overview)
- [Features](#-features)
- [Technology Stack](#technology-stack)
- [Architecture](#-architecture)
- [API Documentation](#-api-documentation)
- [Database Schema](#database-schema)
- [Development](#development)
- [Testing](#testing)

## 🚀 Quick Start - Running the Application

### Option 1: Docker Compose (Recommended) ⭐

**Docker Compose is the easiest and recommended way to run the application.** It handles all services (Django, PostgreSQL, Redis, Celery) automatically.

**Prerequisites:**
- Docker and Docker Compose installed

**Steps:**

1. **Clone the repository**
   ```bash
   git clone https://github.com/Nathan-Yinka/ACAD-AI-Backend.git
   cd ACAD-AI-Backend
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env file if needed with your configuration
   ```
   
   The `.env` file should contain at minimum:
   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   ```

3. **Start all services**
   ```bash
   docker-compose up
   ```
   
   This will start all services in the foreground so you can see the logs. Press `Ctrl+C` to stop all services.

4. **Access the application**
   - API: http://localhost:8000/api/v1/
   - Swagger UI: http://localhost:8000/api/v1/docs
   - ReDoc: http://localhost:8000/api/v1/redoc
   - Admin: http://localhost:8000/admin

**Stop services:**
- Press `Ctrl+C` if running in foreground
- Or in another terminal: `docker-compose down`

**Benefits of Docker Compose:**
- ✅ All services configured and connected automatically
- ✅ No need to install PostgreSQL, Redis, or Python dependencies
- ✅ Consistent environment across all machines
- ✅ Easy to start/stop all services at once
- ✅ Production-ready configuration

---

### Option 2: Docker (Manual Setup)

If you prefer to manage services individually with Docker:

**Prerequisites:**
- Docker installed

**Steps:**

1. **Start Redis container**
   ```bash
   ./scripts/start-redis.sh
   # Or manually:
   docker run -d --name redis-acad-ai -p 6379:6379 redis:7-alpine
   ```

2. **Start PostgreSQL (optional, SQLite used by default)**
   ```bash
   docker run -d --name postgres-acad-ai \
     -e POSTGRES_DB=acad_ai_db \
     -e POSTGRES_USER=acad_ai_user \
     -e POSTGRES_PASSWORD=acad_ai_password \
     -p 5432:5432 \
     postgres:15
   ```

3. **Set up environment variables**
   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   DATABASE_URL=postgresql://acad_ai_user:acad_ai_password@localhost:5432/acad_ai_db
   REDIS_URL=redis://localhost:6379/0
   CELERY_BROKER_URL=redis://localhost:6379/0
   CELERY_RESULT_BACKEND=redis://localhost:6379/0
   ```

4. **Build and run Django container**
   ```bash
   docker build -t acad-ai-assessment .
   docker run -d \
     --name acad-ai-web \
     -p 8000:8000 \
     --env-file .env \
     --link redis-acad-ai:redis \
     --link postgres-acad-ai:db \
     acad-ai-assessment
   ```

---

### Option 3: Terminal/Local Development

For local development without Docker:

**Prerequisites:**
- Python 3.9+
- Redis installed and running
- PostgreSQL (optional, SQLite used by default)
- Virtual environment (recommended)

**Steps:**

1. **Clone the repository**
   ```bash
   git clone https://github.com/Nathan-Yinka/ACAD-AI-Backend.git
   cd ACAD-AI-Backend
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Create .env file with:
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   REDIS_URL=redis://localhost:6379/0
   CELERY_BROKER_URL=redis://localhost:6379/0
   CELERY_RESULT_BACKEND=redis://localhost:6379/0
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start Redis** (required for WebSockets and Celery)
   ```bash
   # Using the provided script
   ./scripts/start-redis.sh
   
   # Or manually
   redis-server
   ```

8. **Start the application**

   **Development mode (with auto-reload):**
   ```bash
   ./scripts/start-dev.sh
   ```

   **Production mode:**
   ```bash
   ./scripts/start.sh
   ```

   **Note:** The scripts automatically:
   - Check Redis connectivity
   - Wait for database
   - Run migrations
   - Start Celery worker and beat
   - Start Django with Daphne (WebSocket support)

9. **Access the application**
   - API: http://localhost:8000/api/v1/
   - Swagger UI: http://localhost:8000/api/v1/docs/
   - ReDoc: http://localhost:8000/api/v1/redoc/
   - Admin: http://localhost:8000/admin/

**Important Notes:**
- `python manage.py runserver` does NOT support WebSockets. You must use Daphne (handled by the scripts).
- Redis is required for WebSocket functionality and Celery tasks.
- Celery workers are started automatically by the scripts, but you can also run them separately if needed.

---

## 🎯 Overview

This project is a full-featured assessment engine that allows students to take exams, submit answers securely, and receive automated grading feedback. Built as a backend test task for Acad AI, the system goes beyond the basic requirements to include advanced features like real-time WebSocket communication, session management, multiple grading methods, and comprehensive admin capabilities.

### Original Requirements

The project was built based on the following requirements:

1. **Database Modeling** - Relational schema with exams, questions, submissions, and answers
2. **Secure Student Submission Endpoint** - Token-based authentication with proper permissions
3. **Automated Grading Logic** - Mock grading service with optional LLM integration
4. **API Documentation** - Swagger/OpenAPI documentation

### Extended Features

Beyond the original requirements, this implementation includes:

- ✅ Real-time WebSocket support for exam sessions
- ✅ Session-based exam taking with token management
- ✅ Background task processing with Celery
- ✅ Multiple question types (Short Answer, Essay, Multiple Choice with single/multiple selection)
- ✅ Comprehensive admin API endpoints
- ✅ Grade history tracking
- ✅ Automatic session expiration handling
- ✅ Custom authentication middleware
- ✅ Standardized API response format
- ✅ Comprehensive test coverage
- ✅ Docker support for easy deployment
- ✅ Production-ready configuration

## ✨ Features

### Core Features

- **User Authentication** - Token-based authentication (DRF Token) with registration and login
- **Exam Management** - Create, update, activate/deactivate exams with metadata
- **Question Management** - Support for multiple question types with options and scoring
- **Session-Based Exam Taking** - Secure token-based exam sessions with time limits
- **Answer Submission** - Save answers during exam session with progress tracking
- **Automated Grading** - Multiple grading methods (Mock, OpenAI, Anthropic)
- **Grade History** - Complete tracking of grading results and history
- **Real-time Updates** - WebSocket support for live session updates

### Advanced Features

- **WebSocket Integration** - Real-time communication for exam sessions
- **Session Management** - Token-based session tracking with expiration
- **Grading System** - Modular grader architecture (Mock, OpenAI, Anthropic)
- **Background Processing** - Celery integration for asynchronous operations
- **Admin Features** - Full CRUD operations for exams, questions, sessions, and grades
- **API Features** - Standardized response format, comprehensive error handling, pagination

## 🛠 Technology Stack

### Backend Framework
- **Django 4.2.7** - Web framework
- **Django REST Framework 3.14.0** - REST API framework
- **Django Channels 4.0.0** - WebSocket support
- **Daphne 4.0.0** - ASGI server for WebSockets

### Database & Caching
- **PostgreSQL** (production) / **SQLite** (development)
- **Redis** - Channel layers and Celery broker

### Task Queue
- **Celery 5.3.4** - Asynchronous task processing
- **django-celery-beat 2.5.0** - Scheduled tasks

### Grading Services
- **scikit-learn 1.3.2** - Machine learning utilities (mock grading)
- **OpenAI 1.3.5** - GPT integration
- **Anthropic 0.7.8** - Claude integration

### API Documentation
- **drf-spectacular 0.26.5** - OpenAPI 3.0 schema generation

### Other Tools
- **python-dotenv** - Environment variable management
- **WhiteNoise** - Static file serving
- **django-cors-headers** - CORS handling
- **watchfiles** - Development auto-reload

## 🏗 Architecture

### Project Structure

```
acad-ai-assessment/
├── apps/
│   ├── accounts/          # User authentication and profiles
│   ├── assessments/       # Exams, questions, sessions
│   ├── grading/           # Grading services and grade history
│   └── core/              # Shared utilities and base classes
├── config/                # Django settings and configuration
├── scripts/               # Deployment and utility scripts
├── documentation/         # API documentation (Postman collections)
└── tests/                 # Test files
```

### Key Architectural Patterns

1. **Service Layer Pattern** - Business logic separated into service classes
2. **Repository Pattern** - Data access abstracted through services
3. **Serializer Pattern** - Request/response handling via DRF serializers
4. **Middleware Pattern** - Custom authentication middleware for WebSockets
5. **Consumer Pattern** - Async WebSocket handlers using Channels

### Database Design

The system uses a normalized relational database schema with the following key entities:

- **User** - Student and admin accounts
- **Exam** - Exam definitions with metadata
- **Question** - Questions linked to exams with types and options
- **ExamSession** - Active exam attempts with timing
- **SessionToken** - Secure tokens for session access
- **StudentAnswer** - Answers saved during exam session
- **Submission** - Final submissions for grading
- **Answer** - Graded answers linked to submissions
- **GradeHistory** - Complete grading records

See [Database Schema](#database-schema) for detailed information.

## 📚 API Documentation

### Interactive Documentation

The API includes comprehensive interactive documentation:

- **Swagger UI**: http://localhost:8000/api/v1/docs/
- **ReDoc**: http://localhost:8000/api/v1/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/v1/schema/

### API Overview

The API is organized into the following endpoint groups:

- **Authentication** (`/api/v1/auth`) - Registration, login, profile management
- **Exams** (`/api/v1/exams`) - List exams, start exam sessions (students)
- **Exam Session** (`/api/v1/sessions`) - Get questions, submit answers, track progress
- **Grades** (`/api/v1/grades`) - View grade history (students)
- **Admin - Exams** (`/api/v1/admin/exams`) - CRUD operations for exams
- **Admin - Questions** (`/api/v1/admin/exams/{id}/questions`) - Manage questions
- **Admin - Sessions** (`/api/v1/admin/sessions`) - View all sessions
- **Admin - Grades** (`/api/v1/admin/grades`) - View all grades with details

### Authentication

All API endpoints (except registration and login) require authentication using Token Authentication:

```http
Authorization: Bearer <your-token>
```

Tokens are obtained from the `/api/v1/auth/login` or `/api/v1/auth/register` endpoints.

### WebSocket Connection

For real-time exam session updates, connect to the WebSocket endpoint:

```
ws://localhost:8000/ws/exam/{session_token}/?token={auth_token}
```

**Parameters:**
- `session_token` - Token from `/api/v1/exams/{id}/start` endpoint
- `auth_token` - Authentication token (query parameter)

**Events:**
- `connected` - Connection established with session state
- `pong` - Response to ping with updated state
- `session_completed` - Exam submitted/completed
- `session_expired` - Session expired or invalidated

**For detailed endpoint documentation, request/response examples, and Postman collections, see the `/documentation/` folder or visit the interactive Swagger UI at `/api/v1/docs/`.**

## 🗄 Database Schema

### Core Models

#### User (Custom)
- Extends Django's AbstractUser
- Fields: `username`, `email`, `password`, `is_student`
- Used for both students and admins

#### Exam
- `title`, `description`, `duration_minutes`, `course`
- `is_active` - Controls exam availability
- `created_at`, `updated_at`
- Related: Questions, Sessions, Submissions

#### Question
- `exam` (ForeignKey)
- `question_text`, `question_type` (SHORT_ANSWER, ESSAY, MULTIPLE_CHOICE)
- `expected_answer` - Answer key for grading
- `options` (JSONField) - For multiple choice questions
- `allow_multiple` - For multiple selection questions
- `points` - Scoring weight
- `order` - Question ordering in exam

#### ExamSession
- `student`, `exam` (ForeignKeys)
- `started_at`, `expires_at` - Session timing
- `is_completed`, `submitted_at`
- `submission_type` (MANUAL, AUTO_EXPIRED)
- `current_question_order` - Progress tracking
- Unique constraint: (student, exam) - One active session per student per exam

#### SessionToken
- `session` (ForeignKey to ExamSession)
- `token` (Unique) - Secure session token
- `created_at`, `expires_at`
- Used for secure session access

#### StudentAnswer
- `session` (ForeignKey to ExamSession)
- `question` (ForeignKey)
- `answer_text` (JSONField for multiple choice)
- `created_at`, `updated_at`
- Stores answers during exam session

#### Submission
- `student`, `exam` (ForeignKeys)
- `submitted_at`, `graded_at`
- `total_score`, `max_score`, `status`
- Final submission for grading

#### Answer
- `submission`, `question` (ForeignKeys)
- `answer_text`, `score`
- `graded_at`
- Graded answers linked to submission

#### GradeHistory
- `student`, `exam`, `session_id`
- `status` (PENDING, IN_PROGRESS, COMPLETED, FAILED)
- `total_score`, `max_score`, `percentage`
- `grading_method` (mock, openai, anthropic)
- `started_at`, `submitted_at`, `graded_at`
- Complete grading record

### Indexes

All models include appropriate database indexes for optimal query performance:
- Foreign key indexes
- Composite indexes for common query patterns
- Ordering indexes
- Status/state indexes

## 💻 Development

### Environment Variables

Key environment variables (see `.env` file):

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_SETTINGS_MODULE=config.settings.development

# Database
DATABASE_URL=sqlite:///db.sqlite3  # or PostgreSQL URL

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Grading
GRADING_SERVICE=mock  # or 'openai' or 'anthropic'
OPENAI_API_KEY=your-key  # if using OpenAI
ANTHROPIC_API_KEY=your-key  # if using Anthropic

# Admin (for Docker)
ADMIN_EMAIL=admin@example.com
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin12345
```

### Code Structure

- **Models** - Database models in `apps/*/models/`
- **Views** - API views in `apps/*/views/`
- **Serializers** - Request/response handling in `apps/*/serializers/`
- **Services** - Business logic in `apps/*/services/`
- **Tests** - Test files in `apps/*/tests/`
- **Core** - Shared utilities in `apps/core/`

## 📊 Testing

The project includes comprehensive test coverage:

- **Model Tests** - Database model validation
- **Service Tests** - Business logic testing
- **View Tests** - API endpoint testing
- **Integration Tests** - End-to-end workflows
- **WebSocket Tests** - Real-time functionality

Run tests:
```bash
python manage.py test
```

## 📝 License

This project was created as a test task for Acad AI.

## 🤝 Contributing

This is a test project. For questions or issues, please contact the development team.

---

**Built by OLudare Nathaniel Adeyinka**
