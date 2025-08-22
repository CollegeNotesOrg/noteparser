"""API blueprint for web interface."""

from flask import Blueprint, Response, jsonify

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/health", methods=["GET"])
def health() -> Response:
    """Health check endpoint."""
    return jsonify(
        {
            "status": "healthy",
            "version": "2.1.0",
            "services": {"parser": "available", "ai_integration": "available"},
        },
    )


@api_bp.route("/parse/status/<task_id>", methods=["GET"])
def parse_status(task_id: str) -> Response:
    """Get parsing task status."""
    return jsonify(
        {
            "task_id": task_id,
            "status": "completed",
            "progress": 100,
            "result": "Task completed successfully",
        },
    )


@api_bp.route("/files", methods=["GET"])
def list_files() -> Response:
    """List available files."""
    return jsonify({"files": [], "total": 0, "page": 1, "per_page": 10})


@api_bp.route("/plugins", methods=["GET"])
def list_plugins() -> Response:
    """List available plugins."""
    return jsonify(
        {
            "plugins": [
                {
                    "name": "math_plugin",
                    "type": "course",
                    "description": "Mathematics course processor",
                },
                {
                    "name": "cs_plugin",
                    "type": "course",
                    "description": "Computer Science course processor",
                },
            ],
            "total": 2,
        },
    )


@api_bp.errorhandler(404)
def not_found(error) -> tuple[Response, int]:
    """Handle 404 errors."""
    return jsonify({"error": "Not found"}), 404


@api_bp.errorhandler(500)
def internal_error(error) -> tuple[Response, int]:
    """Handle 500 errors."""
    return jsonify({"error": "Internal server error"}), 500
