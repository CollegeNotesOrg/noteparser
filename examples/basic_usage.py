"""
Basic usage examples for NoteParser.

This script demonstrates the core functionality of NoteParser
for converting academic documents to Markdown and LaTeX.
"""

from pathlib import Path
from noteparser import NoteParser
from noteparser.integration import OrganizationSync
from noteparser.plugins import PluginManager


def example_single_document():
    """Example: Parse a single document to Markdown."""
    print("🔄 Parsing single document to Markdown...")
    
    parser = NoteParser()
    
    # Create sample input file (you would use your actual file)
    sample_file = Path("sample_lecture.txt")
    sample_content = """
    # Introduction to Data Structures
    
    ## Arrays
    Arrays are fundamental data structures that store elements in contiguous memory.
    
    ### Time Complexity
    - Access: O(1)
    - Search: O(n)
    - Insertion: O(n)
    
    ```python
    # Example array operations
    arr = [1, 2, 3, 4, 5]
    print(arr[0])  # Access first element
    arr.append(6)  # Add element
    ```
    
    ## Mathematical Properties
    The time complexity for searching in an unsorted array is $O(n)$, while
    for a sorted array using binary search it becomes $O(\\log n)$.
    
    **Theorem**: Binary search reduces search complexity from linear to logarithmic.
    **Proof**: At each step, we eliminate half of the remaining elements...
    """
    
    with open(sample_file, 'w') as f:
        f.write(sample_content)
    
    try:
        # Parse to Markdown with metadata extraction
        result = parser.parse_to_markdown(
            sample_file,
            extract_metadata=True,
            preserve_formatting=True
        )
        
        print(f"✅ Successfully parsed {sample_file}")
        print(f"📄 Content length: {len(result['content'])} characters")
        print(f"📋 Metadata: {result.get('metadata', {})}")
        
        # Save output
        output_file = Path("output_markdown.md")
        with open(output_file, 'w') as f:
            f.write(result['content'])
        print(f"💾 Saved to {output_file}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Clean up
        if sample_file.exists():
            sample_file.unlink()


def example_latex_conversion():
    """Example: Convert document to LaTeX format."""
    print("\n🔄 Converting document to LaTeX...")
    
    parser = NoteParser()
    
    # Create sample markdown content
    sample_file = Path("sample_notes.md")
    sample_content = """
    ---
    title: "Linear Algebra Fundamentals"
    author: "Prof. Smith"
    course: "MATH201"
    date: "2024-03-15"
    ---
    
    # Linear Algebra Fundamentals
    
    ## Vector Spaces
    
    A **vector space** V over a field F is a set equipped with two operations:
    - Vector addition: $v + w \\in V$ for all $v, w \\in V$
    - Scalar multiplication: $\\alpha v \\in V$ for all $\\alpha \\in F, v \\in V$
    
    ### Properties
    
    1. **Commutativity**: $v + w = w + v$
    2. **Associativity**: $(u + v) + w = u + (v + w)$
    3. **Identity**: There exists $0 \\in V$ such that $v + 0 = v$
    
    ## Linear Transformations
    
    ```python
    import numpy as np
    
    # Define a 2x2 transformation matrix
    T = np.array([[2, 1], 
                  [1, 3]])
    
    # Apply to vector
    v = np.array([1, 2])
    result = T @ v
    print(f"T(v) = {result}")
    ```
    
    The determinant of this transformation is:
    $$\\det(T) = 2 \\cdot 3 - 1 \\cdot 1 = 5$$
    """
    
    with open(sample_file, 'w') as f:
        f.write(sample_content)
    
    try:
        # Convert to LaTeX
        result = parser.parse_to_latex(
            sample_file,
            template='article',
            extract_metadata=True
        )
        
        print(f"✅ Successfully converted {sample_file} to LaTeX")
        print(f"📄 LaTeX length: {len(result['content'])} characters")
        
        # Save LaTeX output
        output_file = Path("output_document.tex")
        with open(output_file, 'w') as f:
            f.write(result['content'])
        print(f"💾 Saved LaTeX to {output_file}")
        
        # Show LaTeX preview
        print("\\n📜 LaTeX Preview (first 500 chars):")
        print(result['content'][:500] + "...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if sample_file.exists():
            sample_file.unlink()


def example_batch_processing():
    """Example: Batch process multiple documents."""
    print("\\n🔄 Batch processing multiple documents...")
    
    parser = NoteParser()
    
    # Create sample directory with multiple files
    input_dir = Path("sample_input")
    input_dir.mkdir(exist_ok=True)
    
    # Create sample files
    sample_files = {
        "CS101_Lecture1.md": """
        # Introduction to Programming
        
        ## Variables and Data Types
        
        ```python
        # Basic data types
        name = "Alice"      # string
        age = 20           # integer
        height = 5.6       # float
        is_student = True  # boolean
        ```
        """,
        
        "MATH201_Notes.md": """
        # Calculus Fundamentals
        
        ## Derivatives
        
        The derivative of $f(x) = x^2$ is:
        $$f'(x) = 2x$$
        
        **Chain Rule**: $(f \\circ g)'(x) = f'(g(x)) \\cdot g'(x)$
        """,
        
        "PHYS301_Lab.md": """
        # Physics Lab: Pendulum Experiment
        
        ## Procedure
        
        1. Measure pendulum length: $L = 1.2$ m
        2. Record 10 oscillations
        3. Calculate period: $T = 2\\pi\\sqrt{\\frac{L}{g}}$
        
        ## Results
        
        | Trial | Time (s) | Period (s) |
        |-------|----------|------------|
        | 1     | 22.1     | 2.21       |
        | 2     | 21.9     | 2.19       |
        | 3     | 22.3     | 2.23       |
        """
    }
    
    # Write sample files
    for filename, content in sample_files.items():
        file_path = input_dir / filename
        with open(file_path, 'w') as f:
            f.write(content.strip())
    
    try:
        # Batch process all files
        results = parser.parse_batch(
            directory=input_dir,
            output_format="markdown",
            recursive=False
        )
        
        print(f"✅ Processed {len(results)} files")
        
        # Create output directory
        output_dir = Path("batch_output")
        output_dir.mkdir(exist_ok=True)
        
        # Save processed files
        for file_path, result in results.items():
            if 'error' in result:
                print(f"❌ Error processing {file_path}: {result['error']}")
                continue
                
            filename = Path(file_path).name
            output_file = output_dir / f"processed_{filename}"
            
            with open(output_file, 'w') as f:
                f.write(result['content'])
            
            print(f"💾 Saved processed {filename}")
            
            # Show metadata if available
            if 'metadata' in result:
                metadata = result['metadata']
                course = metadata.get('course', 'Unknown')
                print(f"   📋 Course: {course}, Words: {metadata.get('word_count', 0)}")
    
    except Exception as e:
        print(f"❌ Batch processing error: {e}")
    
    finally:
        # Clean up input directory
        import shutil
        if input_dir.exists():
            shutil.rmtree(input_dir)


def example_plugin_usage():
    """Example: Using plugins for enhanced processing."""
    print("\\n🔌 Demonstrating plugin usage...")
    
    # Initialize plugin manager
    plugin_manager = PluginManager()
    
    print("Available plugins:")
    plugins = plugin_manager.list_plugins()
    for plugin in plugins:
        status = "✅ Enabled" if plugin['enabled'] else "❌ Disabled"
        print(f"  - {plugin['name']} v{plugin['version']} - {status}")
        print(f"    {plugin['description']}")
        print(f"    Course types: {', '.join(plugin['course_types'])}")
        print()
    
    # Example: Process a math-heavy document
    math_content = """
    # Advanced Calculus
    
    ## Theorem: Fundamental Theorem of Calculus
    If $f$ is continuous on $[a, b]$ and $F$ is an antiderivative of $f$, then:
    $$\\int_a^b f(x) dx = F(b) - F(a)$$
    
    **Proof**: The proof follows from the definition of the derivative...
    
    ## Example Calculation
    Find $\\int_0^1 x^2 dx$:
    
    Using the antiderivative $F(x) = \\frac{x^3}{3}$:
    $$\\int_0^1 x^2 dx = F(1) - F(0) = \\frac{1}{3} - 0 = \\frac{1}{3}$$
    """
    
    # Create temporary file
    temp_file = Path("temp_math.md")
    with open(temp_file, 'w') as f:
        f.write(math_content)
    
    try:
        # Process with plugins
        metadata = {'course': 'MATH301', 'topic': 'Calculus'}
        result = plugin_manager.process_with_plugins(
            file_path=temp_file,
            content=math_content,
            metadata=metadata
        )
        
        print("🔄 Processed content with plugins:")
        print(f"📄 Content length: {len(result['content'])} characters")
        print(f"📋 Updated metadata: {result['metadata']}")
        print(f"🔌 Plugin results: {list(result['plugin_results'].keys())}")
        
        # Show enhanced content preview
        print("\\n📜 Enhanced content preview:")
        lines = result['content'].split('\\n')[:10]
        for line in lines:
            print(f"  {line}")
        if len(result['content'].split('\\n')) > 10:
            print("  ...")
    
    except Exception as e:
        print(f"❌ Plugin processing error: {e}")
    
    finally:
        if temp_file.exists():
            temp_file.unlink()


def example_organization_sync():
    """Example: Organization-wide synchronization."""
    print("\\n🔗 Demonstrating organization synchronization...")
    
    try:
        # Initialize organization sync
        org_sync = OrganizationSync()
        
        print("Organization repositories:")
        for repo_name, repo_config in org_sync.repositories.items():
            print(f"  - {repo_name}: {repo_config.type} ({repo_config.path})")
        
        # Generate organization index
        print("\\n📊 Generating organization index...")
        index = org_sync.generate_index()
        
        print(f"📈 Index statistics:")
        print(f"  - Total files: {index['metadata']['total_files']}")
        print(f"  - Repositories: {len(index['metadata']['repositories'])}")
        print(f"  - Courses: {len(index['courses'])}")
        print(f"  - Topics: {len(index['topics'])}")
        
        # Show courses
        if index['courses']:
            print("\\n📚 Courses found:")
            for course, files in index['courses'].items():
                print(f"  - {course}: {len(files)} files")
        
    except Exception as e:
        print(f"❌ Organization sync error: {e}")


if __name__ == "__main__":
    print("🚀 NoteParser Examples")
    print("=" * 50)
    
    # Run all examples
    example_single_document()
    example_latex_conversion()
    example_batch_processing()
    example_plugin_usage()
    example_organization_sync()
    
    print("\\n✅ All examples completed!")
    print("\\nNext steps:")
    print("  1. Try parsing your own documents")
    print("  2. Set up organization sync with your repositories")
    print("  3. Create custom plugins for your courses")
    print("  4. Start the web dashboard: noteparser web")