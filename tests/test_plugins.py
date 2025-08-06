"""Tests for plugin system functionality."""

import pytest
from pathlib import Path
from unittest.mock import Mock

from noteparser.plugins.base import BasePlugin, PluginManager
from noteparser.plugins.builtin.math_plugin import MathPlugin
from noteparser.plugins.builtin.cs_plugin import ComputerSciencePlugin


class TestPlugin(BasePlugin):
    """Test plugin for unit testing."""
    
    name = "test_plugin"
    version = "1.0.0"
    description = "Test plugin for unit testing"
    supported_formats = ['.txt', '.md']
    course_types = ['test', 'demo']
    
    def process_content(self, content: str, metadata: dict) -> dict:
        """Simple test processing - just add a prefix."""
        return {
            'content': f"PROCESSED: {content}",
            'metadata': {**metadata, 'processed_by': self.name}
        }


class TestBasePlugin:
    """Test cases for the base plugin class."""
    
    def test_init(self):
        """Test plugin initialization."""
        plugin = TestPlugin()
        assert plugin.name == "test_plugin"
        assert plugin.version == "1.0.0"
        assert plugin.enabled is True
        
    def test_init_with_config(self):
        """Test plugin initialization with config."""
        config = {'enabled': False, 'custom_setting': 'value'}
        plugin = TestPlugin(config)
        assert plugin.enabled is False
        assert plugin.config['custom_setting'] == 'value'
    
    def test_can_handle_format(self):
        """Test format handling detection."""
        plugin = TestPlugin()
        
        # Supported formats
        assert plugin.can_handle(Path('test.txt'), {})
        assert plugin.can_handle(Path('test.md'), {})
        
        # Unsupported formats
        assert not plugin.can_handle(Path('test.pdf'), {})
    
    def test_can_handle_course_type(self):
        """Test course type handling detection."""
        plugin = TestPlugin()
        
        # Supported course types
        assert plugin.can_handle(Path('test.txt'), {'course': 'TEST101'})
        assert plugin.can_handle(Path('test.txt'), {'course': 'demo_course'})
        
        # Unsupported course types
        assert not plugin.can_handle(Path('test.txt'), {'course': 'MATH101'})
    
    def test_process_content(self):
        """Test content processing."""
        plugin = TestPlugin()
        content = "Hello, world!"
        metadata = {'course': 'TEST101'}
        
        result = plugin.process_content(content, metadata)
        
        assert result['content'] == "PROCESSED: Hello, world!"
        assert result['metadata']['processed_by'] == 'test_plugin'
        assert result['metadata']['course'] == 'TEST101'
    
    def test_validate_config(self):
        """Test configuration validation."""
        plugin = TestPlugin()
        errors = plugin.validate_config()
        assert len(errors) == 0  # Should be valid
        
        # Test plugin with missing name
        class InvalidPlugin(BasePlugin):
            name = ""
            
            def process_content(self, content, metadata):
                return {'content': content, 'metadata': metadata}
        
        invalid_plugin = InvalidPlugin()
        errors = invalid_plugin.validate_config()
        assert len(errors) > 0
        assert "Plugin name is required" in errors
    
    def test_get_info(self):
        """Test plugin info retrieval."""
        plugin = TestPlugin()
        info = plugin.get_info()
        
        expected_keys = ['name', 'version', 'description', 'supported_formats', 
                        'course_types', 'enabled', 'config']
        for key in expected_keys:
            assert key in info


