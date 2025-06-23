# 🛡️ Iran-Israel Narrative Intelligence Platform

A comprehensive web application for analyzing conflicting narratives across news, social media, and video platforms in the Iran-Israel conflict. The platform provides real-time narrative detection, source attribution, and interactive visualizations to help users understand how information spreads across different media ecosystems.

## 🚀 Current Status

✅ **Modern Frontend** - React 19/Vite with Zustand state management and React Router  
✅ **Backend API** - FastAPI with PostgreSQL, JWT authentication, Redis caching & rate limiting  
✅ **Docker Deployment** - Full containerization with docker-compose  
✅ **Real-Time Data** - Live ingestion from news, social media, and video platforms  
✅ **AI-Powered Analysis** - Anthropic Claude for narrative summarization and conflict detection  
✅ **Interactive Visualizations** - Network graphs and timeline charts  
✅ **Background Processing** - Celery with Redis for async data processing  
✅ **Authentication System** - Secure user management with route guards and superuser controls  
✅ **Performance Optimization** - Redis caching and API rate limiting for production scalability  
✅ **Multi-Platform Scrapers** - Twitter/X, Reddit, YouTube, and RSS feeds  
✅ **Production Ready** - CI/CD pipeline, code quality checks, and monitoring  
✅ **Enhanced Bias Analysis** - Multi-dimensional bias detection with LLM-powered alternative perspectives  
✅ **Academic Source Integration** - Fact-checking against historical texts and research papers  
🔄 **Active Development** - Enhanced conflict analysis and user customization

## ✨ Key Features

### 🔍 Narrative Detection & Analysis
- **Semantic Clustering** - Groups similar claims using advanced text embeddings
- **AI Summarization** - Claude-powered narrative summaries with conflict identification
- **Real-Time Processing** - Continuous ingestion and analysis pipeline
- **Source Attribution** - Complete tracking of content origin and engagement metrics

### ⚖️ Enhanced Bias Analysis System
- **Multi-Dimensional Bias Detection** - Political bias, factual accuracy, emotional tone, and sensationalism scoring
- **LLM-Powered Analysis** - Claude Sonnet for comprehensive bias assessment and blind spot identification
- **Alternative Perspective Generation** - AI-generated counter-narratives and missing context
- **Academic Source Integration** - Fact-checking against historical documents and research papers
- **Real-Time Bias Scoring** - Automated bias classification for incoming sources
- **Comprehensive Reporting** - Detailed bias analysis reports with confidence scores

### 📚 Academic Reference System
- **Historical Document Database** - Curated collection of academic papers and historical texts
- **Fact-Checking Pipeline** - Automated verification against authoritative sources
- **Source Credibility Scoring** - Multi-factor credibility assessment
- **Citation Tracking** - Academic source citation counts and impact metrics

### 🎨 Modern User Interface
- **Clean Design System** - Minimalist, professional interface prioritizing usability
- **Interactive Bias Visualization** - Real-time bias metrics and trend analysis
- **Alternative Perspective Display** - Side-by-side comparison of different viewpoints
- **Fact-Check Integration** - Inline fact-checking results with academic source citations
- **Responsive Design** - Optimized for desktop, tablet, and mobile devices

## 🔧 Enhanced Bias Analysis Features

### Political Bias Detection
- **Spectrum Analysis** - -1.0 (left) to 1.0 (right) political bias scoring
- **Language Pattern Recognition** - Identification of loaded language and political framing
- **Source Positioning** - Automatic classification of news sources on political spectrum

### Factual Accuracy Assessment
- **Truth Verification** - Cross-referencing claims against academic sources
- **Evidence Scoring** - 0.0 to 1.0 factual accuracy rating
- **Context Provision** - Missing context identification and supplementation

### Emotional Analysis
- **Tone Detection** - Emotional tone analysis from negative to positive
- **Sensationalism Scoring** - Detection of inflammatory or sensationalized content
- **Manipulation Identification** - Recognition of emotional manipulation techniques

### Alternative Perspective Generation
- **Counter-Narrative Creation** - AI-generated opposing viewpoints
- **Missing Context Addition** - Historical and political context supplementation
- **Blind Spot Identification** - Recognition of perspective gaps and omissions
- **Academic Source Integration** - Alternative perspectives backed by scholarly research

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js 18+
- PostgreSQL
- Redis
- Docker & Docker Compose

