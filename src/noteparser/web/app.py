"""Flask web application for note browsing dashboard."""

from flask import Flask, render_template, request, jsonify, send_file
from pathlib import Path
import json
from typing import Dict, Any, List
import logging

from ..core import NoteParser
from ..integration.org_sync import OrganizationSync
from ..plugins.base import PluginManager

logger = logging.getLogger(__name__)


def create_app(config: Dict[str, Any] = None) -> Flask:
    """Create and configure the Flask application.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Configured Flask application
    """
    app = Flask(__name__)
    
    # Configuration
    app.config.update({
        'SECRET_KEY': 'dev-key-please-change-in-production',
        'DEBUG': True,
        'NOTES_BASE_PATH': str(Path.cwd()),
        'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB max file size
    })
    
    if config:
        app.config.update(config)
        
    # Initialize components
    app.parser = NoteParser()
    app.org_sync = OrganizationSync()
    app.plugin_manager = PluginManager()
    
    # Register routes
    register_routes(app)
    
    return app


def register_routes(app: Flask):
    """Register all routes for the application.
    
    Args:
        app: Flask application instance
    """
    
    @app.route('/')
    def index():
        """Main dashboard page."""
        try:
            # Load organization index
            index_path = Path('.noteparser-index.json')
            if index_path.exists():
                with open(index_path, 'r') as f:
                    org_index = json.load(f)
            else:
                org_index = app.org_sync.generate_index()
                
            return render_template('dashboard.html', 
                                 index=org_index,
                                 repositories=list(app.org_sync.repositories.keys()))
        except Exception as e:
            logger.error(f"Dashboard error: {e}")
            return render_template('error.html', error=str(e)), 500
            
    @app.route('/browse/<repo_name>')
    def browse_repository(repo_name: str):
        """Browse files in a specific repository."""
        try:
            if repo_name not in app.org_sync.repositories:
                return render_template('error.html', 
                                     error=f"Repository '{repo_name}' not found"), 404
                
            repo_config = app.org_sync.repositories[repo_name]
            files = app.org_sync._scan_repository_files(repo_config.path)
            
            return render_template('repository.html',
                                 repo_name=repo_name,
                                 repo_config=repo_config,
                                 files=files)
        except Exception as e:
            logger.error(f"Repository browse error: {e}")
            return render_template('error.html', error=str(e)), 500
            
    @app.route('/view/<path:file_path>')
    def view_file(file_path: str):
        """View a specific file."""
        try:
            full_path = Path(app.config['NOTES_BASE_PATH']) / file_path
            
            if not full_path.exists():
                return render_template('error.html', 
                                     error=f"File '{file_path}' not found"), 404
                
            # Read file content
            if full_path.suffix.lower() in ['.md', '.txt']:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                return render_template('file_viewer.html',
                                     file_path=file_path,
                                     content=content,
                                     file_type='markdown')
            else:
                # For other file types, show file info
                file_info = {
                    'name': full_path.name,
                    'size': full_path.stat().st_size,
                    'modified': full_path.stat().st_mtime,
                    'type': full_path.suffix
                }
                
                return render_template('file_info.html',
                                     file_path=file_path,
                                     file_info=file_info)
        except Exception as e:
            logger.error(f"File view error: {e}")
            return render_template('error.html', error=str(e)), 500
            
    @app.route('/parse', methods=['GET', 'POST'])
    def parse_file():
        """Parse a new file."""
        if request.method == 'GET':
            return render_template('parse.html',
                                 supported_formats=list(app.parser.SUPPORTED_FORMATS),
                                 plugins=app.plugin_manager.list_plugins())
                                 
        try:
            # Handle file upload
            if 'file' not in request.files:
                return jsonify({'error': 'No file uploaded'}), 400
                
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
                
            # Save uploaded file
            upload_dir = Path('uploads')
            upload_dir.mkdir(exist_ok=True)
            
            file_path = upload_dir / file.filename
            file.save(file_path)
            
            # Parse options
            output_formats = request.form.getlist('formats')
            if not output_formats:
                output_formats = ['markdown']
                
            # Parse file
            results = {}
            for format_type in output_formats:
                if format_type == 'markdown':
                    result = app.parser.parse_to_markdown(file_path)
                elif format_type == 'latex':
                    result = app.parser.parse_to_latex(file_path)
                else:
                    continue
                    
                results[format_type] = result
                
            return jsonify({
                'success': True,
                'file_path': str(file_path),
                'results': results
            })
            
        except Exception as e:
            logger.error(f"Parse error: {e}")
            return jsonify({'error': str(e)}), 500
            
    @app.route('/api/search')
    def search():
        """Search across all notes."""
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'results': []})
            
        try:
            results = []
            
            # Load index
            index_path = Path('.noteparser-index.json')
            if index_path.exists():
                with open(index_path, 'r') as f:
                    org_index = json.load(f)
                    
                # Simple search through file metadata
                for file_info in org_index.get('files', []):
                    file_path = Path(file_info['path'])
                    
                    # Search in filename and course/topic
                    searchable_text = ' '.join([
                        file_path.name,
                        file_info.get('course', ''),
                        file_info.get('topic', '')
                    ]).lower()
                    
                    if query.lower() in searchable_text:
                        results.append({
                            'path': file_info['path'],
                            'repository': file_info['repository'],
                            'course': file_info.get('course'),
                            'topic': file_info.get('topic'),
                            'format': file_info['format']
                        })
                        
            return jsonify({'results': results[:20]})  # Limit results
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return jsonify({'error': str(e)}), 500
            
    @app.route('/api/plugins')
    def list_plugins():
        """List all available plugins."""
        return jsonify({'plugins': app.plugin_manager.list_plugins()})
        
    @app.route('/api/plugins/<plugin_name>/toggle', methods=['POST'])
    def toggle_plugin(plugin_name: str):
        """Enable or disable a plugin."""
        try:
            action = request.json.get('action')  # 'enable' or 'disable'
            
            if action == 'enable':
                app.plugin_manager.enable_plugin(plugin_name)
            elif action == 'disable':
                app.plugin_manager.disable_plugin(plugin_name)
            else:
                return jsonify({'error': 'Invalid action'}), 400
                
            return jsonify({'success': True, 'action': action})
            
        except Exception as e:
            logger.error(f"Plugin toggle error: {e}")
            return jsonify({'error': str(e)}), 500
            
    @app.route('/api/sync', methods=['POST'])
    def sync_repositories():
        """Sync parsed notes to target repository."""
        try:
            data = request.json
            source_files = [Path(f) for f in data.get('files', [])]
            target_repo = data.get('target_repo', 'study-notes')
            course = data.get('course')
            
            result = app.org_sync.sync_parsed_notes(
                source_files=source_files,
                target_repo=target_repo,
                course=course
            )
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Sync error: {e}")
            return jsonify({'error': str(e)}), 500
            
    @app.route('/api/index/refresh', methods=['POST'])
    def refresh_index():
        """Refresh the organization index."""
        try:
            index = app.org_sync.generate_index()
            return jsonify(index)
        except Exception as e:
            logger.error(f"Index refresh error: {e}")
            return jsonify({'error': str(e)}), 500
            
    @app.errorhandler(404)
    def not_found(error):
        return render_template('error.html', error='Page not found'), 404
        
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('error.html', error='Internal server error'), 500