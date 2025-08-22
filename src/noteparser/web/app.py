"""Flask web application for note browsing dashboard."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Optional

from flask import Flask, jsonify, render_template, request

from noteparser.core import NoteParser
from noteparser.integration.ai_services import AIServicesIntegration
from noteparser.integration.org_sync import OrganizationSync
from noteparser.plugins.base import PluginManager

logger = logging.getLogger(__name__)


def create_app(config: Optional[dict[str, Any]] = None) -> Flask:
    """Create and configure the Flask application.

    Args:
        config: Optional configuration dictionary

    Returns:
        Configured Flask application
    """
    app = Flask(__name__)

    # Configuration
    app.config.update(
        {
            "SECRET_KEY": "dev-key-please-change-in-production",
            "DEBUG": True,
            "NOTES_BASE_PATH": str(Path.cwd()),
            "MAX_CONTENT_LENGTH": 16 * 1024 * 1024,  # 16MB max file size
        },
    )

    if config:
        app.config.update(config)

    # Initialize components
    enable_ai = config.get("AI_ENABLED", True) if config else True
    app.parser = NoteParser(enable_ai=enable_ai)
    app.org_sync = OrganizationSync()
    app.plugin_manager = PluginManager()

    # Initialize AI services if enabled
    app.ai_integration = None
    if enable_ai:
        try:
            app.ai_integration = AIServicesIntegration(config)
        except Exception as e:
            logger.warning(f"AI services not available: {e}")
            app.ai_integration = None

    # Register routes
    register_routes(app)

    return app


def register_routes(app: Flask):
    """Register all routes for the application.

    Args:
        app: Flask application instance
    """

    @app.route("/")
    def index():
        """Main dashboard page."""
        try:
            # Load organization index
            index_path = Path(".noteparser-index.json")
            if index_path.exists():
                with open(index_path) as f:
                    org_index = json.load(f)
            else:
                org_index = app.org_sync.generate_index()

            return render_template(
                "dashboard.html",
                index=org_index,
                repositories=list(app.org_sync.repositories.keys()),
            )
        except Exception as e:
            logger.exception(f"Dashboard error: {e}")
            return render_template("error.html", error=str(e)), 500

    @app.route("/browse/<repo_name>")
    def browse_repository(repo_name: str):
        """Browse files in a specific repository."""
        try:
            if repo_name not in app.org_sync.repositories:
                return (
                    render_template("error.html", error=f"Repository '{repo_name}' not found"),
                    404,
                )

            repo_config = app.org_sync.repositories[repo_name]
            files = app.org_sync._scan_repository_files(repo_config.path)

            return render_template(
                "repository.html",
                repo_name=repo_name,
                repo_config=repo_config,
                files=files,
            )
        except Exception as e:
            logger.exception(f"Repository browse error: {e}")
            return render_template("error.html", error=str(e)), 500

    @app.route("/view/<path:file_path>")
    def view_file(file_path: str):
        """View a specific file."""
        try:
            full_path = Path(app.config["NOTES_BASE_PATH"]) / file_path

            if not full_path.exists():
                return render_template("error.html", error=f"File '{file_path}' not found"), 404

            # Read file content
            if full_path.suffix.lower() in [".md", ".txt"]:
                with open(full_path, encoding="utf-8") as f:
                    content = f.read()

                return render_template(
                    "file_viewer.html",
                    file_path=file_path,
                    content=content,
                    file_type="markdown",
                )
            # For other file types, show file info
            file_info = {
                "name": full_path.name,
                "size": full_path.stat().st_size,
                "modified": full_path.stat().st_mtime,
                "type": full_path.suffix,
            }

            return render_template("file_info.html", file_path=file_path, file_info=file_info)
        except Exception as e:
            logger.exception(f"File view error: {e}")
            return render_template("error.html", error=str(e)), 500

    @app.route("/parse", methods=["GET", "POST"])
    def parse_file():
        """Parse a new file."""
        if request.method == "GET":
            return render_template(
                "parse.html",
                supported_formats=list(app.parser.SUPPORTED_FORMATS),
                plugins=app.plugin_manager.list_plugins(),
            )

        try:
            # Handle file upload
            if "file" not in request.files:
                return jsonify({"error": "No file uploaded"}), 400

            file = request.files["file"]
            if file.filename == "":
                return jsonify({"error": "No file selected"}), 400

            # Save uploaded file
            upload_dir = Path("uploads")
            upload_dir.mkdir(exist_ok=True)

            file_path = upload_dir / file.filename
            file.save(file_path)

            # Parse options
            output_formats = request.form.getlist("formats")
            if not output_formats:
                output_formats = ["markdown"]

            # Parse file
            results = {}
            for format_type in output_formats:
                if format_type == "markdown":
                    result = app.parser.parse_to_markdown(file_path)
                elif format_type == "latex":
                    result = app.parser.parse_to_latex(file_path)
                else:
                    continue

                results[format_type] = result

            return jsonify({"success": True, "file_path": str(file_path), "results": results})

        except Exception as e:
            logger.exception(f"Parse error: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/search")
    def search():
        """Search across all notes."""
        query = request.args.get("q", "").strip()
        if not query:
            return jsonify({"results": []})

        try:
            results = []

            # Load index
            index_path = Path(".noteparser-index.json")
            if index_path.exists():
                with open(index_path) as f:
                    org_index = json.load(f)

                # Simple search through file metadata
                for file_info in org_index.get("files", []):
                    file_path = Path(file_info["path"])

                    # Search in filename and course/topic
                    searchable_text = " ".join(
                        [file_path.name, file_info.get("course", ""), file_info.get("topic", "")],
                    ).lower()

                    if query.lower() in searchable_text:
                        results.append(
                            {
                                "path": file_info["path"],
                                "repository": file_info["repository"],
                                "course": file_info.get("course"),
                                "topic": file_info.get("topic"),
                                "format": file_info["format"],
                            },
                        )

            return jsonify({"results": results[:20]})  # Limit results

        except Exception as e:
            logger.exception(f"Search error: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/plugins")
    def list_plugins():
        """List all available plugins."""
        return jsonify({"plugins": app.plugin_manager.list_plugins()})

    @app.route("/api/plugins/<plugin_name>/toggle", methods=["POST"])
    def toggle_plugin(plugin_name: str):
        """Enable or disable a plugin."""
        try:
            action = request.json.get("action")  # 'enable' or 'disable'

            if action == "enable":
                app.plugin_manager.enable_plugin(plugin_name)
            elif action == "disable":
                app.plugin_manager.disable_plugin(plugin_name)
            else:
                return jsonify({"error": "Invalid action"}), 400

            return jsonify({"success": True, "action": action})

        except Exception as e:
            logger.exception(f"Plugin toggle error: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/sync", methods=["POST"])
    def sync_repositories():
        """Sync parsed notes to target repository."""
        try:
            data = request.json
            source_files = [Path(f) for f in data.get("files", [])]
            target_repo = data.get("target_repo", "study-notes")
            course = data.get("course")

            result = app.org_sync.sync_parsed_notes(
                source_files=source_files,
                target_repo=target_repo,
                course=course,
            )

            return jsonify(result)

        except Exception as e:
            logger.exception(f"Sync error: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/index/refresh", methods=["POST"])
    def refresh_index():
        """Refresh the organization index."""
        try:
            index = app.org_sync.generate_index()
            return jsonify(index)
        except Exception as e:
            logger.exception(f"Index refresh error: {e}")
            return jsonify({"error": str(e)}), 500

    # AI-powered routes
    @app.route("/ai")
    def ai_dashboard():
        """AI features dashboard."""
        if not app.ai_integration:
            return (
                render_template(
                    "error.html",
                    error="AI services not available. Please ensure noteparser-ai-services is running.",
                ),
                503,
            )

        return render_template("ai_dashboard.html")

    @app.route("/api/ai/parse", methods=["POST"])
    def ai_parse_file():
        """Parse file with AI enhancement."""
        if not app.ai_integration:
            return jsonify({"error": "AI services not available"}), 503

        try:
            # Handle file upload
            if "file" not in request.files:
                return jsonify({"error": "No file uploaded"}), 400

            file = request.files["file"]
            if file.filename == "":
                return jsonify({"error": "No file selected"}), 400

            # Save uploaded file
            upload_dir = Path("uploads")
            upload_dir.mkdir(exist_ok=True)

            file_path = upload_dir / file.filename
            file.save(file_path)

            # Parse with AI enhancement
            async def parse_with_ai():
                return await app.parser.parse_to_markdown_with_ai(
                    file_path,
                    extract_metadata=True,
                    preserve_formatting=True,
                )

            result = asyncio.run(parse_with_ai())

            return jsonify(
                {
                    "success": True,
                    "file_path": str(file_path),
                    "content": result["content"],
                    "metadata": result.get("metadata", {}),
                    "ai_processing": result.get("ai_processing", {}),
                },
            )

        except Exception as e:
            logger.exception(f"AI parse error: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/ai/query", methods=["POST"])
    def ai_query():
        """Query the AI knowledge base."""
        if not app.ai_integration:
            return jsonify({"error": "AI services not available"}), 503

        try:
            data = request.json
            query = data.get("query", "").strip()
            filters = data.get("filters", {})

            if not query:
                return jsonify({"error": "Query is required"}), 400

            async def run_query():
                return await app.parser.query_knowledge(query, filters)

            result = asyncio.run(run_query())

            if "error" in result:
                return jsonify({"error": result["error"]}), 500

            return jsonify(result)

        except Exception as e:
            logger.exception(f"AI query error: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/ai/analyze", methods=["POST"])
    def ai_analyze_text():
        """Analyze text content with AI."""
        if not app.ai_integration:
            return jsonify({"error": "AI services not available"}), 503

        try:
            data = request.json
            content = data.get("content", "").strip()

            if not content:
                return jsonify({"error": "Content is required"}), 400

            async def analyze():
                await app.ai_integration.initialize()
                return await app.ai_integration.process_document(
                    {
                        "content": content,
                        "metadata": {
                            "title": data.get("title", "Web Analysis"),
                            "source": "web_interface",
                        },
                    },
                )

            result = asyncio.run(analyze())
            return jsonify(result)

        except Exception as e:
            logger.exception(f"AI analysis error: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/ai/health")
    def ai_health():
        """Check AI services health."""
        if not app.ai_integration:
            return jsonify({"status": "disabled", "message": "AI services not configured"})

        try:
            from noteparser.integration.service_client import ServiceClientManager

            async def check_health():
                manager = ServiceClientManager()
                return await manager.health_check_all()

            health_status = asyncio.run(check_health())

            # Determine overall status
            all_healthy = all(
                status.get("status") == "healthy"
                for status in health_status.values()
                if status.get("status") != "disabled"
            )

            return jsonify(
                {
                    "status": "healthy" if all_healthy else "unhealthy",
                    "services": health_status,
                    "timestamp": json.dumps({"timestamp": "now"}),  # JSON serializable
                },
            )

        except Exception as e:
            logger.exception(f"AI health check error: {e}")
            return jsonify({"status": "error", "error": str(e)}), 500

    @app.route("/api/ai/search", methods=["POST"])
    def ai_search():
        """Enhanced AI-powered search."""
        if not app.ai_integration:
            # Fallback to regular search
            return search()

        try:
            data = request.json
            query = data.get("query", "").strip()
            filters = data.get("filters", {})
            limit = min(data.get("limit", 10), 50)  # Max 50 results

            if not query:
                return jsonify({"error": "Query is required"}), 400

            async def enhanced_search():
                # Try AI search first
                try:
                    await app.ai_integration.initialize()
                    ai_results = await app.ai_integration.query_knowledge(query, filters)

                    if "documents" in ai_results:
                        return {
                            "results": ai_results["documents"][:limit],
                            "answer": ai_results.get("answer"),
                            "search_type": "ai_enhanced",
                        }
                except Exception as e:
                    logger.warning(f"AI search failed, falling back to regular search: {e}")

                # Fallback to regular search
                regular_results = []
                index_path = Path(".noteparser-index.json")
                if index_path.exists():
                    with open(index_path) as f:
                        org_index = json.load(f)

                    for file_info in org_index.get("files", []):
                        file_path = Path(file_info["path"])
                        searchable_text = " ".join(
                            [
                                file_path.name,
                                file_info.get("course", ""),
                                file_info.get("topic", ""),
                            ],
                        ).lower()

                        if query.lower() in searchable_text:
                            regular_results.append(
                                {
                                    "path": file_info["path"],
                                    "repository": file_info["repository"],
                                    "course": file_info.get("course"),
                                    "topic": file_info.get("topic"),
                                    "format": file_info["format"],
                                },
                            )

                return {"results": regular_results[:limit], "search_type": "regular"}

            result = asyncio.run(enhanced_search())
            return jsonify(result)

        except Exception as e:
            logger.exception(f"Enhanced search error: {e}")
            return jsonify({"error": str(e)}), 500

    @app.errorhandler(404)
    def not_found(error):
        return render_template("error.html", error="Page not found"), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template("error.html", error="Internal server error"), 500
