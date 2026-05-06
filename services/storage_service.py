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
        original_filename = "original.pdf"
        original_path = upload_dir / original_filename
        file.save(original_path)

        # Save metadata (store only filenames, not absolute paths)
        metadata = {
            "id": file_id,
            "original_name": file.filename,
            "upload_time": timestamp,
            "original_file": original_filename
        }
        self._save_metadata(file_id, metadata)

        return file_id, metadata

    def get_pdf_path(self, file_id):
        """Get path to PDF file (edited if exists, otherwise original)."""
        upload_dir = self.get_upload_dir(file_id)
        
        # Check for edited version first
        edited_path = upload_dir / "edited.pdf"
        if edited_path.exists():
            return str(edited_path)
            
        # Fallback to original
        original_path = upload_dir / "original.pdf"
        if original_path.exists():
            return str(original_path)
            
        return None

    def get_original_path(self, file_id):
        """Get path to original PDF file."""
        upload_dir = self.get_upload_dir(file_id)
        original_path = upload_dir / "original.pdf"
        
        if original_path.exists():
            return str(original_path)
        return None

    def save_edited(self, file_id, edited_pdf_path):
        """Update metadata with edited PDF path (optional now, as we check by filename)."""
        metadata = self._load_metadata(file_id)
        if not metadata:
            return None

        metadata['last_edit'] = datetime.now().strftime("%Y%m%d_%H%M%S")
        metadata['has_edited'] = True
        self._save_metadata(file_id, metadata)

        return str(edited_pdf_path)

    def get_upload_dir(self, file_id):
        """Get the upload directory for a file."""
        return self.upload_folder / file_id

    def delete_upload(self, file_id):
        """Delete an uploaded PDF and its metadata."""
        upload_dir = self.get_upload_dir(file_id)
        if upload_dir.exists():
            shutil.rmtree(upload_dir)
            return True
        return False

    def _save_metadata(self, file_id, metadata):
        """Save metadata to JSON file."""
        upload_dir = self.get_upload_dir(file_id)
        upload_dir.mkdir(exist_ok=True)
        metadata_path = upload_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

    def _load_metadata(self, file_id):
        """Load metadata from JSON file."""
        metadata_path = self.get_upload_dir(file_id) / "metadata.json"
        if not metadata_path.exists():
            return None
        with open(metadata_path, 'r') as f:
            return json.load(f)