### Quick Start with Docker
```bash
# Clone the repository
git clone <repository-url>
cd ii

# Set up environment variables
cp env.example .env
# Edit .env with your API keys and database credentials

# Load sample academic sources
python -m app.etl.academic_loader data/academic_sources_sample.csv

# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec api alembic upgrade head

# Load sample bias data (optional)
docker-compose exec api python -m app.etl.load_bias data/bias_ratings.csv
```

### Enhanced Bias Analysis Setup

1. **Load Academic Sources**
```bash
# Load historical documents and research papers
python -m app.etl.academic_loader data/academic_sources_sample.csv
```

2. **Configure Claude API**
```bash
# Add to your .env file
ANTHROPIC_API_KEY=your_claude_api_key_here
```

3. **Start Bias Analysis**
```bash
# Trigger batch analysis of existing sources
curl -X POST "http://localhost:8000/api/bias/analyze/batch?limit=50"

# Analyze a specific source
curl -X POST "http://localhost:8000/api/bias/sources/{source_id}/analyze"
```

4. **View Bias Analysis**
Navigate to `/bias/{source_id}` in the frontend to see comprehensive bias analysis including:
- Multi-dimensional bias metrics
- Alternative perspectives
- Fact-check results
- Academic source citations

### API Endpoints

#### Bias Analysis
- `GET /api/bias/sources/{id}/bias-analysis` - Get comprehensive bias analysis
- `POST /api/bias/sources/{id}/analyze` - Trigger bias analysis for source
- `POST /api/bias/analyze/batch` - Batch analyze multiple sources
- `GET /api/bias/bias-stats` - System-wide bias statistics
- `GET /api/bias/alternative-perspectives` - Recent alternative perspectives

#### Academic Sources
- Academic source loading via ETL: `python -m app.etl.academic_loader <csv_file>`
- Fact-checking integration in bias analysis pipeline

## 📊 Bias Analysis Workflow

1. **Source Ingestion** - News articles collected from RSS feeds and social media
2. **Initial Processing** - Text analysis and embedding generation
3. **Bias Detection** - Multi-dimensional bias analysis using Claude
4. **Academic Cross-Reference** - Fact-checking against historical sources
5. **Alternative Generation** - AI-powered counter-narrative creation
6. **Visualization** - Interactive bias metrics and perspective comparison

## 🎯 Use Cases

### For Researchers
- **Academic Fact-Checking** - Verify news claims against scholarly sources
- **Bias Pattern Analysis** - Study bias trends across different media outlets
- **Alternative Perspective Research** - Access AI-generated counter-narratives
- **Historical Context Integration** - Connect current events to historical precedents

### For Journalists
- **Source Verification** - Check factual accuracy of claims
- **Perspective Balancing** - Access alternative viewpoints for balanced reporting
- **Bias Awareness** - Understand potential biases in source material
- **Context Enhancement** - Add historical context to current reporting

### For Analysts
- **Media Monitoring** - Track bias trends across news sources
- **Narrative Analysis** - Understand competing narratives and their evolution
- **Source Credibility Assessment** - Evaluate reliability of information sources
- **Conflict Analysis** - Analyze information warfare and narrative conflicts

## 📈 Recent Updates

### Enhanced Bias Analysis (Latest)
- **Multi-dimensional bias scoring** with political, factual, emotional, and sensationalism metrics
- **LLM-powered alternative perspective generation** using Claude Sonnet
- **Academic source integration** for fact-checking and historical context
- **Comprehensive bias reporting** with confidence scores and evidence
- **Real-time bias analysis pipeline** for incoming sources

### Previous Updates
- Modern React 19 frontend with improved UX
- Enhanced API with Redis caching and rate limiting
- Comprehensive authentication system
- Multi-platform data ingestion
- Interactive network visualizations

## 🔮 Roadmap

- **Advanced Bias Detection** - Integration with additional bias detection models
- **Enhanced Academic Integration** - Expanded academic source database
- **Real-time Fact-Checking** - Live fact-checking during news ingestion
- **Bias Trend Analysis** - Historical bias pattern analysis and prediction
- **Export Capabilities** - PDF reports and data export functionality
- **API Rate Limiting** - Enhanced API security and usage controls

## 🛡️ Technical Architecture

- **Backend**: FastAPI, PostgreSQL, Redis, Celery
- **Frontend**: React 19, TypeScript, Vite, TailwindCSS
- **AI/ML**: Anthropic Claude, SentenceTransformers, HDBSCAN
- **Infrastructure**: Docker, Docker Compose, Alembic migrations
- **Data Sources**: RSS feeds, academic papers, historical documents

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.
