import uuid
import fitz  # PyMuPDF
from pathlib import Path

class PDFService:
    @staticmethod
    def get_pdf_info(pdf_path):
        """Get basic PDF information."""
        doc = fitz.open(pdf_path)
        info = {
            "pages": len(doc),
            "pageInfo": []
        }
        for i, page in enumerate(doc):
            info["pageInfo"].append({
                "page": i + 1,
                "width": page.rect.width,
                "height": page.rect.height
            })
        doc.close()
        return info

    @staticmethod
    def extract_text_with_positions(pdf_path):
        """Extract text with positions from all pages."""
        doc = fitz.open(pdf_path)
        result = {"pages": []}

        for page_num, page in enumerate(doc):
            page_height = page.rect.height
            page_data = {
                "page": page_num + 1,
                "width": page.rect.width,
                "height": page_height,
                "textBlocks": []
            }

            # Extract text as dictionary with full details
            text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)

            for block in text_dict.get("blocks", []):
                if block.get("type") != 0:  # Skip non-text blocks
                    continue

                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if not text:
                            continue

                        bbox = span.get("bbox", [0, 0, 0, 0])
                        # Convert to PDF coordinates (origin bottom-left)
                        text_block = {
                            "id": str(uuid.uuid4()),
                            "text": text,
                            "x": bbox[0],
                            "y": page_height - bbox[3],  # Convert to bottom-left origin
                            "width": bbox[2] - bbox[0],
                            "height": bbox[3] - bbox[1],
                            "fontSize": span.get("size", 12),
                            "fontName": span.get("font", "Helvetica"),
                            "color": PDFService._color_to_hex(span.get("color", 0)),
                            "originalBbox": bbox  # Keep original for redaction
                        }
                        page_data["textBlocks"].append(text_block)

            result["pages"].append(page_data)

        doc.close()
        return result

    @staticmethod
    def apply_edits(pdf_path, operations, output_path):
        """Apply edit operations to PDF."""
        doc = fitz.open(pdf_path)

        # Group operations by page
        by_page = {}
        for op in operations:
            page_num = op.get('page', 1) - 1
            if page_num not in by_page:
                by_page[page_num] = []
            by_page[page_num].append(op)

        for page_num, page_ops in by_page.items():
            if page_num >= len(doc):
                continue

            page = doc[page_num]
            page_height = page.rect.height

            # First pass: redact modified/deleted text
            for op in page_ops:
                if op['type'] in ('modify', 'delete'):
                    # Get original bounding box
                    original_bbox = op.get('originalBbox')
                    if original_bbox:
                        rect = fitz.Rect(original_bbox)
                    else:
                        # Calculate from position
                        x = op.get('originalX', op.get('x', 0))
                        y = op.get('originalY', op.get('y', 0))
                        w = op.get('originalWidth', op.get('width', 100))
                        h = op.get('originalHeight', op.get('height', 12))
                        # Convert from PDF coords to fitz coords
                        top = page_height - y - h
                        rect = fitz.Rect(x, top, x + w, top + h)

                    # Add redaction with white fill
                    page.add_redact_annot(rect, fill=(1, 1, 1))

            # Apply all redactions
            page.apply_redactions()

            # Second pass: add new/modified text
            for op in page_ops:
                if op['type'] in ('modify', 'add'):
                    text = op.get('newText') if op['type'] == 'modify' else op.get('text', '')
                    x = op.get('x', 0)
                    y = op.get('y', 0)

                    # Convert PDF coords (bottom-left) to fitz coords (top-left)
                    fitz_y = page_height - y

                    font_size = op.get('fontSize', 12)
                    font_name = PDFService._map_font(op.get('fontName', 'Helvetica'))
                    color = PDFService._hex_to_rgb(op.get('color', '#000000'))

                    page.insert_text(
                        fitz.Point(x, fitz_y),
                        text,
                        fontsize=font_size,
                        fontname=font_name,
                        color=color
                    )

        doc.save(output_path)
        doc.close()
        return output_path

    @staticmethod
    def render_page_to_image(pdf_path, page_num, scale=1.5, hide_text=True):
        """Render a PDF page to PNG image bytes."""
        # Open original just to get page count
        original_doc = fitz.open(pdf_path)
        if page_num < 1 or page_num > len(original_doc):
            original_doc.close()
            return None
        original_doc.close()

        if hide_text:
            # Open a fresh copy for modification
            doc = fitz.open(pdf_path)
            page = doc[page_num - 1]

            # Redact all text areas with white to hide original text
            text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
            for block in text_dict.get("blocks", []):
                if block.get("type") != 0:  # Skip non-text blocks
                    continue
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        bbox = span.get("bbox")
                        if bbox:
                            rect = fitz.Rect(bbox)
                            # Expand slightly to fully cover
                            rect = rect + (-1, -1, 1, 1)
                            page.add_redact_annot(rect, fill=(1, 1, 1))
            page.apply_redactions()

            mat = fitz.Matrix(scale, scale)
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes("png")
            doc.close()  # Close without saving - changes are discarded
        else:
            doc = fitz.open(pdf_path)
            page = doc[page_num - 1]
            mat = fitz.Matrix(scale, scale)
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes("png")
            doc.close()

        return img_bytes

    @staticmethod
    def _color_to_hex(color):
        """Convert PyMuPDF color int to hex string."""
        if isinstance(color, int):
            # Color is stored as integer
            r = (color >> 16) & 0xFF
            g = (color >> 8) & 0xFF
            b = color & 0xFF
            return f"#{r:02x}{g:02x}{b:02x}"
        return "#000000"

    @staticmethod
    def _hex_to_rgb(hex_color):
        """Convert hex color to RGB tuple (0-1 range)."""
        if hex_color.startswith('#'):
            hex_color = hex_color[1:]
        r = int(hex_color[0:2], 16) / 255
        g = int(hex_color[2:4], 16) / 255
        b = int(hex_color[4:6], 16) / 255
        return (r, g, b)

    @staticmethod
    def _map_font(font_name):
        """Map font names to PyMuPDF built-in fonts."""
        font_map = {
            'Helvetica': 'helv',
            'Helvetica-Bold': 'hebo',
            'Times-Roman': 'tiro',
            'Times': 'tiro',
            'Courier': 'cour',
            'Arial': 'helv',
        }
        # Check if font name contains keywords
        lower_name = font_name.lower()
        if 'bold' in lower_name:
            return 'hebo'
        if 'times' in lower_name:
            return 'tiro'
        if 'courier' in lower_name or 'mono' in lower_name:
            return 'cour'
        return font_map.get(font_name, 'helv')
