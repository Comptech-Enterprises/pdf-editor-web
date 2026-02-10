# PDF Editor Web

A web-based PDF editor that allows users to upload PDFs and edit text directly in the browser.

## Features

- Upload PDF files
- View PDF pages in browser
- Click on text to select and edit
- Double-click to modify text content
- Drag text to reposition
- Add new text anywhere
- Change font size, font family, and color
- Navigate multi-page PDFs
- Download edited PDF

## Tech Stack

- **Backend**: Python Flask
- **PDF Processing**: PyMuPDF (fitz)
- **Frontend**: PDF.js + Fabric.js
- **Styling**: CSS3

## Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/pdf-editor-web.git
cd pdf-editor-web
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

5. Open http://localhost:5000 in your browser

## Project Structure

```
pdf_editor_web/
├── app.py                 # Flask application
├── config.py              # Configuration
├── requirements.txt       # Python dependencies
├── api/
│   └── routes.py          # API endpoints
├── services/
│   ├── pdf_service.py     # PDF processing
│   └── storage_service.py # File storage
├── static/
│   └── css/editor.css     # Styles
├── templates/
│   ├── index.html         # Upload page
│   └── editor.html        # Editor page
└── uploads/               # Uploaded files (gitignored)
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload` | Upload PDF file |
| GET | `/api/pdf/<id>/text` | Extract text with positions |
| GET | `/api/pdf/<id>/page/<n>/image` | Get page as image |
| POST | `/api/pdf/<id>/edit` | Apply edits |
| GET | `/api/pdf/<id>/download` | Download edited PDF |

## Deployment

### Option 1: Railway (Recommended)
1. Push to GitHub
2. Connect to [Railway](https://railway.app)
3. Deploy from GitHub repo

### Option 2: Render
1. Push to GitHub
2. Create new Web Service on [Render](https://render.com)
3. Connect GitHub repo

### Option 3: Docker
```bash
docker build -t pdf-editor .
docker run -p 5000:5000 pdf-editor
```

## License

MIT License
