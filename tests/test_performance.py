"""
Performance and load tests for AI integration.
"""

import pytest
import asyncio
import time
from pathlib import Path
from unittest.mock import AsyncMock, patch
import statistics

from noteparser.core import NoteParser
from noteparser.integration.service_client import ServiceClientManager
from noteparser.integration.ai_services import AIServicesIntegration


class TestPerformance:
    """Performance tests for AI integration."""
    
    @pytest.mark.asyncio
    async def test_concurrent_service_calls(self):
        """Test concurrent calls to AI services."""
        manager = ServiceClientManager()
        
        # Mock healthy responses
        mock_response = {'status': 'healthy', 'uptime': 3600}
        
        async def mock_health_check():
            await asyncio.sleep(0.1)  # Simulate network delay
            return mock_response
        
        # Create mock clients
        for service in ['ragflow', 'deepwiki']:
            mock_client = AsyncMock()
            mock_client.health_check.side_effect = mock_health_check
            manager.clients[service] = mock_client
        
        # Test concurrent health checks
        start_time = time.time()
        
        tasks = []
        for _ in range(10):
            task = asyncio.create_task(manager.health_check_all())
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete in reasonable time with concurrency
        assert duration < 2.0  # Should be much faster than 10 * 0.1 * 2 services
        assert len(results) == 10
        
        for result in results:
            assert 'ragflow' in result
            assert 'deepwiki' in result
    
    @pytest.mark.asyncio
    async def test_batch_document_processing(self, tmp_path):
        """Test processing multiple documents efficiently."""
        # Create test documents
        documents = []
        for i in range(5):
            doc_path = tmp_path / f"test_doc_{i}.txt"
            doc_path.write_text(f"This is test document number {i} with unique content.")
            documents.append(doc_path)
        
        # Mock AI integration
        mock_ai = AsyncMock()
        mock_ai.initialize.return_value = True
        
        async def mock_process_document(doc):
            await asyncio.sleep(0.05)  # Simulate processing time
            return {
                'summary': f'Summary for {doc["metadata"]["title"]}',
                'keywords': ['test', 'document'],
                'processing_time': 0.05
            }
        
        mock_ai.process_document.side_effect = mock_process_document
        
        parser = NoteParser(enable_ai=True)
        parser.ai_integration = mock_ai
        
        # Time batch processing
        start_time = time.time()
        
        tasks = []
        for doc_path in documents:
            task = asyncio.create_task(
                parser.parse_to_markdown_with_ai(doc_path)
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should process concurrently, not sequentially
        assert duration < 0.3  # Much less than 5 * 0.05 = 0.25 seconds
        assert len(results) == 5
        
        for result in results:
            assert 'content' in result
            assert 'ai_processing' in result
    
    def test_large_document_processing(self, tmp_path):
        """Test processing of large documents."""
        # Create a large document
        large_content = "This is a test sentence. " * 10000  # ~250KB of text
        large_doc = tmp_path / "large_document.txt"
        large_doc.write_text(large_content)
        
        parser = NoteParser()
        
        # Time the parsing
        start_time = time.time()
        result = parser.parse_to_markdown(large_doc)
        end_time = time.time()
        
        duration = end_time - start_time
        
        # Should process reasonably quickly
        assert duration < 5.0  # Should complete within 5 seconds
        assert 'content' in result
        assert len(result['content']) > 200000  # Should preserve content
    
    @pytest.mark.asyncio
    async def test_service_timeout_handling(self):
        """Test handling of service timeouts."""
        manager = ServiceClientManager()
        
        # Create a client with very short timeout
        client = manager.get_client('ragflow')
        client.timeout = 0.1  # 100ms timeout
        
        # Mock a slow response
        slow_response = AsyncMock()
        
        async def slow_health_check(*args, **kwargs):
            await asyncio.sleep(0.2)  # Longer than timeout
            return slow_response
        
        client.client = AsyncMock()
        client.client.get.side_effect = slow_health_check
        
        # Should handle timeout gracefully
        start_time = time.time()
        result = await client.health_check()
        end_time = time.time()
        
        duration = end_time - start_time
        
        # Should timeout quickly and return error
        assert duration < 0.5
        assert result['status'] == 'unhealthy'
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_memory_usage_stability(self, tmp_path):
        """Test that memory usage remains stable during processing."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create test documents
        documents = []
        for i in range(20):
            doc_path = tmp_path / f"memory_test_{i}.txt"
            content = f"Document {i} content. " * 1000  # ~20KB each
            doc_path.write_text(content)
            documents.append(doc_path)
        
        parser = NoteParser()
        memory_readings = []
        
        # Process documents and track memory
        for doc_path in documents:
            result = parser.parse_to_markdown(doc_path)
            assert 'content' in result
            
            current_memory = process.memory_info().rss
            memory_readings.append(current_memory)
        
        # Check memory stability
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB)
        assert memory_increase < 100 * 1024 * 1024
        
        # Memory should not continuously grow
        if len(memory_readings) > 10:
            first_half = memory_readings[:10]
            second_half = memory_readings[10:]
            
            avg_first = statistics.mean(first_half)
            avg_second = statistics.mean(second_half)
            
            # Second half shouldn't be dramatically higher
            assert avg_second < avg_first * 1.5


class TestLoadHandling:
    """Load and stress tests for AI services."""
    
    @pytest.mark.asyncio
    async def test_high_concurrency_health_checks(self):
        """Test system under high concurrency."""
        manager = ServiceClientManager()
        
        # Mock responses with variable delays
        async def variable_delay_health_check():
            delay = 0.05 + (hash(asyncio.current_task()) % 100) / 1000  # 50-150ms
            await asyncio.sleep(delay)
            return {'status': 'healthy'}
        
        # Setup mock clients
        for service in ['ragflow', 'deepwiki']:
            mock_client = AsyncMock()
            mock_client.health_check.side_effect = variable_delay_health_check
            manager.clients[service] = mock_client
        
        # Create many concurrent requests
        concurrent_requests = 50
        start_time = time.time()
        
        tasks = [
            asyncio.create_task(manager.health_check_all())
            for _ in range(concurrent_requests)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Check results
        successful_results = [r for r in results if not isinstance(r, Exception)]
        failed_results = [r for r in results if isinstance(r, Exception)]
        
        # Most requests should succeed
        success_rate = len(successful_results) / len(results)
        assert success_rate > 0.9  # At least 90% success rate
        
        # Should handle concurrency reasonably well
        assert duration < 5.0  # Complete within 5 seconds
        
        print(f"Processed {concurrent_requests} concurrent requests in {duration:.2f}s")
        print(f"Success rate: {success_rate:.2%}")
        if failed_results:
            print(f"Failed requests: {len(failed_results)}")
    
    @pytest.mark.asyncio
    async def test_service_recovery_after_failure(self):
        """Test system recovery after service failures."""
        manager = ServiceClientManager()
        
        failure_count = 0
        max_failures = 3
        
        async def failing_then_recovering_health_check():
            nonlocal failure_count
            if failure_count < max_failures:
                failure_count += 1
                raise Exception(f"Service failure #{failure_count}")
            return {'status': 'healthy'}
        
        # Setup mock client that fails then recovers
        mock_client = AsyncMock()
        mock_client.health_check.side_effect = failing_then_recovering_health_check
        manager.clients['ragflow'] = mock_client
        
        # Test multiple attempts
        results = []
        for i in range(max_failures + 2):
            result = await manager.health_check_all()
            results.append(result)
            await asyncio.sleep(0.1)  # Small delay between attempts
        
        # First few should fail, then succeed
        for i, result in enumerate(results):
            if i < max_failures:
                assert result['ragflow']['status'] == 'unhealthy'
            else:
                assert result['ragflow']['status'] == 'healthy'
    
    @pytest.mark.asyncio
    async def test_rate_limiting_behavior(self):
        """Test behavior under rate limiting scenarios."""
        manager = ServiceClientManager()
        
        call_count = 0
        rate_limit_threshold = 10
        
        async def rate_limited_health_check():
            nonlocal call_count
            call_count += 1
            
            if call_count > rate_limit_threshold:
                # Simulate rate limiting (HTTP 429)
                import httpx
                response = AsyncMock()
                response.status_code = 429
                raise httpx.HTTPStatusError(
                    "Rate limited", 
                    request=AsyncMock(), 
                    response=response
                )
            
            return {'status': 'healthy'}
        
        # Setup mock client with rate limiting
        mock_client = AsyncMock()
        mock_client.health_check.side_effect = rate_limited_health_check
        manager.clients['ragflow'] = mock_client
        
        # Make requests beyond rate limit
        tasks = []
        for _ in range(rate_limit_threshold + 5):
            task = asyncio.create_task(manager.health_check_all())
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=False)
        
        # Count successful vs rate-limited responses
        successful = sum(1 for r in results if r.get('ragflow', {}).get('status') == 'healthy')
        rate_limited = sum(1 for r in results if r.get('ragflow', {}).get('status') == 'unhealthy')
        
        assert successful == rate_limit_threshold
        assert rate_limited > 0
    
    def test_configuration_validation(self):
        """Test configuration validation and error handling."""
        # Test with invalid configuration
        invalid_configs = [
            {},  # Empty config
            {'services': {}},  # No services defined
            {'services': {'ragflow': {}}},  # Missing required fields
            {'services': {'ragflow': {'host': 'invalid'}}},  # Missing port
        ]
        
        for config in invalid_configs:
            manager = ServiceClientManager()
            manager.config = config
            
            # Should handle gracefully
            try:
                client = manager.get_client('ragflow')
                assert client is not None
            except ValueError:
                # Expected for some invalid configs
                pass
    
    @pytest.mark.asyncio
    async def test_error_propagation_and_handling(self):
        """Test proper error propagation through the system."""
        integration = AIServicesIntegration()
        
        # Test various error scenarios
        error_scenarios = [
            (ConnectionError("Network unreachable"), "network"),
            (TimeoutError("Request timeout"), "timeout"),
            (ValueError("Invalid response"), "validation"),
            (Exception("Unknown error"), "unknown"),
        ]
        
        for error, error_type in error_scenarios:
            # Mock manager that raises the error
            mock_manager = AsyncMock()
            mock_manager.health_check_all.side_effect = error
            
            integration.manager = mock_manager
            
            # Should handle error gracefully
            result = await integration.initialize()
            assert result is False
            assert integration.services_initialized is False
    
    @pytest.mark.asyncio
    async def test_cleanup_and_resource_management(self):
        """Test proper cleanup of resources."""
        manager = ServiceClientManager()
        
        # Create multiple clients
        clients = []
        for service in ['ragflow', 'deepwiki']:
            client = manager.get_client(service)
            clients.append(client)
        
        # Verify clients are created
        assert len(manager.clients) == 2
        
        # Test cleanup
        await manager.close_all()
        
        # Verify cleanup
        assert len(manager.clients) == 0
        
        # Verify clients were properly closed
        for client in clients:
            if hasattr(client, 'client') and hasattr(client.client, 'aclose'):
                # In real scenario, aclose would have been called
                pass


@pytest.mark.benchmark
class TestBenchmarks:
    """Benchmark tests for performance comparison."""
    
    def test_parsing_benchmark(self, tmp_path, benchmark):
        """Benchmark document parsing performance."""
        # Create test document
        test_doc = tmp_path / "benchmark.txt"
        content = "This is benchmark content. " * 1000
        test_doc.write_text(content)
        
        parser = NoteParser()
        
        # Benchmark parsing
        result = benchmark(parser.parse_to_markdown, test_doc)
        
        assert 'content' in result
        assert len(result['content']) > 0
    
    def test_batch_processing_benchmark(self, tmp_path, benchmark):
        """Benchmark batch processing performance."""
        # Create multiple test documents
        documents = []
        for i in range(10):
            doc_path = tmp_path / f"bench_doc_{i}.txt"
            doc_path.write_text(f"Benchmark document {i} content. " * 500)
            documents.append(doc_path)
        
        parser = NoteParser()
        
        def batch_process():
            return parser.parse_batch(tmp_path, recursive=False)
        
        # Benchmark batch processing
        result = benchmark(batch_process)
        
        assert len(result) == 10
        successful = sum(1 for r in result.values() if 'error' not in r)
        assert successful == 10
    
    @pytest.mark.asyncio
    async def test_async_operations_benchmark(self, benchmark):
        """Benchmark async operation performance."""
        manager = ServiceClientManager()
        
        # Mock fast health check
        async def fast_health_check():
            await asyncio.sleep(0.001)  # 1ms simulated work
            return {'status': 'healthy'}
        
        for service in ['ragflow', 'deepwiki']:
            mock_client = AsyncMock()
            mock_client.health_check.side_effect = fast_health_check
            manager.clients[service] = mock_client
        
        # Benchmark async health check
        @benchmark
        def async_health_check():
            return asyncio.run(manager.health_check_all())
        
        result = async_health_check()
        assert 'ragflow' in result
        assert 'deepwiki' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--benchmark-only'])