class TestMathPlugin:
    """Test cases for the mathematics plugin."""
    
    @pytest.fixture
    def math_plugin(self):
        """Create a math plugin instance."""
        return MathPlugin()
    
    def test_init(self, math_plugin):
        """Test math plugin initialization."""
        assert math_plugin.name == "math_processor"
        assert "math" in math_plugin.course_types
        assert "mathematics" in math_plugin.course_types
    
    def test_can_handle_math_course(self, math_plugin):
        """Test math course detection."""
        assert math_plugin.can_handle(Path('test.pdf'), {'course': 'MATH101'})
        assert math_plugin.can_handle(Path('test.pdf'), {'course': 'Calculus'})
        assert not math_plugin.can_handle(Path('test.pdf'), {'course': 'CS101'})
    
    def test_enhance_equations(self, math_plugin):
        """Test equation enhancement."""
        content = """
        Here is an inline equation $x = y + z$.
        
        And a display equation:
        $$E = mc^2$$
        
        Another equation: $$F = ma$$
        """
        
        enhanced_content, count = math_plugin._enhance_equations(content)
        
        assert count == 3  # Should find 3 equations
        assert '$x = y + z$' in enhanced_content  # Inline preserved
        assert '\\tag{1}' in enhanced_content  # Display equations numbered
    
    def test_format_theorems(self, math_plugin):
        """Test theorem formatting."""
        content = """
        Theorem: This is a mathematical theorem.
        Proof: Here is the proof.
        Definition: This is a definition.
        Q.E.D.
        """
        
        formatted_content, count = math_plugin._format_theorems(content)
        
        assert count > 0
        assert '**Theorem**:' in formatted_content
        assert '**Proof**:' in formatted_content
        assert '**Definition**:' in formatted_content
        assert '*Q.E.D.* ∎' in formatted_content
    
    def test_standardize_symbols(self, math_plugin):
        """Test symbol standardization."""
        content = "The value of pi is approximately 3.14 and infinity is large."
        
        standardized = math_plugin._standardize_symbols(content)
        
        assert 'π' in standardized
        assert '∞' in standardized
    
    def test_process_content(self, math_plugin):
        """Test complete math content processing."""
        content = """
        # Linear Algebra
        
        Theorem: Vector spaces are important.
        The equation is $v = u + w$ and pi = 3.14.
        
        $$A = \\begin{pmatrix} 1 & 2 \\\\ 3 & 4 \\end{pmatrix}$$
        """
        
        metadata = {'course': 'MATH201'}
        result = math_plugin.process_content(content, metadata)
        
        assert 'content' in result
        assert 'metadata' in result
        assert result['metadata']['math_equations'] > 0
        assert '**Theorem**' in result['content']
        assert 'π' in result['content']


class TestComputerSciencePlugin:
    """Test cases for the computer science plugin."""
    
    @pytest.fixture  
    def cs_plugin(self):
        """Create a CS plugin instance."""
        return ComputerSciencePlugin()
    
    def test_init(self, cs_plugin):
        """Test CS plugin initialization."""
        assert cs_plugin.name == "cs_processor"
        assert "cs" in cs_plugin.course_types
        assert "programming" in cs_plugin.course_types
    
    def test_detect_programming_language(self, cs_plugin):
        """Test programming language detection."""
        # Python
        python_code = "def hello():\n    print('Hello')\nimport sys"
        assert cs_plugin._detect_programming_language(python_code) == 'python'
        
        # JavaScript
        js_code = "function hello() {\n    console.log('Hello');\n}\nlet x = 5;"
        assert cs_plugin._detect_programming_language(js_code) == 'javascript'
        
        # Unknown
        text = "This is just regular text without code patterns"
        assert cs_plugin._detect_programming_language(text) == 'text'
    
    def test_looks_like_code_line(self, cs_plugin):
        """Test code line detection."""
        # Code lines
        assert cs_plugin._looks_like_code_line("def hello():")
        assert cs_plugin._looks_like_code_line("x = 5")
        assert cs_plugin._looks_like_code_line("if (condition) {")
        assert cs_plugin._looks_like_code_line("// This is a comment")
        
        # Non-code lines
        assert not cs_plugin._looks_like_code_line("This is regular text")
        assert not cs_plugin._looks_like_code_line("# This is a markdown header")
        assert not cs_plugin._looks_like_code_line("")
    
    def test_enhance_complexity_notation(self, cs_plugin):
        """Test complexity notation enhancement."""
        content = "The time complexity is O(n) and space complexity is O(1)."
        
        enhanced = cs_plugin._enhance_complexity_notation(content)
        
        assert '**O(n)**' in enhanced
        assert '**O(1)**' in enhanced
    
    def test_process_content(self, cs_plugin):
        """Test complete CS content processing."""
        content = """
        # Data Structures
        
        ## Arrays
        Time complexity: O(1) for access.
        
        ```python
        def binary_search(arr, target):
            left, right = 0, len(arr) - 1
            while left <= right:
                mid = (left + right) // 2
                if arr[mid] == target:
                    return mid
                elif arr[mid] < target:
                    left = mid + 1
                else:
                    right = mid - 1
            return -1
        ```
        
        Algorithm: Binary search reduces search time.
        """
        
        metadata = {'course': 'CS101'}
        result = cs_plugin.process_content(content, metadata)
        
        assert 'content' in result
        assert 'metadata' in result
        assert result['metadata']['code_blocks'] > 0
        assert 'python' in result['metadata']['languages_detected']
        assert '**O(1)**' in result['content']


