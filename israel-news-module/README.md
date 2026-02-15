# Israel News Module

An automated "Satellite Service" that feeds real-time, categorized Israeli insights (Farming, Technology, Politics, Hospitality) into the main Insight-Viewer platform. Designed for 1,000+ concurrent users.

## Features

- **Automated News Ingestion** - Scrapes Israeli news from NewsAPI.org, RSS feeds, and direct website parsing
- **AI-Powered Processing** - Uses OpenAI GPT-3.5 to summarize and categorize news into 4 sectors
- **Image Hosting** - Cloudinary and AWS S3 integration for image storage
- **Dual Database** - PostgreSQL for persistent storage + Firebase for real-time updates
- **RESTful API** - Express.js API with category-based endpoints
- **Responsive Frontend** - Vanilla HTML/CSS/JS with real-time updates

## Architecture

```
[Ingestor] → [Processor] → [Asset Automator] → [Database] → [API] → [Frontend]
```

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.8+
- PostgreSQL 14+
- Firebase Project

### Installation

1. **Clone and navigate to project:**
```bash
cd israel-news-module
```

2. **Install Node.js dependencies:**
```bash
cd api
npm install
```

3. **Install Python dependencies:**
```bash
# Ingestor
pip install -r ingestor/requirements.txt

# Processor
pip install -r processor/requirements.txt

# Asset Automator
pip install -r asset_automator/requirements.txt
```

4. **Configure environment variables:**
```bash
cp .env.example .env
# Edit .env with your API keys and database credentials
```

### Database Setup

1. **Create PostgreSQL database:**
```bash
createdb israel_news_db
```

2. **Run schema:**
```bash
psql -d israel_news_db -f data/schema.sql
```

3. **Configure Firebase:**
- Create a Firebase project at https://console.firebase.google.com
- Download service account JSON
- Add to .env file as FIREBASE_SERVICE_ACCOUNT

### Running the Application

1. **Start the API server:**
```bash
cd api
npm start
```

2. **Open the frontend:**
```bash
# Open public/index.html in browser
# Or serve with a local server:
npx serve public
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| NEWSAPI_KEY | NewsAPI.org API key | Yes |
| OPENAI_API_KEY | OpenAI API key | Yes |
| POSTGRES_HOST | PostgreSQL host | Yes |
| POSTGRES_DB | Database name | Yes |
| POSTGRES_USER | Database user | Yes |
| POSTGRES_PASSWORD | Database password | Yes |
| CLOUDINARY_API_KEY | Cloudinary API key | Optional |
| CLOUDINARY_CLOUD_NAME | Cloudinary cloud name | Optional |
| CLOUDINARY_API_SECRET | Cloudinary API secret | Optional |
| IMAGE_STORAGE_PROVIDER | s3, cloudinary, or local | Optional |
| REQUIRE_API_KEY | Enable API key auth (true/false) | Optional |
| API_KEYS | Comma-separated API keys | Optional |

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| GET /api/farming | Farming news |
| GET /api/tech | Technology news |
| GET /api/politics | Politics news |
| GET /api/hospitality | Hospitality news |
| GET /api/general | All Israeli news |
| GET /api/stream | Server-Sent Events stream |
| GET /health | Health check |

### Query Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| page | Page number | 1 |
| limit | Results per page (max 100) | 20 |

### Authentication

Include API key in header:
```
x-api-key: your-api-key
```

## Development

### Running Modules Separately

**Ingestor (fetch news):**
```bash
python -m ingestor.scraper
```

**Processor (AI summarization):**
```bash
python -m processor.summarizer
```

**Asset Automator (image handling):**
```bash
python -m asset_automator.uploader
```

### Docker (Optional)

```bash
docker-compose up -d
```

## Project Structure

```
israel-news-module/
├── api/                    # Node.js Express API
│   ├── middleware/         # Auth, rate limiting
│   ├── routes/             # Category endpoints
│   ├── server.js           # Main server
│   └── db.js               # Database connections
├── ingestor/               # News scraping (Python)
│   ├── scraper.py          # Main scraper
│   ├── feeds.json          # RSS feed config
│   └── requirements.txt
├── processor/              # AI processing (Python)
│   ├── summarizer.py       # OpenAI summarization
│   └── requirements.txt
├── asset_automator/        # Image handling (Python)
│   ├── uploader.py         # Cloudinary/S3 upload
│   └── requirements.txt
├── data/                   # Database
│   ├── schema.sql          # PostgreSQL schema
│   └── database.py         # Python DB utilities
└── public/                 # Frontend
    ├── index.html
    ├── style.css
    └── script.js
```

## Categories

| Category | Keywords |
|----------|----------|
| Farming | agriculture, farming, farmers, crops, livestock, agtech |
| Tech | technology, startup, innovation, AI, cybersecurity |
| Politics | government, Knesset, election, policy, minister |
| Hospitality | hotel, tourism, restaurant, travel, accommodation |

## License

MIT
