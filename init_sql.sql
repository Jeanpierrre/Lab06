
CREATE DATABASE IF NOT EXISTS paperly;
USE paperly;

CREATE TABLE IF NOT EXISTS papers (
    id VARCHAR(64) PRIMARY KEY,
    title TEXT NOT NULL,
    authors JSONB NOT NULL DEFAULT '[]',
    abstract TEXT,
    keywords JSONB DEFAULT '[]',
    year INTEGER,
    journal VARCHAR(255),
    doi VARCHAR(255),
    url VARCHAR(512),
    full_text TEXT,
    citation_count INTEGER DEFAULT 0,
    reference_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_papers_year (year),
    INDEX idx_papers_journal (journal),
    INDEX idx_papers_doi (doi),
    INDEX idx_papers_citation_count (citation_count),
    FULLTEXT INDEX idx_papers_title_abstract (title, abstract)
);

CREATE TABLE IF NOT EXISTS authors (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    affiliation VARCHAR(255),
    orcid VARCHAR(50),
    h_index INTEGER DEFAULT 0,
    total_citations INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_authors_name (name),
    INDEX idx_authors_h_index (h_index)
);

CREATE TABLE IF NOT EXISTS paper_authors (
    paper_id VARCHAR(64),
    author_id VARCHAR(64),
    author_order INTEGER,
    is_corresponding BOOLEAN DEFAULT FALSE,
    
    PRIMARY KEY (paper_id, author_id),
    FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS citations (
    id VARCHAR(64) PRIMARY KEY,
    citing_paper_id VARCHAR(64) NOT NULL,
    cited_paper_id VARCHAR(64) NOT NULL,
    context TEXT,
    citation_type ENUM('methodology', 'comparison', 'background', 'other') DEFAULT 'other',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_citation (citing_paper_id, cited_paper_id),
    FOREIGN KEY (citing_paper_id) REFERENCES papers(id) ON DELETE CASCADE,
    FOREIGN KEY (cited_paper_id) REFERENCES papers(id) ON DELETE CASCADE,
    
    INDEX idx_citations_citing (citing_paper_id),
    INDEX idx_citations_cited (cited_paper_id)
);

CREATE TABLE IF NOT EXISTS search_analytics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    query TEXT NOT NULL,
    results_count INTEGER,
    user_session VARCHAR(64),
    execution_time_ms INTEGER,
    filters_used JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_analytics_timestamp (timestamp),
    INDEX idx_analytics_session (user_session)
);


CREATE TABLE IF NOT EXISTS system_metrics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,2),
    metric_unit VARCHAR(20),
    component VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_metrics_name_timestamp (metric_name, timestamp),
    INDEX idx_metrics_component (component)
);

INSERT INTO papers (id, title, authors, abstract, year, journal, doi, citation_count) VALUES
('paper_001', 
 'Deep Learning Approaches for Scientific Paper Classification',
 '["Alice Johnson", "Bob Smith", "Carol Davis"]',
 'This paper presents a comprehensive survey of deep learning techniques applied to scientific paper classification. We evaluate various neural network architectures and propose a novel hybrid approach.',
 2023,
 'Journal of Machine Learning Research',
 '10.1007/JMLR.2023.001',
 45),

('paper_002',
 'Natural Language Processing in Academic Literature Mining', 
 '["David Wilson", "Emma Thompson"]',
 'We explore advanced NLP techniques for extracting structured information from academic literature. Our approach combines transformer models with graph neural networks.',
 2023,
 'Computational Linguistics',
 '10.1162/COLI.2023.002', 
 32),

('paper_003',
 'Citation Network Analysis Using Graph Databases',
 '["Frank Miller", "Grace Lee", "Henry Chang"]',
 'This work presents a scalable approach to citation network analysis using Neo4j graph database. We demonstrate applications in research trend identification.',
 2022,
 'IEEE Transactions on Knowledge and Data Engineering',
 '10.1109/TKDE.2022.003',
 78);


INSERT INTO authors (id, name, affiliation, h_index, total_citations) VALUES
('author_001', 'Alice Johnson', 'MIT Computer Science', 25, 1250),
('author_002', 'Bob Smith', 'Stanford AI Lab', 18, 890),
('author_003', 'Carol Davis', 'Carnegie Mellon University', 22, 1100),
('author_004', 'David Wilson', 'University of Washington', 15, 650),
('author_005', 'Emma Thompson', 'Google Research', 30, 1800);


INSERT INTO paper_authors (paper_id, author_id, author_order, is_corresponding) VALUES
('paper_001', 'author_001', 1, TRUE),
('paper_001', 'author_002', 2, FALSE),
('paper_001', 'author_003', 3, FALSE),
('paper_002', 'author_004', 1, TRUE),
('paper_002', 'author_005', 2, FALSE);


INSERT INTO citations (id, citing_paper_id, cited_paper_id, citation_type) VALUES
('citation_001', 'paper_001', 'paper_002', 'methodology'),
('citation_002', 'paper_001', 'paper_003', 'background'),
('citation_003', 'paper_002', 'paper_003', 'comparison');


CREATE VIEW paper_details AS
SELECT 
    p.id,
    p.title,
    p.abstract,
    p.year,
    p.journal,
    p.doi,
    p.citation_count,
    p.reference_count,
    GROUP_CONCAT(a.name ORDER BY pa.author_order SEPARATOR ', ') as author_names
FROM papers p
LEFT JOIN paper_authors pa ON p.id = pa.paper_id  
LEFT JOIN authors a ON pa.author_id = a.id
GROUP BY p.id;