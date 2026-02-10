from flask import Flask, render_template, send_from_directory
from config import Config
from api.routes import api
import os

app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

# Register API blueprint
app.register_blueprint(api, url_prefix='/api')

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
