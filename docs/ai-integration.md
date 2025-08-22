# AI Integration

NoteParser seamlessly integrates with advanced AI services to provide intelligent document processing, knowledge organization, and academic assistance.

## Overview

The AI integration consists of two main services:

- **RagFlow**: Retrieval-Augmented Generation for document search and insights
- **DeepWiki**: AI-powered wiki system with knowledge graphs

## Quick Start

### Prerequisites

You have several options for deploying the AI services:

#### Option 1: Docker Compose (Recommended for Development)

```bash
# Clone and start AI services
git clone https://github.com/CollegeNotesOrg/noteparser-ai-services.git
cd noteparser-ai-services
docker-compose up -d

# Verify services are running
curl http://localhost:8010/health  # RagFlow
curl http://localhost:8011/health  # DeepWiki
```

#### Option 2: Hosted Services (Coming Soon)

```bash
# Use hosted AI services (when available)
export RAGFLOW_URL=https://api.collegenotesorg.com/ragflow
export DEEPWIKI_URL=https://api.collegenotesorg.com/deepwiki
```

#### Option 3: Custom Deployment

Deploy to your own infrastructure using Kubernetes, AWS, or other cloud providers. See the [noteparser-ai-services documentation](https://github.com/CollegeNotesOrg/noteparser-ai-services) for deployment guides.

### Using AI Features

#### Document Processing with AI

```python
from noteparser import NoteParser
from noteparser.integration.ai_services import AIServicesIntegration

# Initialize parser with AI integration
parser = NoteParser()
ai_integration = AIServicesIntegration()

# Parse and process with AI
result = parser.parse_to_markdown("document.pdf")
ai_result = await ai_integration.process_document(result)

print(f"Document indexed: {ai_result['rag_indexing']}")
print(f"Wiki article created: {ai_result['wiki_article']}")
```

#### Using Service Clients Directly

```python
from noteparser.integration.service_client import ServiceClientManager

# Initialize service manager
manager = ServiceClientManager()

# Check service health
health = await manager.health_check_all()
print(f"Services health: {health}")

# Use RagFlow for document analysis
ragflow = manager.get_client("ragflow")
result = await ragflow.index_document(
    content="Your document content here",
    metadata={"title": "Document Title", "author": "Author"}
)

# Query the knowledge base
query_result = await ragflow.query(
    query="What are the main concepts?",
    k=5
)

# Use DeepWiki for knowledge organization
deepwiki = manager.get_client("deepwiki")
article = await deepwiki.create_article(
    title="New Concept",
    content="Detailed explanation...",
    metadata={"tags": ["concept", "important"]}
)

# Search wiki knowledge
search_result = await deepwiki.search("machine learning")
```

## RagFlow Integration

### Features

- **Document Indexing**: Automatic embedding and vector storage
- **Similarity Search**: Find related content using semantic search
- **Insight Extraction**: AI-powered summaries and key points
- **Question Answering**: Natural language queries with context

### API Endpoints

- `POST /index` - Index a document
- `POST /query` - Query indexed documents
- `POST /insights` - Extract document insights
- `GET /stats` - Get indexing statistics

### Configuration

```yaml
# config/services.yml
services:
  ragflow:
    enabled: true
    host: localhost
    port: 8010
    config:
      embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
      vector_db_type: "faiss"
      chunk_size: 512
      chunk_overlap: 50
      top_k: 5
```

## DeepWiki Integration

### Features

- **Article Creation**: AI-enhanced wiki articles
- **Auto-linking**: Automatic cross-references between concepts
- **Knowledge Graph**: Visual relationship mapping
- **AI Assistant**: Natural language Q&A about content
- **Real-time Collaboration**: WebSocket-based live editing

### API Endpoints

- `POST /article` - Create/update articles
- `POST /search` - Search wiki content
- `POST /ask` - Ask AI assistant
- `GET /graph` - Get knowledge graph
- `GET /similar/{id}` - Find similar articles

### Wiki Features

#### Creating Articles

```python
article = await deepwiki.create_article(
    title="Machine Learning Fundamentals",
    content="""
# Machine Learning Fundamentals

Machine learning is a subset of artificial intelligence...

## Key Concepts
- Supervised Learning
- Unsupervised Learning
- Reinforcement Learning
    """,
    metadata={
        "tags": ["AI", "ML", "fundamentals"],
        "author": "Student",
        "course": "CS101"
    }
)
```

#### Knowledge Graphs

```python
# Get link graph for visualization
graph = await deepwiki.get_link_graph(
    article_id="machine-learning-fundamentals",
    depth=2
)

# Find similar articles
similar = await deepwiki.find_similar(
    article_id="machine-learning-fundamentals",
    limit=5
)
```

## Advanced Features

### Academic Workflow Integration

```python
async def process_course_materials(file_paths):
    """Process multiple course files with AI integration."""

    for file_path in file_paths:
        # Parse document
        result = parser.parse_to_markdown(file_path)

        # Index in RagFlow for search
        await ragflow.index_document(
            content=result["content"],
            metadata={
                **result["metadata"],
                "course": "Advanced AI",
                "semester": "Fall 2025"
            }
        )

        # Create wiki article
        await deepwiki.create_article(
            title=result["metadata"]["title"],
            content=result["content"],
            metadata=result["metadata"]
        )

    # Organize knowledge structure
    await ai_integration.organize_knowledge()
```

### Batch Processing

```python
from noteparser.integration.ai_services import AIServicesIntegration

ai = AIServicesIntegration({
    "enable_ragflow": True,
    "enable_deepwiki": True
})

# Process multiple documents
documents = [
    {"content": "...", "metadata": {"title": "Doc 1"}},
    {"content": "...", "metadata": {"title": "Doc 2"}},
]

for doc in documents:
    result = await ai.process_document(doc)
    print(f"Processed: {result}")
```

## Configuration

### Environment Variables

```bash
# AI Services URLs
RAGFLOW_URL=http://localhost:8010
DEEPWIKI_URL=http://localhost:8011

# Database connections (shared with ai-services)
DATABASE_URL=postgresql://noteparser:noteparser@localhost:5434/noteparser
REDIS_URL=redis://localhost:6380/0

# AI Model Configuration
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
```

### Service Configuration

Edit `config/services.yml` to customize AI service behavior:

```yaml
services:
  ragflow:
    enabled: true
    config:
      chunk_size: 512          # Text chunk size for indexing
      top_k: 5                 # Number of results to return
      temperature: 0.7         # AI response creativity

  deepwiki:
    enabled: true
    config:
      auto_link: true          # Automatic cross-linking
      versioning: true         # Article version control
      ai_enhancement: true     # AI content enhancement
```

## Monitoring and Debugging

### Health Checks

```python
# Check all service health
health = await manager.health_check_all()
if not all(health.values()):
    print("Some services are down:", health)
```

### Error Handling

```python
try:
    result = await ragflow.query("complex query")
except Exception as e:
    logger.error(f"RagFlow query failed: {e}")
    # Fallback to basic search
    result = {"error": str(e)}
```

### Performance Monitoring

The AI services include built-in metrics:

- Request counts and durations
- Error rates
- Document processing statistics
- Memory and CPU usage

Access metrics at:
- Prometheus: http://localhost:9090
- Grafana dashboards: http://localhost:3001

## Troubleshooting

### Common Issues

1. **Services not responding**
   ```bash
   # Check if services are running
   docker-compose -f ../noteparser-ai-services/docker-compose.yml ps

   # Restart if needed
   docker-compose -f ../noteparser-ai-services/docker-compose.yml restart
   ```

2. **Connection timeouts**
   ```python
   # Increase timeout in client
   client = RagFlowClient()
   client.timeout = 60  # seconds
   ```

3. **Memory issues with large documents**
   ```yaml
   # Reduce chunk size in config
   ragflow:
     config:
       chunk_size: 256  # Smaller chunks
   ```

### Logs

```bash
# View service logs
docker-compose -f ../noteparser-ai-services/docker-compose.yml logs -f ragflow
docker-compose -f ../noteparser-ai-services/docker-compose.yml logs -f deepwiki
```

## Migration Guide

### From Legacy Integration

If upgrading from mock services:

1. Remove old mock service files (already done in cleanup)
2. Update service URLs in configuration
3. Install new dependencies:
   ```bash
   pip install httpx tenacity
   ```
4. Update imports:
   ```python
   # Old
   from services.ragflow_service import RagFlowService

   # New
   from noteparser.integration.service_client import RagFlowClient
   ```

## Next Steps

- Explore [API Reference](api-reference.md) for detailed method documentation
- See [Configuration](configuration.md) for advanced setup options
- Check out examples in the `/examples` directory
