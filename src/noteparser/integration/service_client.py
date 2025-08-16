"""
Service Client for connecting to deployed AI services.
"""

import os
import logging
from typing import Dict, Any, Optional, List
import httpx
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class AIServiceClient:
    """Client for communicating with deployed AI services."""
    
    def __init__(self, service_name: str, base_url: str, timeout: int = 30):
        self.service_name = service_name
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def health_check(self) -> bool:
        """Check if service is healthy."""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed for {self.service_name}: {e}")
            return False
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make POST request to service."""
        try:
            response = await self.client.post(
                f"{self.base_url}/{endpoint}",
                json=data
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from {self.service_name}: {e}")
            return {"status": "error", "error": str(e)}
        except Exception as e:
            logger.error(f"Error calling {self.service_name}: {e}")
            return {"status": "error", "error": str(e)}
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make GET request to service."""
        try:
            response = await self.client.get(
                f"{self.base_url}/{endpoint}",
                params=params
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from {self.service_name}: {e}")
            return {"status": "error", "error": str(e)}
        except Exception as e:
            logger.error(f"Error calling {self.service_name}: {e}")
            return {"status": "error", "error": str(e)}

class RagFlowClient(AIServiceClient):
    """Client specifically for RagFlow service."""
    
    def __init__(self, base_url: str = None):
        if base_url is None:
            base_url = os.getenv("RAGFLOW_URL", "http://localhost:8010")
        super().__init__("ragflow", base_url)
    
    async def index_document(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Index a document in RagFlow."""
        return await self.post("index", {
            "content": content,
            "metadata": metadata
        })
    
    async def query(self, query: str, k: int = 5, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """Query RagFlow for answers."""
        return await self.post("query", {
            "query": query,
            "k": k,
            "filters": filters or {}
        })
    
    async def extract_insights(self, content: str) -> Dict[str, Any]:
        """Extract insights from content."""
        return await self.post("insights", {
            "content": content
        })
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get RagFlow statistics."""
        return await self.get("stats")

class DeepWikiClient(AIServiceClient):
    """Client specifically for DeepWiki service."""
    
    def __init__(self, base_url: str = None):
        if base_url is None:
            base_url = os.getenv("DEEPWIKI_URL", "http://localhost:8011")
        super().__init__("deepwiki", base_url)
    
    async def create_article(self, title: str, content: str, 
                           metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Create a wiki article."""
        return await self.post("article", {
            "title": title,
            "content": content,
            "metadata": metadata or {}
        })
    
    async def update_article(self, article_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a wiki article."""
        return await self.post(f"article/{article_id}", updates)
    
    async def get_article(self, article_id: str) -> Dict[str, Any]:
        """Get a wiki article."""
        return await self.get(f"article/{article_id}")
    
    async def search(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search wiki articles."""
        return await self.post("search", {
            "query": query,
            "limit": limit
        })
    
    async def ask_assistant(self, question: str, 
                          context_articles: Optional[List[str]] = None) -> Dict[str, Any]:
        """Ask the AI assistant a question."""
        return await self.post("ask", {
            "question": question,
            "context_articles": context_articles
        })
    
    async def get_link_graph(self, article_id: Optional[str] = None, 
                           depth: int = 2) -> Dict[str, Any]:
        """Get the wiki link graph."""
        params = {"depth": depth}
        if article_id:
            params["article_id"] = article_id
        return await self.get("graph", params)
    
    async def find_similar(self, article_id: str, limit: int = 5) -> Dict[str, Any]:
        """Find similar articles."""
        return await self.get(f"similar/{article_id}", {"limit": limit})

class ServiceClientManager:
    """Manages all AI service clients."""
    
    def __init__(self):
        self.clients = {}
        self.initialize_clients()
    
    def initialize_clients(self):
        """Initialize all service clients."""
        # RagFlow client
        self.clients["ragflow"] = RagFlowClient()
        
        # DeepWiki client
        self.clients["deepwiki"] = DeepWikiClient()
        
        # Future service clients can be added here
        # self.clients["dolphin"] = DolphinClient()
        # self.clients["langextract"] = LangExtractClient()
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all services."""
        results = {}
        for name, client in self.clients.items():
            results[name] = await client.health_check()
        return results
    
    def get_client(self, service_name: str) -> Optional[AIServiceClient]:
        """Get a specific service client."""
        return self.clients.get(service_name)
    
    async def close_all(self):
        """Close all client connections."""
        for client in self.clients.values():
            await client.client.aclose()

# Example usage
async def example_usage():
    """Example of using the service clients."""
    
    # Create manager
    manager = ServiceClientManager()
    
    # Check health of all services
    health_status = await manager.health_check_all()
    print(f"Service health: {health_status}")
    
    # Use RagFlow client
    ragflow = manager.get_client("ragflow")
    if ragflow:
        # Index a document
        result = await ragflow.index_document(
            content="This is a test document about machine learning.",
            metadata={"title": "ML Test", "author": "Test"}
        )
        print(f"Index result: {result}")
        
        # Query
        query_result = await ragflow.query(
            query="What is machine learning?",
            k=3
        )
        print(f"Query result: {query_result}")
    
    # Use DeepWiki client
    deepwiki = manager.get_client("deepwiki")
    if deepwiki:
        # Create article
        article_result = await deepwiki.create_article(
            title="Introduction to AI",
            content="Artificial Intelligence is...",
            metadata={"tags": ["AI", "intro"]}
        )
        print(f"Article created: {article_result}")
        
        # Search wiki
        search_result = await deepwiki.search("AI", limit=5)
        print(f"Search result: {search_result}")
    
    # Clean up
    await manager.close_all()

if __name__ == "__main__":
    asyncio.run(example_usage())