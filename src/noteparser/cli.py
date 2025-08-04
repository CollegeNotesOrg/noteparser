"""Command-line interface for noteparser."""

import click
import json
from pathlib import Path
from typing import List, Optional
import logging

from .core import NoteParser
from .integration.org_sync import OrganizationSync
from .plugins.base import PluginManager
from .web.app import create_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def main(ctx, verbose):
    """NoteParser - Convert documents to Markdown and LaTeX for academic use."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose


@main.command()
@click.argument('input_file', type=click.Path(exists=True, path_type=Path))
@click.option('--output', '-o', type=click.Path(path_type=Path), help='Output file path')
@click.option('--format', '-f', 'output_format', 
              type=click.Choice(['markdown', 'latex']), 
              default='markdown', help='Output format')
@click.option('--metadata/--no-metadata', default=True, help='Extract metadata')
@click.option('--preserve-formatting/--no-preserve-formatting', default=True, 
              help='Preserve academic formatting')
@click.pass_context
def parse(ctx, input_file: Path, output: Optional[Path], output_format: str, 
          metadata: bool, preserve_formatting: bool):
    """Parse a single document to the specified format."""
    try:
        parser = NoteParser()
        
        if output_format == 'markdown':
            result = parser.parse_to_markdown(
                input_file, 
                extract_metadata=metadata,
                preserve_formatting=preserve_formatting
            )
        else:  # latex
            result = parser.parse_to_latex(
                input_file,
                extract_metadata=metadata
            )
        
        # Determine output path
        if not output:
            suffix = '.md' if output_format == 'markdown' else '.tex'
            output = input_file.with_suffix(suffix)
        
        # Write output
        with open(output, 'w', encoding='utf-8') as f:
            f.write(result['content'])
        
        click.echo(f"✓ Parsed {input_file} to {output}")
        
        if ctx.obj['verbose'] and metadata and 'metadata' in result:
            click.echo("Metadata:")
            for key, value in result['metadata'].items():
                click.echo(f"  {key}: {value}")
                
    except Exception as e:
        click.echo(f"✗ Error parsing {input_file}: {e}", err=True)
        raise click.Abort()


@main.command()
@click.argument('input_dir', type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option('--output-dir', '-o', type=click.Path(path_type=Path), help='Output directory')
@click.option('--format', '-f', 'output_format',
              type=click.Choice(['markdown', 'latex']), 
              default='markdown', help='Output format')
@click.option('--recursive/--no-recursive', default=True, help='Search recursively')
@click.option('--pattern', '-p', help='File pattern to match')
@click.pass_context
def batch(ctx, input_dir: Path, output_dir: Optional[Path], output_format: str,
          recursive: bool, pattern: Optional[str]):
    """Parse multiple documents in a directory."""
    try:
        parser = NoteParser()
        
        results = parser.parse_batch(
            directory=input_dir,
            output_format=output_format,
            recursive=recursive,
            pattern=pattern
        )
        
        # Create output directory
        if not output_dir:
            output_dir = input_dir / 'parsed'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        success_count = 0
        error_count = 0
        
        for file_path, result in results.items():
            file_path_obj = Path(file_path)
            
            if 'error' in result:
                click.echo(f"✗ Error parsing {file_path}: {result['error']}", err=True)
                error_count += 1
                continue
            
            # Write output file
            suffix = '.md' if output_format == 'markdown' else '.tex'
            output_file = output_dir / f"{file_path_obj.stem}{suffix}"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result['content'])
            
            click.echo(f"✓ Parsed {file_path_obj.name} to {output_file}")
            success_count += 1
        
        click.echo(f"\nCompleted: {success_count} successful, {error_count} errors")
        
    except Exception as e:
        click.echo(f"✗ Batch processing error: {e}", err=True)
        raise click.Abort()


@main.command()
@click.option('--target-repo', '-t', default='study-notes', help='Target repository name')
@click.option('--course', '-c', help='Course identifier')
@click.argument('files', nargs=-1, type=click.Path(exists=True, path_type=Path))
def sync(target_repo: str, course: Optional[str], files: List[Path]):
    """Sync parsed notes to target repository."""
    try:
        org_sync = OrganizationSync()
        
        if not files:
            click.echo("No files specified for syncing", err=True)
            raise click.Abort()
        
        result = org_sync.sync_parsed_notes(
            source_files=list(files),
            target_repo=target_repo,
            course=course
        )
        
        click.echo(f"✓ Synced {len(result['synced_files'])} files to {target_repo}")
        
        if result['errors']:
            click.echo("Errors:")
            for error in result['errors']:
                click.echo(f"  • {error}", err=True)
                
    except Exception as e:
        click.echo(f"✗ Sync error: {e}", err=True)
        raise click.Abort()


@main.command()
@click.option('--format', '-f', type=click.Choice(['json', 'yaml']), 
              default='json', help='Output format')
def index(format: str):
    """Generate organization-wide index of notes."""
    try:
        org_sync = OrganizationSync()
        index_data = org_sync.generate_index()
        
        if format == 'json':
            click.echo(json.dumps(index_data, indent=2, default=str))
        else:  # yaml
            import yaml
            click.echo(yaml.dump(index_data, default_flow_style=False))
            
    except Exception as e:
        click.echo(f"✗ Index generation error: {e}", err=True)
        raise click.Abort()


@main.command()
def plugins():
    """List available plugins."""
    try:
        plugin_manager = PluginManager()
        plugin_list = plugin_manager.list_plugins()
        
        if not plugin_list:
            click.echo("No plugins loaded")
            return
        
        click.echo("Available Plugins:")
        click.echo("-" * 50)
        
        for plugin_info in plugin_list:
            status = "✓ Enabled" if plugin_info['enabled'] else "✗ Disabled"
            click.echo(f"{plugin_info['name']} v{plugin_info['version']} - {status}")
            click.echo(f"  {plugin_info['description']}")
            if plugin_info['course_types']:
                click.echo(f"  Course types: {', '.join(plugin_info['course_types'])}")
            if plugin_info['supported_formats']:
                click.echo(f"  Formats: {', '.join(plugin_info['supported_formats'])}")
            click.echo()
            
    except Exception as e:
        click.echo(f"✗ Plugin listing error: {e}", err=True)
        raise click.Abort()


@main.command()
@click.option('--host', '-h', default='127.0.0.1', help='Host to bind to')
@click.option('--port', '-p', default=5000, help='Port to bind to')
@click.option('--debug/--no-debug', default=True, help='Enable debug mode')
def web(host: str, port: int, debug: bool):
    """Start the web dashboard."""
    try:
        app = create_app({'DEBUG': debug})
        click.echo(f"Starting web dashboard at http://{host}:{port}")
        app.run(host=host, port=port, debug=debug)
        
    except Exception as e:
        click.echo(f"✗ Web server error: {e}", err=True)
        raise click.Abort()


@main.command()
@click.option('--config-path', '-c', type=click.Path(path_type=Path), 
              help='Path to configuration file')
def init(config_path: Optional[Path]):
    """Initialize noteparser configuration for current directory."""
    try:
        # Create default configuration
        if not config_path:
            config_path = Path('.noteparser-org.yml')
        
        # Initialize OrganizationSync to create default config
        org_sync = OrganizationSync(config_path)
        
        # Create directories
        for dir_name in ['input', 'output', 'plugins']:
            Path(dir_name).mkdir(exist_ok=True)
        
        click.echo(f"✓ Initialized noteparser configuration at {config_path}")
        click.echo("Created directories: input/, output/, plugins/")
        click.echo("You can now:")
        click.echo("  • Place documents in input/ directory")
        click.echo("  • Run 'noteparser batch input/' to parse them")
        click.echo("  • Start web dashboard with 'noteparser web'")
        
    except Exception as e:
        click.echo(f"✗ Initialization error: {e}", err=True)
        raise click.Abort()


if __name__ == '__main__':
    main()