class TestPluginManager:
    """Test cases for the plugin manager."""
    
    @pytest.fixture
    def plugin_manager(self):
        """Create a plugin manager with test plugin."""
        # Create manager without auto-loading
        manager = PluginManager(plugin_dirs=[])
        
        # Manually add test plugin
        test_plugin = TestPlugin()
        manager.plugins[test_plugin.name] = test_plugin
        
        return manager
    
    def test_init(self, plugin_manager):
        """Test plugin manager initialization."""
        assert isinstance(plugin_manager.plugins, dict)
        assert len(plugin_manager.plugins) >= 1  # At least our test plugin
    
    def test_get_plugin(self, plugin_manager):
        """Test getting plugin by name."""
        plugin = plugin_manager.get_plugin("test_plugin")
        assert plugin is not None
        assert plugin.name == "test_plugin"
        
        # Non-existent plugin
        assert plugin_manager.get_plugin("nonexistent") is None
    
    def test_get_plugins_for_file(self, plugin_manager):
        """Test getting applicable plugins for a file."""
        # File that matches test plugin
        plugins = plugin_manager.get_plugins_for_file(
            Path('test.txt'), 
            {'course': 'TEST101'}
        )
        assert len(plugins) >= 1
        assert plugins[0].name == 'test_plugin'
        
        # File that doesn't match
        plugins = plugin_manager.get_plugins_for_file(
            Path('test.xyz'),  # Unsupported format
            {'course': 'MATH101'}  # Unsupported course
        )
        assert len(plugins) == 0
    
    def test_process_with_plugins(self, plugin_manager):
        """Test processing content with plugins."""
        content = "Hello, world!"
        metadata = {'course': 'TEST101'}
        
        result = plugin_manager.process_with_plugins(
            Path('test.txt'),
            content,
            metadata
        )
        
        assert 'content' in result
        assert 'metadata' in result
        assert 'plugin_results' in result
        
        # Content should be processed by test plugin
        assert result['content'] == "PROCESSED: Hello, world!"
        assert result['metadata']['processed_by'] == 'test_plugin'
    
    def test_enable_disable_plugin(self, plugin_manager):
        """Test enabling and disabling plugins."""
        # Disable plugin
        plugin_manager.disable_plugin("test_plugin")
        plugin = plugin_manager.get_plugin("test_plugin")
        assert not plugin.enabled
        
        # Enable plugin
        plugin_manager.enable_plugin("test_plugin")
        plugin = plugin_manager.get_plugin("test_plugin")
        assert plugin.enabled
    
    def test_list_plugins(self, plugin_manager):
        """Test listing all plugins."""
        plugin_list = plugin_manager.list_plugins()
        
        assert len(plugin_list) >= 1
        plugin_info = plugin_list[0]
        assert 'name' in plugin_info
        assert 'version' in plugin_info
        assert 'enabled' in plugin_info