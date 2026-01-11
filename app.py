"""
RAG Web Application - Flask API
================================
A beautiful web interface for the RAG system.

Run with: python app.py
Open: http://localhost:5000
"""

import os
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

from rag import RAGPipeline

# ============================================
# Flask App Configuration
# ============================================

app = Flask(__name__, static_folder='static')
CORS(app)

# Upload configuration
UPLOAD_FOLDER = Path(__file__).parent / 'uploads'
UPLOAD_FOLDER.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}

app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ============================================
# Routes
# ============================================

@app.route('/')
def index():
    """Serve the main HTML page."""
    return send_from_directory('static', 'index.html')


@app.route('/api/status')
def status():
    """Check system status and document count."""
    try:
        rag = RAGPipeline()
        # Try to connect to Weaviate
        connected = rag.vector_store.client.is_ready()
        rag.close()
        return jsonify({
            'status': 'connected' if connected else 'disconnected',
            'weaviate': connected
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload and ingestion."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({
            'error': f'File type not allowed. Supported: {", ".join(ALLOWED_EXTENSIONS)}'
        }), 400
    
    try:
        # Save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Ingest into RAG
        rag = RAGPipeline()
        chunks = rag.ingest_document(filepath)
        rag.close()
        
        return jsonify({
            'success': True,
            'filename': filename,
            'chunks': chunks,
            'message': f'Successfully ingested {chunks} chunks from {filename}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/query', methods=['POST'])
def query():
    """Query the RAG system."""
    data = request.get_json()
    
    if not data or 'question' not in data:
        return jsonify({'error': 'No question provided'}), 400
    
    question = data['question'].strip()
    
    if not question:
        return jsonify({'error': 'Question cannot be empty'}), 400
    
    try:
        rag = RAGPipeline()
        answer = rag.query(question)
        rag.close()
        
        return jsonify({
            'success': True,
            'question': question,
            'answer': answer
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/documents')
def list_documents():
    """List uploaded documents."""
    try:
        files = []
        for f in UPLOAD_FOLDER.iterdir():
            if f.is_file() and allowed_file(f.name):
                files.append({
                    'name': f.name,
                    'size': f.stat().st_size,
                    'modified': f.stat().st_mtime
                })
        return jsonify({'documents': files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# Run the app
# ============================================

if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("🚀 RAG Web Application")
    print("=" * 50)
    print("📁 Upload folder:", UPLOAD_FOLDER)
    print("🌐 Open: http://localhost:5000")
    print("=" * 50 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
