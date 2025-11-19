-- PostgreSQL initialization for Document Manager API
-- Generated based on the models in app/models/

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table for document tags
CREATE TABLE IF NOT EXISTS tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for tags name
CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name);

-- Function to update the updated_at column for tags
CREATE OR REPLACE FUNCTION update_updated_at_column_tags()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for tags table
CREATE TRIGGER update_tags_updated_at BEFORE UPDATE ON tags
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column_tags();

-- Table for tag domains
CREATE TABLE IF NOT EXISTS tag_domain (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for tag_domain name
CREATE INDEX IF NOT EXISTS idx_tag_domain_name ON tag_domain(name);

-- Function to update the updated_at column for tag_domain
CREATE OR REPLACE FUNCTION update_updated_at_column_tag_domain()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for tag_domain table
CREATE TRIGGER update_tag_domain_updated_at BEFORE UPDATE ON tag_domain
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column_tag_domain();

-- Table for documents
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    size INTEGER NOT NULL,
    storage_key VARCHAR(500) NOT NULL UNIQUE,
    is_audited BOOLEAN DEFAULT FALSE,
    description TEXT,
    custom_fields JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for documents
CREATE INDEX IF NOT EXISTS idx_documents_storage_key ON documents(storage_key);
CREATE INDEX IF NOT EXISTS idx_documents_is_audited ON documents(is_audited);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at);
CREATE INDEX IF NOT EXISTS idx_documents_updated_at ON documents(updated_at);

-- Function to update the updated_at column for documents
CREATE OR REPLACE FUNCTION update_updated_at_column_documents()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for documents table
CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column_documents();

-- Table for document aliases
CREATE TABLE IF NOT EXISTS document_aliases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alias VARCHAR(255) NOT NULL UNIQUE,
    document_id UUID NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for document aliases
CREATE INDEX IF NOT EXISTS idx_document_aliases_alias ON document_aliases(alias);
CREATE INDEX IF NOT EXISTS idx_document_aliases_document_id ON document_aliases(document_id);

-- Table for document-tag associations (many-to-many)
CREATE TABLE IF NOT EXISTS document_tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL,
    tag_id UUID NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for document tags associations
CREATE INDEX IF NOT EXISTS idx_document_tags_document_id ON document_tags(document_id);
CREATE INDEX IF NOT EXISTS idx_document_tags_tag_id ON document_tags(tag_id);

-- Table for document processing status
CREATE TABLE IF NOT EXISTS document_processing (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL UNIQUE,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    step_counts INTEGER,
    current_step INTEGER,
    processing_data JSONB,
    processing_updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for document processing status
CREATE INDEX IF NOT EXISTS idx_document_processing_status ON document_processing(status);

-- Function to update the processing_updated_at column for document_processing
CREATE OR REPLACE FUNCTION update_processing_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.processing_updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for document_processing table
CREATE TRIGGER update_document_processing_updated_at BEFORE UPDATE ON document_processing
    FOR EACH ROW EXECUTE FUNCTION update_processing_updated_at_column();

-- Table for document review status
CREATE TABLE IF NOT EXISTS document_reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL UNIQUE,
    review_state VARCHAR(50) NOT NULL DEFAULT 'unreviewed',
    review_by VARCHAR(255),
    review_comment TEXT,
    review_updated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for document review state
CREATE INDEX IF NOT EXISTS idx_document_reviews_state ON document_reviews(review_state);

-- Insert default tag domain if not exists
INSERT INTO tag_domain (name, display_name, created_at, updated_at)
SELECT 
    'default',
    'Default Domain',
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM tag_domain WHERE name = 'default'
);