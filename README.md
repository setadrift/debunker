# 🛠️ Misinformation Debunker – Iran–Israel Conflict

## Objective

Build a web-based application that helps **casual readers** explore **conflicting narratives** and see **which sources are promoting each one**, using data from news, social media, and video platforms. The user interface highlights **the top 10 active narratives** and lets users explore them via timeline views, side-by-side claim comparison, and network visualizations of source clusters.

## 🚀 Current Status

✅ **Backend API** - FastAPI with PostgreSQL database  
✅ **Frontend Interface** - React/Vite with modern UI components  
✅ **Data Pipeline** - RSS ingestion, embedding generation, clustering  
✅ **Network Visualization** - Interactive graph showing source relationships  
✅ **Timeline Charts** - Visual timeline of narrative activity  
✅ **Narrative Summaries** - AI-powered cluster analysis  
✅ **Multi-Platform Scrapers** - Twitter, Reddit, YouTube data collection  
✅ **Real-Time Content** - Live data from social media and video platforms  
✅ **Transcript Analysis** - YouTube video transcript extraction and keyword analysis  
🔄 **Active Development** - Expanding narrative detection and conflict analysis

## Core Functionality

### 1. Narrative Detection

- Cluster semantically similar claims using **text embeddings**
- Use **Anthropic Claude** to summarize each cluster into a short narrative label
- Optionally highlight competing or conflicting clusters (e.g. "Claim A" vs "Claim B")

### 2. 🔍 Source Attribution

- Track and display:
    - Source name
    - Timestamp
    - Platform (e.g. Reddit, YouTube, etc.)
    - Country of origin (if derivable)
    - Confidence/reliability score (simple heuristic for now)
    - Link to original content
    - Engagement metrics (likes, retweets, views if available)

### 3. 🧱 Homepage

- Show **"Top 10 Active Narratives"** ranked by recent activity
- Each narrative card includes:
    - Summary (from Claude)
    - Timeline snippet (e.g. "First seen X, Last seen Y")
    - Conflicting claim toggle or preview
    - Total # mentions or sources
    - "Explore" button → detailed timeline/source view

### 4. 📈 Narrative Explorer

For each narrative:

- Display timeline of claim occurrences
- Show side-by-side conflicting claims
- Visualize sources using **network graph** (nodes = source, edges = similarity/cluster)
- Show all original posts/articles that support the narrative

## 🏗️ Technical Architecture

The application identifies conflicting narratives across news, social media, and video platforms through a multi-stage pipeline that processes raw content into structured narrative clusters. 

### Dependencies
- **FastAPI** for the web API
- **Vite + React** for the frontend application  
- **PostgreSQL** (via Supabase) for data storage
- **Anthropic Claude** for LLM-powered narrative analysis
- **NLP Stack**: sentence-transformers, HDBSCAN clustering, scikit-learn for embedding generation and narrative clustering
- **Visualization**: react-force-graph for network graphs, Chart.js for timeline charts
- **Scraping**: snscrape for Twitter/X, PRAW for Reddit, YouTube Data API for video content
- **Transcript Processing**: youtube-transcript-api for extracting video captions and keyword analysis

### Data Sources
Currently ingesting from multiple platforms:

**News Media (RSS):**
- **Western Media:** BBC, Reuters, CNN, AP
- **Middle Eastern Media:** Al Jazeera, Times of Israel, Jerusalem Post, Middle East Eye  
- **Iranian Media:** Mehr News Agency

**Social Media:**
- **Twitter/X:** Real-time scraping with search query "Iran Israel since:2025-06-01" (with fallback mock data)
- **Reddit:** Live posts from r/worldnews and r/MiddleEast with comment extraction

**Video Platforms:**
- **YouTube:** Video search with transcript extraction and keyword-based excerpt generation
- **Content Analysis:** 3-sentence excerpts around key terms (Iran, Israel, conflict, diplomacy, nuclear, etc.)

**Fallback Systems:** 
- Comprehensive mock data generation for development when APIs are unavailable
- Maintains data structure consistency across all platforms

## Local Development

### 1. Environment Setup
Create a `.env` file (or copy `env.example`) and add your credentials:
```bash
cp env.example .env
```
Your `.env` should contain your Supabase connection string and Anthropic API key:
```bash
DATABASE_URL=postgresql+asyncpg://postgres.oqqecohkqkjomxxwypss:<pwd>@aws-0-us-east-1.pooler.supabase.com:6543/postgres
ANTHROPIC_API_KEY=sk-...
```

### 2. Backend Setup
Install Python dependencies and set up the database.
```bash
# Install Python packages
pip install -r requirements.txt

# Apply database migrations
make migrate
```

To run the backend server:
```bash
uvicorn app.main:app --reload
```

### 3. Frontend Setup
Install Node.js dependencies and run the development server.
```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Run the dev server (usually on http://localhost:5173)
npm run dev
```

### 4. Data Processing
To populate the database, run the data ingestion and processing pipelines.

