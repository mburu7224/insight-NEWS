# Israel News Module - Project Roadmap

## Project Overview
An automated "Satellite Service" that feeds real-time, categorized Israeli insights (Farming, Technology, Politics, Hospitality) into the main Insight-Viewer platform. Designed for 1,000+ concurrent users.

---

## Module 1: Ingestor (Python / BeautifulSoup / RSS)
**Purpose:** Web scraping - scans the web 24/7 to pull raw data from Israeli news outlets and government feeds.

### Tasks:
- [x] 1.1 Create scraper.py with BeautifulSoup setup
- [x] 1.2 Create requirements.txt for Python dependencies
- [x] 1.3 Create feeds.json with Israeli news RSS/URL sources
- [x] 1.4 Implement base scraper class
- [x] 1.5 Add RSS feed parser
- [x] 1.6 Add HTML parser for news websites
- [ ] 1.7 Implement rate limiting and error handling
- [ ] 1.8 Create output format for raw JSON data

### Dependencies:
- beautifulsoup4
- requests
- feedparser
- lxml

---

## Module 2: Processor (Python / AI / NLP)
**Purpose:** AI processing - filters noise, categorizes news, creates 3-bullet summaries, handles translation.

### Tasks:
- [x] 2.1 Create summarizer.py for AI summarization
- [ ] 2.2 Create categorizer.py for sector classification
- [ ] 2.3 Create translator.py for English-Hebrew handling
- [x] 2.4 Define sector keywords (Farming, Tech, Politics, Hospitality)
- [x] 2.5 Implement LLM integration (OpenAI)
- [x] 2.6 Create bullet point generation logic
- [ ] 2.7 Add language detection
- [ ] 2.8 Create processing pipeline

### Dependencies:
- openai (or anthropic)
- googletrans (or deep-translator)
- nltk

---

## Module 3: Asset Automator (Python / Cloud Storage)
**Purpose:** Image handling - fetches, hosts, and links image URLs for the frontend.

### Tasks:
- [x] 3.1 Create uploader.py for cloud storage
- [x] 3.2 Create image_gen.py for image generation/fetching
- [x] 3.3 Implement image URL extraction from news
- [x] 3.4 Add cloud storage integration (AWS S3 / Cloudinary / custom)
- [x] 3.5 Implement image caching
- [x] 3.6 Create fallback image handling
- [ ] 3.7 Add image optimization

### Dependencies:
- boto3 (for AWS S3)
- cloudinary (optional)
- Pillow

---

## Module 4: Persistence Layer (PostgreSQL + Firebase)
**Purpose:** Database storage - stores processed insights and image URLs for high-traffic handling.

### Tasks:
- [x] 4.1 Create schema.sql for PostgreSQL
- [x] 4.2 Define tables: news, categories, images, translations
- [ ] 4.3 Create migration scripts
- [x] 4.4 Integrate Firebase for real-time database
- [x] 4.5 Create database connection utilities
- [x] 4.6 Implement CRUD operations for both PostgreSQL and Firebase
- [ ] 4.7 Add query optimization
- [x] 4.8 Create sync between PostgreSQL and Firebase

### Dependencies:
- psycopg2 (PostgreSQL)
- firebase-admin
- SQLAlchemy

---

## Module 5: Delivery API (Node.js / PHP)
**Purpose:** API endpoints - serves final data in clean format for frontend.

### Tasks:
- [x] 5.1 Create API entry point (server.js)
- [x] 5.2 Create db.js for database connection
- [x] 5.3 Create endpoints/farming.js
- [x] 5.4 Create endpoints/tech.js
- [x] 5.5 Create endpoints/politics.js
- [x] 5.6 Create endpoints/hospitality.js
- [ ] 5.7 Implement API authentication
- [x] 5.8 Add request validation
- [x] 5.9 Create response formatting
- [x] 5.10 Add rate limiting

### Dependencies (Node.js):
- express
- pg (PostgreSQL)
- redis
- cors
- dotenv

### Dependencies (PHP):
- Composer packages
- PDO extension

---

## Module 6: Frontend View (HTML / CSS / JS)
**Purpose:** User interface - fetches and displays news to end-users.

### Tasks:
- [x] 6.1 Create index.html structure
- [x] 6.2 Create style.css with responsive design
- [x] 6.3 Create script.js for API integration
- [x] 6.4 Implement category tabs (Farming, Tech, Politics, Hospitality)
- [x] 6.5 Add image lazy loading
- [ ] 6.6 Implement real-time updates
- [x] 6.7 Add loading states
- [x] 6.8 Create error handling UI

---

## Configuration & Setup
- [x] Create package.json for Node.js dependencies
- [x] Create .env for environment variables
- [ ] Create README.md with setup instructions
- [ ] Create docker-compose.yml (optional)
- [ ] Set up logging configuration

---

## Priority Order (Recommended Implementation)

### Phase 1: Core Infrastructure
1. Ingestor (Module 1) - Get data
2. Processor (Module 2) - Process data
3. Persistence (Module 4) - Store data

### Phase 2: Delivery
4. Asset Automator (Module 3) - Handle images
5. Delivery API (Module 5) - Serve data

### Phase 3: Frontend
6. Frontend View (Module 6) - Display data

---

## Information Needed from You

Before I can proceed with implementation, please provide:

1. **News Sources**: Which Israeli news websites/RSS feeds should I monitor?
   - Examples: Ynet, Haaretz, The Times of Israel, Calcalist, etc.

2. **Database Preferences**:
   - PostgreSQL (for persistent storage)?
   - Redis (for caching)?
   - Both?

3. **Cloud Storage**:
   - AWS S3?
   - Cloudinary?
   - Custom server?

4. **AI/LLM**:
   - OpenAI (GPT)?
   - Anthropic (Claude)?
   - Local model?
   - Placeholder/Mock?

5. **API Technology**:
   - Node.js with Express?
   - PHP?

6. **Deployment**:
   - Local development?
   - Docker containers?
   - Cloud hosting?

---

## Next Steps
Once you provide the above information, I'll begin implementing the modules in priority order starting with Module 1 (Ingestor).

Last Updated: 2024
