# Evernote ENEX to HTML Converter  

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
Run the script with your input and output directories:  
```bash
python3 convert_enex_to_html.py --input-dir "/path/to/enex/files" --output-dir "/path/to/output"
```

## 📂 Output Structure
```
output-dir/
│── ToC.html          # Merged file with Table of Contents + all notes
│── individual_notes/  # Folder containing separate HTML files per .enex
│   ├── note1.html
│   ├── note2.html
│   ├── ...
│── notes.json         # Machine-readable index of all notes
```

## 🗺️ notes.json schema
Each run writes a `notes.json` file in the output directory to support map-first and search experiences. It is a UTF-8 JSON array with one object per note:

- `id`: Stable note identifier used in HTML anchors (matches `id="note-<id>"`).
- `title`: Note title.
- `created`, `updated`: Original Evernote timestamp strings, if present.
- `lat`, `lon`, `alt`: GPS coordinates (numbers or `null`).
- `htmlPath`: Relative link to the rendered note HTML (e.g., `individual_notes/example.html#note-<id>`).
- `sourceEnex`: Source `.enex` filename (basename).

## 📝 Example  
After running the script, open `ToC.html` in your browser to view all notes in an organized format.

## 📚 License  
MIT License  

---
💡 **Tip:** Customize the CSS in the script to tweak the design as needed!

