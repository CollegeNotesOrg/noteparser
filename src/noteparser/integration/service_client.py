"""
Service Client for connecting to deployed AI services.
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class ServiceClientManager:
    """Manager for all AI service clients."""

    def __init__(self, config_path: Optional[str] = None):
        self.clients = {}
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: Optional[str]) -> dict[str, Any]:
        """Load configuration from file or environment variables."""
        config = {}

        # Try to load from config file
        if config_path and Path(config_path).exists():
            config_file = Path(config_path)
        else:
            # Look for config file in standard locations
            possible_paths = [
                Path("config/services.yml"),
                Path("services.yml"),
                Path.cwd() / "config" / "services.yml",
                Path(__file__).parent.parent.parent.parent / "config" / "services.yml",
            ]

            config_file = None
            for path in possible_paths:
                if path.exists():
                    config_file = path
                    break

        if config_file and config_file.exists():
            try:
                with open(config_file) as f:
                    import yaml

                    config = yaml.safe_load(f)
            except Exception as e:
                print(f"Warning: Failed to load config from {config_file}: {e}")
                config = {}

        # Build service URLs from config or environment
        if not config.get("services"):
            config["services"] = {}

        # Ensure service configurations exist
        services_config = config["services"]

        # RagFlow service
        if "ragflow" not in services_config:
            services_config["ragflow"] = {}
        ragflow_config = services_config["ragflow"]
        ragflow_host = ragflow_config.get("host", "localhost")
        ragflow_port = ragflow_config.get("port", 8010)
        ragflow_config["base_url"] = os.getenv(
            "RAGFLOW_URL",
            f"http://{ragflow_host}:{ragflow_port}",
        )

        # DeepWiki service
        if "deepwiki" not in services_config:
            services_config["deepwiki"] = {}
        deepwiki_config = services_config["deepwiki"]
        deepwiki_host = deepwiki_config.get("host", "localhost")
        deepwiki_port = deepwiki_config.get("port", 8011)
        deepwiki_config["base_url"] = os.getenv(
            "DEEPWIKI_URL",
            f"http://{deepwiki_host}:{deepwiki_port}",
        )

        return config

    def get_client(self, service_name: str) -> "AIServiceClient":
        """Get or create a client for the specified service."""
        if service_name not in self.clients:
            service_config = self.config["services"].get(service_name)
            if not service_config:
                raise ValueError(f"Service {service_name} not configured")

            base_url = service_config["base_url"]
            # Use specialized clients if available
            if service_name == "ragflow":
                self.clients[service_name] = RagFlowClient(base_url)
            elif service_name == "deepwiki":
                self.clients[service_name] = DeepWikiClient(base_url)
            else:
                self.clients[service_name] = AIServiceClient(service_name, base_url)

        return self.clients[service_name]

    async def health_check_all(self) -> dict[str, dict[str, Any]]:
        """Check health of all configured services."""
        results = {}
        for service_name in self.config["services"]:
            if self.config["services"][service_name].get("enabled", True):
                try:
                    client = self.get_client(service_name)
                    health_result = await client.health_check()
                    if isinstance(health_result, bool):
                        results[service_name] = {
                            "status": "healthy" if health_result else "unhealthy",
                        }
                    else:
                        results[service_name] = health_result
                except Exception as e:
                    logger.exception(f"Health check failed for {service_name}: {e}")
                    results[service_name] = {"status": "unhealthy", "error": str(e)}
            else:
                results[service_name] = {"status": "disabled"}
        return results

    async def close_all(self):
        """Close all client connections."""
        for client in self.clients.values():
            if hasattr(client, "__aexit__"):
                await client.__aexit__(None, None, None)
            elif hasattr(client, "client") and hasattr(client.client, "aclose"):
                await client.client.aclose()
        self.clients.clear()


class AIServiceClient:
    """Client for communicating with deployed AI services."""

    def __init__(self, service_name: str, base_url: str, timeout: int = 30):
        self.service_name = service_name
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def health_check(self) -> dict[str, Any]:
        """Check if service is healthy."""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                try:
                    health_data = response.json()
                    return {"status": "healthy", "details": health_data}
                except:
                    return {"status": "healthy"}
            else:
                return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            logger.exception(f"Health check failed for {self.service_name}: {e}")
            return {"status": "unhealthy", "error": str(e)}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def post(self, endpoint: str, data: dict[str, Any]) -> dict[str, Any]:
        """Make POST request to service."""
        try:
            response = await self.client.post(f"{self.base_url}/{endpoint}", json=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.exception(f"HTTP error from {self.service_name}: {e}")
            return {"status": "error", "error": str(e)}
        except Exception as e:
            logger.exception(f"Error calling {self.service_name}: {e}")
            return {"status": "error", "error": str(e)}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get(self, endpoint: str, params: Optional[dict] = None) -> dict[str, Any]:
        """Make GET request to service."""
        try:
            response = await self.client.get(f"{self.base_url}/{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.exception(f"HTTP error from {self.service_name}: {e}")
            return {"status": "error", "error": str(e)}
        except Exception as e:
            logger.exception(f"Error calling {self.service_name}: {e}")
            return {"status": "error", "error": str(e)}


class RagFlowClient(AIServiceClient):
    """Client specifically for RagFlow service."""

    def __init__(self, base_url: Optional[str] = None):
        if base_url is None:
            base_url = os.getenv("RAGFLOW_URL", "http://localhost:8010")
        super().__init__("ragflow", base_url)

    async def index_document(self, content: str, metadata: dict[str, Any]) -> dict[str, Any]:
        """Index a document in RagFlow."""
        return await self.post("index", {"content": content, "metadata": metadata})

    async def query(self, query: str, k: int = 5, filters: Optional[dict] = None) -> dict[str, Any]:
        """Query RagFlow for answers."""
        return await self.post("query", {"query": query, "k": k, "filters": filters or {}})

    async def extract_insights(self, content: str) -> dict[str, Any]:
        """Extract insights from content."""
        return await self.post("insights", {"content": content})

    async def get_stats(self) -> dict[str, Any]:
        """Get RagFlow statistics."""
        return await self.get("stats")


class DeepWikiClient(AIServiceClient):
    """Client specifically for DeepWiki service."""

    def __init__(self, base_url: Optional[str] = None):
        if base_url is None:
            base_url = os.getenv("DEEPWIKI_URL", "http://localhost:8011")
        super().__init__("deepwiki", base_url)

    async def create_article(
        self,
        title: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Create a wiki article."""
        return await self.post(
            "article",
            {"title": title, "content": content, "metadata": metadata or {}},
        )

    async def update_article(self, article_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        """Update a wiki article."""
        return await self.post(f"article/{article_id}", updates)

    async def get_article(self, article_id: str) -> dict[str, Any]:
        """Get a wiki article."""
        return await self.get(f"article/{article_id}")

    async def search(self, query: str, limit: int = 10) -> dict[str, Any]:
        """Search wiki articles."""
        return await self.post("search", {"query": query, "limit": limit})

    async def ask_assistant(
        self,
        question: str,
        context_articles: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Ask the AI assistant a question."""
        return await self.post("ask", {"question": question, "context_articles": context_articles})

    async def get_link_graph(
        self,
        article_id: Optional[str] = None,
        depth: int = 2,
    ) -> dict[str, Any]:
        """Get the wiki link graph."""
        params = {"depth": depth}
        if article_id:
            params["article_id"] = article_id
        return await self.get("graph", params)

    async def find_similar(self, article_id: str, limit: int = 5) -> dict[str, Any]:
        """Find similar articles."""
        return await self.get(f"similar/{article_id}", {"limit": limit})


# Example usage
async def example_usage():
    """Example of using the service clients."""

    # Create manager
    manager = ServiceClientManager()

    try:
        # Check health of all services
        health_status = await manager.health_check_all()
        print(f"Service health: {health_status}")

        # Use RagFlow client
        ragflow = manager.get_client("ragflow")
        if ragflow:
            # Index a document
            result = await ragflow.index_document(
                content="This is a test document about machine learning.",
                metadata={"title": "ML Test", "author": "Test"},
            )
            print(f"Index result: {result}")

            # Query
            query_result = await ragflow.query(query="What is machine learning?", k=3)
            print(f"Query result: {query_result}")

        # Use DeepWiki client
        deepwiki = manager.get_client("deepwiki")
        if deepwiki:
            # Create article
            article_result = await deepwiki.create_article(
                title="Introduction to AI",
                content="Artificial Intelligence is...",
                metadata={"tags": ["AI", "intro"]},
            )
            print(f"Article created: {article_result}")

            # Search wiki
            search_result = await deepwiki.search("AI", limit=5)
            print(f"Search result: {search_result}")

    finally:
        # Clean up
        await manager.close_all()


if __name__ == "__main__":
    asyncio.run(example_usage())
