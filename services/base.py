"""
Base service class for all microservices.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
import asyncio
from datetime import datetime
import aiohttp
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ServiceConfig:
    """Configuration for a microservice."""
    name: str
    version: str
    host: str = "localhost"
    port: int = 8000
    timeout: int = 30
    retry_count: int = 3
    health_check_interval: int = 60

class BaseService(ABC):
    """Abstract base class for all microservices."""
    
    def __init__(self, config: ServiceConfig):
        self.config = config
        self.is_healthy = False
        self.last_health_check = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._health_check_task = None
    
    async def start(self):
        """Start the service."""
        logger.info(f"Starting service: {self.config.name}")
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        # Start health check background task
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        await self.initialize()
    
    async def stop(self):
        """Stop the service."""
        logger.info(f"Stopping service: {self.config.name}")
        if self._health_check_task:
            self._health_check_task.cancel()
        if self._session:
            await self._session.close()
        await self.cleanup()
    
    @abstractmethod
    async def initialize(self):
        """Initialize service-specific resources."""
        pass
    
    @abstractmethod
    async def cleanup(self):
        """Clean up service-specific resources."""
        pass
    
    @abstractmethod
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data through the service."""
        pass
    
    async def health_check(self) -> bool:
        """Check if the service is healthy."""
        try:
            # Default implementation - override in subclasses
            return await self._check_endpoint_health()
        except Exception as e:
            logger.error(f"Health check failed for {self.config.name}: {e}")
            return False
    
    async def _check_endpoint_health(self) -> bool:
        """Check health via HTTP endpoint."""
        if not self._session:
            return False
        
        try:
            url = f"http://{self.config.host}:{self.config.port}/health"
            async with self._session.get(url) as response:
                return response.status == 200
        except:
            return False
    
    async def _health_check_loop(self):
        """Background task for periodic health checks."""
        while True:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                self.is_healthy = await self.health_check()
                self.last_health_check = datetime.utcnow()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
    
    async def call_api(self, endpoint: str, method: str = "GET", 
                       data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make API call to the service."""
        if not self._session:
            raise RuntimeError(f"Service {self.config.name} not started")
        
        url = f"http://{self.config.host}:{self.config.port}/{endpoint}"
        
        for attempt in range(self.config.retry_count):
            try:
                async with self._session.request(
                    method, url, json=data
                ) as response:
                    response.raise_for_status()
                    return await response.json()
            except Exception as e:
                if attempt == self.config.retry_count - 1:
                    raise
                logger.warning(f"API call failed (attempt {attempt + 1}): {e}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

class ServiceOrchestrator:
    """Orchestrates multiple services."""
    
    def __init__(self):
        self.services: Dict[str, BaseService] = {}
    
    async def register_service(self, service: BaseService):
        """Register and start a service."""
        await service.start()
        self.services[service.config.name] = service
        logger.info(f"Registered service: {service.config.name}")
    
    async def process_pipeline(self, data: Dict[str, Any], 
                              pipeline: list[str]) -> Dict[str, Any]:
        """Process data through a pipeline of services."""
        result = data
        for service_name in pipeline:
            if service_name not in self.services:
                raise ValueError(f"Service {service_name} not found")
            
            service = self.services[service_name]
            result = await service.process(result)
            logger.info(f"Processed through {service_name}")
        
        return result
    
    async def shutdown(self):
        """Shutdown all services."""
        for service in self.services.values():
            await service.stop()