```bash
# Scrape latest news from RSS feeds
python -m app.ingest news

# Run individual scrapers
python app/scrapers/twitter.py   # Twitter/X posts (with fallback)
python app/scrapers/reddit.py    # Reddit posts from r/worldnews, r/MiddleEast  
python app/scrapers/youtube.py   # YouTube videos with transcript analysis

# Generate embeddings, cluster sources, and create summaries
python -m app.pipeline
```

### 5. API Endpoints
The backend provides several key endpoints:

```bash
# Get all narratives with summaries
GET /api/narratives/

# Get network graph data (nodes and links)
GET /api/graph/

# Get timeline data for charts
GET /api/narratives/timeline
```

### 6. Git Hooks (Recommended)
Set up automatic formatting and linting before each commit:
```bash
pre-commit install
```

## 🎨 Frontend Features

The React frontend includes several interactive components:

- **Homepage** - Displays top 10 active narratives with summary cards
- **Network Graph** - Interactive visualization of source relationships using react-force-graph
- **Timeline Charts** - Visual timeline showing narrative activity over time
- **Narrative Detail** - Detailed view of individual narratives with sources
- **Responsive Design** - Modern UI with Tailwind CSS

## 🎯 Next Development Steps

### Immediate Priorities
- **Enhanced Narrative Detection** - Improve conflicting narrative identification algorithms
- **Real-time Updates** - WebSocket connections for live data feeds
- **User Interaction** - Bookmarking, sharing, and advanced narrative filtering
- **Content Integration** - Unified pipeline for all scraper outputs

### Data Source Expansion
**Additional News Sources:**
- Haaretz, Jerusalem Post, Tehran Times
- Middle East Monitor, Al-Monitor  
- Iranian state media (IRNA, Tasnim)
- Israeli media (Channel 12, Ynet)

**Additional Social Media:**
- Expanded Reddit coverage (r/geopolitics, r/iran, r/israel)
- Additional YouTube news channels and live streams
- Enhanced Twitter/X coverage with verified API access
- Telegram channels (public Iran-Israel discussion groups)

**Technical Improvements:**
- **Performance** - Database indexing, caching layer
- **Reliability** - Better error handling, retry mechanisms  
- **Security** - Input validation, rate limiting
- **Testing** - Comprehensive test coverage

This diversity is crucial for the clustering algorithm to identify genuinely conflicting narratives rather than variations of the same perspective.

## 🔧 Database Management

### Migrations
Apply database migrations to set up the schema:
```bash
make migrate
```

Override the default Supabase connection if needed:
```bash
export DATABASE_URL="postgresql+asyncpg://<user>:<pwd>@<host>/<db>"
```

### Environment Variables
Create a `.env` file with your credentials:
```bash
# Database and AI
DATABASE_URL=postgresql+asyncpg://postgres.oqqecohkqkjomxxwypss:<pwd>@aws-0-us-east-1.pooler.supabase.com:6543/postgres
ANTHROPIC_API_KEY=sk-...

# Social Media APIs  
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret

# Video Platform APIs
YOUTUBE_API_KEY=your_youtube_api_key
```

**API Setup Guides:**
- **Reddit**: Create app at https://www.reddit.com/prefs/apps (select "script" type)
- **YouTube**: Get API key at https://console.developers.google.com/ (enable YouTube Data API v3)

## 🧪 Testing & Quality

### Code Quality
- **Pre-commit hooks** - Black formatting, isort, flake8 linting
- **GitHub Actions** - Automated CI/CD pipeline  
- **Testing** - pytest test suite

Setup:
```bash
pre-commit install
```

### Project Structure
```
ii/
├── app/                    # Backend application
│   ├── api/               # FastAPI routes (narratives, graph endpoints)
│   ├── scrapers/          # Multi-platform data collection
│   │   ├── twitter.py     # Twitter/X scraping with snscrape
│   │   ├── reddit.py      # Reddit scraping with PRAW
│   │   └── youtube.py     # YouTube video + transcript analysis
│   ├── nlp/              # NLP processing and summarization
│   └── *.py              # Core modules (models, pipeline, ingest)
├── frontend/              # React application
│   └── src/
│       ├── components/    # NetworkGraph, TimelineChart, Card components
│       └── pages/        # Home, Graph, NarrativeDetail pages
├── migrations/           # Database schema migrations
└── tests/               # Test suite
```

### Scraper Capabilities

| Platform | Status | Content Type | Special Features |
|----------|--------|--------------|------------------|
| **RSS Feeds** | ✅ Active | News articles | Multi-source aggregation |
| **Twitter/X** | ✅ Active | Posts/tweets | Engagement metrics, fallback mock data |
| **Reddit** | ✅ Active | Posts + comments | Subreddit targeting (r/worldnews, r/MiddleEast) |
| **YouTube** | ✅ Active | Video transcripts | Real-time transcript analysis, keyword excerpts |
