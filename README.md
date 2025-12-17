# Evernote ENEX to HTML Converter  

First I extracted ENEX files via Evernote API cloud to gather the GPS location
https://github.com/vzhd1701/evernote-backup

Convert Evernote `.enex` files into beautifully styled HTML with a **Table of Contents** and **individual note pages**.  

## 🚀 Features  
- Parses and converts Evernote `.enex` files to HTML.  
- Generates a **Table of Contents (ToC)** linking to individual notes.  
- Preserves original filenames for easy reference.  
- Uses **modern fonts & styling** for readability.  
- Command-line support for flexible input/output directory selection.  

## 🛠 Installation  
Ensure you have **Python 3.x** installed, then clone the repository:  
```bash
git clone https://github.com/your-username/enex-to-html.git
cd enex-to-html
```

## 📌 Usage
Run the converter with your input and output directories:
```bash
python3 enex2html.py --input-dir "/path/to/enex/files" --output-dir "/path/to/output"
```

The input directory is walked recursively, and the relative folder structure is mirrored under `notes/` in the output (e.g., `Personal/Journal.enex` produces `notes/Personal/<note_id>.html`).

## 📂 Output Structure
```
output-dir/
│── index.html         # Table of Contents linking to individual notes
│── notes/             # One HTML page per note (isolated layout, mirrors input folders)
│   ├── <note_id>.html
│   ├── Personal/
│   │   └── <note_id>.html
│   └── ...
│── resources/         # Extracted attachments referenced by notes
│── notes.json         # Machine-readable index of all notes
│── build_report.txt   # Summary of the latest conversion run
```

## 🗺️ notes.json schema
Each run writes a `notes.json` file in the output directory to support map-first and search experiences. It is a UTF-8 JSON array with one object per note:

- `id`: Stable note identifier used for filenames (`notes/<id>.html`) and anchors.
- `title`: Note title.
- `created`, `updated`: Original Evernote timestamp strings, if present.
- `createdIso`, `updatedIso`: Parsed ISO-8601 timestamps when available.
- `lat`, `lon`, `alt`: GPS coordinates (numbers or `null`).
- `hasLocation`: Boolean flag when latitude/longitude are present.
- `htmlPath`: Relative link to the rendered note HTML (e.g., `notes/<id>.html`).
- `sourceEnex`: Source `.enex` filename (basename).
- `snippet`: Plain-text summary (first few hundred characters) for search.

## ▶️ How to run locally
1. Convert your notes
```bash
python3 enex2html.py --input-dir /path/to/enex/files --output-dir /tmp/output
```

2. Serve the output locally for quick inspection (default: port 8000)
```bash
python3 serve_local.py --dir /tmp/output --port 8000
# then open the printed URL, e.g., http://localhost:8000/index.html
```

Each run also writes a `build_report.txt` in the output directory with counts for ENEX files, notes, geotagged notes, resources, and the key output paths.

## 📝 Example
After running the script, open `index.html` in your browser to view all notes in an organized format.

## 📚 License  
MIT License  

---
💡 **Tip:** Customize the CSS in the script to tweak the design as needed!

