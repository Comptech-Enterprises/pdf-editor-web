from flask import Flask, render_template, send_from_directory, jsonify, request
from config import Config
from api.routes import api
import os

app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

# Register API blueprint
app.register_blueprint(api, url_prefix='/api')


# JSON error handlers for API routes
@app.errorhandler(413)
def request_entity_too_large(error):
    if request.path.startswith('/api/'):
        return jsonify({"error": "File too large. Maximum size is 50MB."}), 413
    return error

@app.errorhandler(500)
def internal_server_error(error):
    if request.path.startswith('/api/'):
        return jsonify({"error": "Internal server error"}), 500
    return error

@app.errorhandler(404)
def not_found(error):
    if request.path.startswith('/api/'):
        return jsonify({"error": "Not found"}), 404
    return error

@app.route('/')
def index():
    """Landing page with upload form."""
    return render_template('index.html')

@app.route('/editor/<file_id>')
def editor(file_id):
    """PDF editor page."""
    return render_template('editor.html', file_id=file_id)

@app.route('/static/js/lib/<path:filename>')
def serve_lib(filename):
    """Serve library files."""
    return send_from_directory('static/js/lib', filename)

if __name__ == '__main__':
    import os
    debug = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
    port = int(os.environ.get('PORT', 5000))

    print("Starting PDF Editor Web App...")
    print(f"Open http://localhost:{port} in your browser")
    app.run(debug=debug, host='0.0.0.0', port=port)
