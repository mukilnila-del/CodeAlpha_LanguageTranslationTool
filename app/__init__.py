import logging
from flask import Flask, render_template, jsonify
from app.config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

    # Register Blueprints
    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({'success': False, 'error': 'Resource not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

    return app
