-- Israel News Module - PostgreSQL Database Schema

-- PostgreSQL note:
-- Create the database separately if needed:
--   createdb israel_news_db

-- Connect to database
\c israel_news_db;

-- Categories table
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    keywords TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default categories
INSERT INTO categories (name, keywords) VALUES 
    ('farming', ARRAY['agriculture', 'farming', 'farmers', 'crops', 'livestock', 'agtech']),
    ('tech', ARRAY['technology', 'tech', 'startup', 'innovation', 'AI', 'cybersecurity']),
    ('politics', ARRAY['politics', 'government', 'Knesset', 'election', 'policy']),
    ('hospitality', ARRAY['hotel', 'tourism', 'restaurant', 'hospitality', 'travel']),
    ('general', ARRAY['news', 'israel'])
ON CONFLICT (name) DO NOTHING;

-- News articles table
CREATE TABLE IF NOT EXISTS articles (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(255) UNIQUE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    content TEXT,
    url VARCHAR(1000) UNIQUE NOT NULL,
    image_url VARCHAR(1000),
    published_at TIMESTAMP,
    source VARCHAR(255),
    category_id INTEGER REFERENCES categories(id),
    summary JSONB,
    sentiment VARCHAR(20) DEFAULT 'neutral',
    importance VARCHAR(20) DEFAULT 'medium',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category_id);
CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source);
CREATE INDEX IF NOT EXISTS idx_articles_importance ON articles(importance);

-- Images table
CREATE TABLE IF NOT EXISTS images (
    id SERIAL PRIMARY KEY,
    article_id INTEGER REFERENCES articles(id) ON DELETE CASCADE,
    original_url VARCHAR(1000),
    hosted_url VARCHAR(1000),
    cloud_provider VARCHAR(50),
    width INTEGER,
    height INTEGER,
    file_size INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_images_article ON images(article_id);

-- Translations table
CREATE TABLE IF NOT EXISTS translations (
    id SERIAL PRIMARY KEY,
    article_id INTEGER REFERENCES articles(id) ON DELETE CASCADE,
    language VARCHAR(10) NOT NULL,
    title_translated VARCHAR(500),
    description_translated TEXT,
    summary_translated JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(article_id, language)
);

CREATE INDEX IF NOT EXISTS idx_translations_article ON translations(article_id);
CREATE INDEX IF NOT EXISTS idx_translations_language ON translations(language);

-- API logs table
CREATE TABLE IF NOT EXISTS api_logs (
    id SERIAL PRIMARY KEY,
    endpoint VARCHAR(100) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER,
    response_time_ms INTEGER,
    user_agent VARCHAR(255),
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_api_logs_endpoint ON api_logs(endpoint);
CREATE INDEX IF NOT EXISTS idx_api_logs_created ON api_logs(created_at DESC);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers
CREATE TRIGGER update_articles_updated_at BEFORE UPDATE ON articles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_categories_updated_at BEFORE UPDATE ON categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_translations_updated_at BEFORE UPDATE ON translations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'israel_news_user') THEN
        GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO israel_news_user;
        GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO israel_news_user;
    END IF;
END
$$;
