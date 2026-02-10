import os
import uuid
import json
import shutil
from pathlib import Path
from datetime import datetime

class StorageService:
    def __init__(self, upload_folder):
        self.upload_folder = Path(upload_folder)
        self.upload_folder.mkdir(exist_ok=True)

    def save_upload(self, file):
        """Save uploaded PDF and return unique ID."""
        file_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create directory for this upload
        upload_dir = self.upload_folder / file_id
        upload_dir.mkdir(exist_ok=True)

        # Save original file
        original_path = upload_dir / "original.pdf"
        file.save(original_path)

        # Save metadata
        metadata = {
            "id": file_id,
            "original_name": file.filename,
            "upload_time": timestamp,
            "original_path": str(original_path)
        }
        self._save_metadata(file_id, metadata)

        return file_id, metadata

    def get_pdf_path(self, file_id):
        """Get path to PDF file (edited if exists, otherwise original)."""
        metadata = self._load_metadata(file_id)
        if not metadata:
            return None
        edited_path = metadata.get('edited_path')
        if edited_path and os.path.exists(edited_path):
            return edited_path
        return metadata.get('original_path')

    def get_original_path(self, file_id):
        """Get path to original PDF file."""
        metadata = self._load_metadata(file_id)
        if not metadata:
            return None
        return metadata.get('original_path')

    def save_edited(self, file_id, edited_pdf_path):
        """Update metadata with edited PDF path."""
        metadata = self._load_metadata(file_id)
        if not metadata:
            return None

        metadata['edited_path'] = str(edited_pdf_path)
        metadata['last_edit'] = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._save_metadata(file_id, metadata)

        return edited_pdf_path

    def get_upload_dir(self, file_id):
        """Get the upload directory for a file."""
        return self.upload_folder / file_id

    def delete_upload(self, file_id):
        """Delete an uploaded PDF and its metadata."""
        upload_dir = self.upload_folder / file_id
        if upload_dir.exists():
            shutil.rmtree(upload_dir)
            return True
        return False

    def _save_metadata(self, file_id, metadata):
        """Save metadata to JSON file."""
        metadata_path = self.upload_folder / file_id / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

    def _load_metadata(self, file_id):
        """Load metadata from JSON file."""
        metadata_path = self.upload_folder / file_id / "metadata.json"
        if not metadata_path.exists():
            return None
        with open(metadata_path, 'r') as f:
            return json.load(f)
