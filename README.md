# 🛡️ Iran-Israel Narrative Intelligence Platform

A comprehensive web application for analyzing conflicting narratives across news, social media, and video platforms in the Iran-Israel conflict. The platform provides real-time narrative detection, source attribution, and interactive visualizations to help users understand how information spreads across different media ecosystems.

## 🚀 Current Status

✅ **Modern Frontend** - React/Vite with clean, minimalist design system  
✅ **Backend API** - FastAPI with PostgreSQL database and JWT authentication  
✅ **Docker Deployment** - Full containerization with docker-compose  
✅ **Real-Time Data** - Live ingestion from news, social media, and video platforms  
✅ **AI-Powered Analysis** - Anthropic Claude for narrative summarization and conflict detection  
✅ **Interactive Visualizations** - Network graphs and timeline charts  
✅ **Background Processing** - Celery with Redis for async data processing  
✅ **Authentication System** - Secure user management with superuser controls  
✅ **Multi-Platform Scrapers** - Twitter/X, Reddit, YouTube, and RSS feeds  
✅ **Production Ready** - CI/CD pipeline, code quality checks, and monitoring  
🔄 **Active Development** - Enhanced conflict analysis and user customization

## ✨ Key Features

### 🔍 Narrative Detection & Analysis
- **Semantic Clustering** - Groups similar claims using advanced text embeddings
- **AI Summarization** - Claude-powered narrative summaries with conflict identification
- **Real-Time Processing** - Continuous ingestion and analysis pipeline
- **Source Attribution** - Complete tracking of content origin and engagement metrics

### 🎨 Modern User Interface
- **Clean Design System** - Minimalist, professional interface prioritizing usability
- **Interactive Dashboards** - Real-time metrics and system status indicators
- **Network Visualizations** - Interactive force-directed graphs showing source relationships
- **Timeline Analysis** - Visual representation of narrative evolution over time
- **Responsive Design** - Optimized for desktop and mobile viewing

### 🔐 Enterprise Authentication
- **JWT-Based Security** - Secure token authentication with role-based access
- **User Management** - Registration, login, and persistent sessions
- **Superuser Controls** - Administrative access for data refresh and system management
- **Route Protection** - Secure access to sensitive features and data

## 🐳 Quick Start with Docker

### One-Command Deployment

```bash
# Clone the repository
git clone <repository-url>
cd ii

# Copy and configure environment
cp env.example .env
# Edit .env with your API keys and database credentials

# Start all services
docker compose up -d

# Check status
docker compose ps
```

**Available Services:**
- **Frontend:** http://localhost:5173 - Modern React application
- **API:** http://localhost:8000 - FastAPI backend with documentation
- **API Docs:** http://localhost:8000/docs - Interactive API documentation
- **Database:** PostgreSQL with persistent storage
- **Redis:** Task queue and session management
- **Celery Worker:** Background data processing

### Development Environment

```bash
# Start development stack with hot reloading
docker compose -f docker-compose.dev.yml up -d

# Apply database migrations
docker compose exec api alembic upgrade head

# Create superuser
docker compose exec api python -c "
from app.auth import create_superuser
import asyncio
asyncio.run(create_superuser('admin@example.com', 'secure_password'))
"

# View logs
docker compose logs -f api
docker compose logs -f frontend
```

## 🔧 Configuration & Environment

### Required Environment Variables
```bash
# Database Configuration
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database

# Authentication Security
SECRET=your-jwt-secret-key-minimum-32-characters

# AI Integration
ANTHROPIC_API_KEY=sk-ant-your-api-key

# Task Queue
REDIS_URL=redis://localhost:6379/0

# Optional: Social Media APIs
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
YOUTUBE_API_KEY=your_youtube_api_key
```

## 📡 API Documentation

### Core Endpoints

**Narratives & Analysis:**
```bash
GET  /api/narratives/          # Active narrative clusters with summaries
GET  /api/narratives/timeline  # Timeline data for visualization
GET  /api/graph/              # Network graph nodes and relationships
```

**Authentication:**
```bash
POST /auth/jwt/login           # User authentication
POST /auth/jwt/logout          # Session termination
POST /auth/jwt/register        # New user registration
GET  /auth/jwt/me             # Current user information
```

**Administrative:**
```bash
POST /api/refresh             # Trigger background data processing (superuser)
GET  /health                  # System health and status
```

## 🏗️ Technical Architecture

### Core Technologies
- **Backend:** FastAPI with async/await, SQLAlchemy ORM, Alembic migrations
- **Frontend:** React 18 + Vite, modern CSS with custom design system, React Router
- **Database:** PostgreSQL with optimized indexing and query performance
- **Caching:** Redis for session management and task queue coordination
- **AI Integration:** Anthropic Claude for natural language processing and analysis
- **Authentication:** FastAPI Users with bcrypt password hashing and JWT tokens

### Data Processing Pipeline
- **NLP Stack:** sentence-transformers, HDBSCAN clustering, scikit-learn
- **Background Tasks:** Celery for distributed task processing
- **Real-Time Updates:** WebSocket support for live data feeds
- **Monitoring:** Comprehensive logging and health check endpoints

### Architecture Overview
```
ii/
├── app/                     # Backend FastAPI application
│   ├── api/                # REST API endpoints and routing
│   ├── auth.py             # Authentication and user management
│   ├── models.py           # Database models and schemas
│   ├── scrapers/           # Multi-platform data collection
│   ├── nlp/                # Natural language processing
│   ├── tasks.py            # Celery background tasks
│   └── worker.py           # Task queue worker configuration
├── frontend/               # React frontend application
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── pages/          # Application pages and routing
│   │   ├── stores/         # Zustand state management
│   │   └── hooks/          # Custom React hooks
│   ├── public/             # Static assets
│   └── package.json        # Node.js dependencies
├── migrations/             # Database migration files
├── docker-compose.yml      # Production Docker configuration
├── docker-compose.dev.yml  # Development Docker configuration
├── Dockerfile              # Backend container definition
└── requirements.txt        # Python dependencies
```

Built with ❤️ for understanding complex geopolitical narratives through data-driven analysis.
