"""
AI Services Integration Module

Integrates various AI/ML services into the noteparser workflow.
"""

import asyncio
from typing import Dict, Any, List, Optional
import logging
from pathlib import Path
import sys

# Add services to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from services.base import ServiceOrchestrator
from services.ragflow_service import RagFlowService
from services.deepwiki_service import DeepWikiService

logger = logging.getLogger(__name__)

class AIServicesIntegration:
    """Main integration class for AI services."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.orchestrator = ServiceOrchestrator()
        self.services_initialized = False
    
    async def initialize(self):
        """Initialize all AI services."""
        if self.services_initialized:
            return
        
        logger.info("Initializing AI services...")
        
        # Initialize RagFlow for RAG capabilities
        if self.config.get("enable_ragflow", True):
            ragflow = RagFlowService()
            await self.orchestrator.register_service(ragflow)
            logger.info("RagFlow service initialized")
        
        # Initialize DeepWiki for wiki functionality  
        if self.config.get("enable_deepwiki", True):
            deepwiki = DeepWikiService()
            await self.orchestrator.register_service(deepwiki)
            logger.info("DeepWiki service initialized")
        
        self.services_initialized = True
        logger.info("All AI services initialized successfully")
    
    async def process_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Process a document through AI services."""
        if not self.services_initialized:
            await self.initialize()
        
        results = {}
        
        # Extract content and metadata
        content = document.get("content", "")
        metadata = document.get("metadata", {})
        
        # Process through RagFlow for indexing and insights
        if "ragflow" in self.orchestrator.services:
            try:
                # Index document
                rag_result = await self.orchestrator.services["ragflow"].process({
                    "action": "index",
                    "content": content,
                    "metadata": metadata
                })
                results["rag_indexing"] = rag_result
                
                # Extract insights
                insights = await self.orchestrator.services["ragflow"].process({
                    "action": "extract_insights",
                    "content": content,
                    "insight_type": "all"
                })
                results["insights"] = insights
            except Exception as e:
                logger.error(f"RagFlow processing failed: {e}")
                results["rag_error"] = str(e)
        
        # Create wiki article
        if "deepwiki" in self.orchestrator.services:
            try:
                wiki_result = await self.orchestrator.services["deepwiki"].process({
                    "action": "create",
                    "title": metadata.get("title", "Untitled"),
                    "content": content,
                    "metadata": metadata
                })
                results["wiki_article"] = wiki_result
                
                # Auto-link with existing articles
                link_result = await self.orchestrator.services["deepwiki"].process({
                    "action": "link",
                    "article_id": wiki_result.get("article_id")
                })
                results["wiki_links"] = link_result
            except Exception as e:
                logger.error(f"DeepWiki processing failed: {e}")
                results["wiki_error"] = str(e)
        
        return results
    
    async def query_knowledge(self, query: str, 
                            filters: Optional[Dict] = None) -> Dict[str, Any]:
        """Query the knowledge base."""
        if not self.services_initialized:
            await self.initialize()
        
        results = {}
        
        # Query through RagFlow
        if "ragflow" in self.orchestrator.services:
            try:
                rag_response = await self.orchestrator.services["ragflow"].process({
                    "action": "query",
                    "query": query,
                    "filters": filters or {}
                })
                results["rag_response"] = rag_response
            except Exception as e:
                logger.error(f"RagFlow query failed: {e}")
                results["rag_error"] = str(e)
        
        # Query through DeepWiki
        if "deepwiki" in self.orchestrator.services:
            try:
                # Search wiki
                wiki_search = await self.orchestrator.services["deepwiki"].process({
                    "action": "search",
                    "query": query,
                    "search_type": "content"
                })
                results["wiki_search"] = wiki_search
                
                # Ask AI assistant
                ai_response = await self.orchestrator.services["deepwiki"].process({
                    "action": "ask",
                    "question": query
                })
                results["ai_assistant"] = ai_response
            except Exception as e:
                logger.error(f"DeepWiki query failed: {e}")
                results["wiki_error"] = str(e)
        
        return results
    
    async def organize_knowledge(self) -> Dict[str, Any]:
        """Organize and structure the knowledge base."""
        if not self.services_initialized:
            await self.initialize()
        
        results = {}
        
        # Organize wiki structure
        if "deepwiki" in self.orchestrator.services:
            try:
                org_result = await self.orchestrator.services["deepwiki"].process({
                    "action": "organize"
                })
                results["wiki_organization"] = org_result
            except Exception as e:
                logger.error(f"Wiki organization failed: {e}")
                results["organization_error"] = str(e)
        
        return results
    
    async def shutdown(self):
        """Shutdown all services."""
        if self.orchestrator:
            await self.orchestrator.shutdown()
            self.services_initialized = False
            logger.info("All AI services shut down")

# Integration with existing noteparser
def integrate_ai_services(parser_instance):
    """Integrate AI services with noteparser instance."""
    
    # Create AI services integration
    ai_integration = AIServicesIntegration()
    
    # Add to parser instance
    parser_instance.ai_services = ai_integration
    
    # Extend parser methods
    original_parse = parser_instance.parse_to_markdown
    
    async def enhanced_parse(file_path: str, **kwargs) -> Dict[str, Any]:
        """Enhanced parse with AI services."""
        # Original parsing
        result = original_parse(file_path, **kwargs)
        
        # Process through AI services
        if hasattr(parser_instance, 'ai_services'):
            ai_result = await parser_instance.ai_services.process_document({
                "content": result.get("content", ""),
                "metadata": {
                    "title": Path(file_path).stem,
                    "file_path": str(file_path),
                    **result.get("metadata", {})
                }
            })
            result["ai_processing"] = ai_result
        
        return result
    
    parser_instance.parse_to_markdown_with_ai = enhanced_parse
    
    return parser_instance