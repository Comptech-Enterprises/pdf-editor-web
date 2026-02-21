from flask import Blueprint, request, jsonify, send_file, current_app
from services.storage_service import StorageService
from services.pdf_service import PDFService
from pathlib import Path
import os

api = Blueprint('api', __name__)

def get_storage():
    return StorageService(current_app.config['UPLOAD_FOLDER'])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@api.route('/upload', methods=['POST'])
def upload_pdf():
    """Upload a PDF file."""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    storage = get_storage()
    file_id, metadata = storage.save_upload(file)

    # Get PDF info
    pdf_path = storage.get_pdf_path(file_id)
    pdf_info = PDFService.get_pdf_info(pdf_path)

    return jsonify({
        "success": True,
        "id": file_id,
        "filename": metadata['original_name'],
        "pages": pdf_info['pages'],
        "pageInfo": pdf_info['pageInfo']
    })

@api.route('/pdf/<file_id>/text', methods=['GET'])
def get_text(file_id):
    """Extract text with positions from PDF."""
    storage = get_storage()
    pdf_path = storage.get_original_path(file_id)

    if not pdf_path or not os.path.exists(pdf_path):
        return jsonify({"error": "PDF not found"}), 404

    text_data = PDFService.extract_text_with_positions(pdf_path)

    return jsonify({
        "success": True,
        "documentId": file_id,
        **text_data
    })

@api.route('/pdf/<file_id>/page/<int:page_num>/image', methods=['GET'])
def get_page_image(file_id, page_num):
    """Get PDF page as PNG image."""
    storage = get_storage()
    pdf_path = storage.get_original_path(file_id)

    if not pdf_path or not os.path.exists(pdf_path):
        return jsonify({"error": "PDF not found"}), 404

    scale = float(request.args.get('scale', 1.5))
    img_bytes = PDFService.render_page_to_image(pdf_path, page_num, scale)

    if not img_bytes:
        return jsonify({"error": "Page not found"}), 404

    from io import BytesIO
    return send_file(
        BytesIO(img_bytes),
        mimetype='image/png',
        download_name=f'page_{page_num}.png'
    )

@api.route('/pdf/<file_id>/edit', methods=['POST'])
def apply_edits(file_id):
    """Apply edits to PDF and generate new version."""
    storage = get_storage()
    pdf_path = storage.get_original_path(file_id)

    if not pdf_path or not os.path.exists(pdf_path):
        return jsonify({"error": "PDF not found"}), 404

    data = request.get_json()
    if not data or 'operations' not in data:
        return jsonify({"error": "No operations provided"}), 400

    operations = data['operations']

    # Create output path
    upload_dir = storage.get_upload_dir(file_id)
    output_path = upload_dir / "edited.pdf"

    try:
        PDFService.apply_edits(pdf_path, operations, str(output_path))
        storage.save_edited(file_id, output_path)

        return jsonify({
            "success": True,
            "message": "PDF edited successfully",
            "downloadUrl": f"/api/pdf/{file_id}/download"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/pdf/<file_id>/download', methods=['GET'])
def download_pdf(file_id):
    """Download the edited PDF."""
    storage = get_storage()
    pdf_path = storage.get_pdf_path(file_id)

    if not pdf_path or not os.path.exists(pdf_path):
        return jsonify({"error": "PDF not found"}), 404

    metadata = storage._load_metadata(file_id)
    original_name = metadata.get('original_name', 'document.pdf')
    download_name = original_name.replace('.pdf', '_edited.pdf')

    return send_file(
        pdf_path,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=download_name
    )

@api.route('/pdf/<file_id>', methods=['DELETE'])
def delete_pdf(file_id):
    """Delete an uploaded PDF."""
    storage = get_storage()
    if storage.delete_upload(file_id):
        return jsonify({"success": True})
    return jsonify({"error": "PDF not found"}), 404


@api.route('/pdf/<file_id>/preview', methods=['POST'])
def generate_preview(file_id):
    """Generate a preview PDF with applied edits."""
    storage = get_storage()
    pdf_path = storage.get_original_path(file_id)

    if not pdf_path or not os.path.exists(pdf_path):
        return jsonify({"error": "PDF not found"}), 404

    data = request.get_json()
    if not data or 'operations' not in data:
        return jsonify({"error": "No operations provided"}), 400

    operations = data['operations']

    # Create preview output path
    upload_dir = storage.get_upload_dir(file_id)
    preview_path = upload_dir / "preview.pdf"

    try:
        PDFService.apply_edits(pdf_path, operations, str(preview_path))

        # Get page count from preview
        pdf_info = PDFService.get_pdf_info(str(preview_path))

        return jsonify({
            "success": True,
            "pages": pdf_info['pages']
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route('/pdf/<file_id>/preview/page/<int:page_num>/image', methods=['GET'])
def get_preview_page_image(file_id, page_num):
    """Get preview PDF page as PNG image."""
    storage = get_storage()
    upload_dir = storage.get_upload_dir(file_id)
    preview_path = upload_dir / "preview.pdf"

    if not preview_path.exists():
        return jsonify({"error": "Preview not found"}), 404

    scale = float(request.args.get('scale', 1.5))
    # For preview, show text (hide_text=False) since we want to display the final result
    img_bytes = PDFService.render_page_to_image(str(preview_path), page_num, scale, hide_text=False)

    if not img_bytes:
        return jsonify({"error": "Page not found"}), 404

    from io import BytesIO
    return send_file(
        BytesIO(img_bytes),
        mimetype='image/png',
        download_name=f'preview_page_{page_num}.png'
    )


@api.route('/pdf/<file_id>/preview', methods=['DELETE'])
def delete_preview(file_id):
    """Delete the preview PDF."""
    storage = get_storage()
    upload_dir = storage.get_upload_dir(file_id)
    preview_path = upload_dir / "preview.pdf"

    if preview_path.exists():
        os.remove(preview_path)
        return jsonify({"success": True})

    return jsonify({"success": True})  # Not an error if preview doesn't exist
