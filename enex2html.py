import argparse
import base64
import hashlib
import os
import xml.etree.ElementTree as ET
import re
from datetime import datetime
from html import unescape

def extract_notes_from_enex(enex_file):
    """Extracts notes from an Evernote ENEX file and returns them as a list of dictionaries."""
    notes = []
    tree = ET.parse(enex_file)
    root = tree.getroot()

    for note in root.findall(".//note"):
        title = note.find("title").text if note.find("title") is not None else "Untitled"
        content = note.find("content").text if note.find("content") is not None else "<p>No content</p>"
        created = note.find("created").text if note.find("created") is not None else None
        updated = note.find("updated").text if note.find("updated") is not None else None

        note_attributes = note.find("note-attributes")
        latitude = None
        longitude = None
        altitude = None
        if note_attributes is not None:
            lat_text = note_attributes.find("latitude").text if note_attributes.find("latitude") is not None else None
            lon_text = note_attributes.find("longitude").text if note_attributes.find("longitude") is not None else None
            alt_text = note_attributes.find("altitude").text if note_attributes.find("altitude") is not None else None

            try:
                latitude = float(lat_text) if lat_text is not None else None
            except (TypeError, ValueError):
                latitude = None

            try:
                longitude = float(lon_text) if lon_text is not None else None
            except (TypeError, ValueError):
                longitude = None

            try:
                altitude = float(alt_text) if alt_text is not None else None
            except (TypeError, ValueError):
                altitude = None

        resources = []
        for resource in note.findall("resource"):
            data_element = resource.find("data")
            resource_attributes = resource.find("resource-attributes")

            data_base64 = data_element.text if data_element is not None else None
            data_hash = data_element.get("hash") if data_element is not None else None
            mime = resource.find("mime").text if resource.find("mime") is not None else None
            filename = (
                resource_attributes.find("file-name").text
                if resource_attributes is not None and resource_attributes.find("file-name") is not None
                else None
            )

            resources.append({
                "hash": data_hash,
                "mime": mime,
                "filename": filename,
                "data_base64": data_base64,
            })

        notes.append({
            "title": title,
            "content": content,
            "created": created,
            "updated": updated,
            "latitude": latitude,
            "longitude": longitude,
            "altitude": altitude,
            "resources": resources,
        })

    return notes


def extract_resources(note, resources_dir, web_prefix="resources/"):
    os.makedirs(resources_dir, exist_ok=True)
    hash_map = {}

    mime_extensions = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "application/pdf": ".pdf",
        "audio/mpeg": ".mp3",
        "audio/mp4": ".m4a",
        "video/mp4": ".mp4",
    }

    for resource in note.get("resources", []):
        data_base64 = resource.get("data_base64")
        mime = resource.get("mime")
        filename = resource.get("filename")
        if not data_base64:
            continue

        try:
            data_bytes = base64.b64decode(data_base64)
        except (ValueError, TypeError):
            continue

        hash_hex = resource.get("hash")
        if not hash_hex:
            hash_hex = hashlib.md5(data_bytes).hexdigest()
        hash_hex = hash_hex.lower()

        ext = ""
        if mime:
            ext = mime_extensions.get(mime, "")

        output_name = os.path.basename(filename) if filename else f"{hash_hex}{ext}"
        output_path = os.path.join(resources_dir, output_name)
        try:
            with open(output_path, "wb") as f:
                f.write(data_bytes)
        except OSError:
            continue

        hash_map[hash_hex] = {
            "mime": mime,
            "output_path": f"{web_prefix}{output_name}",
        }

    return hash_map


def rewrite_en_media(content, hash_map):
    if not content or not hash_map:
        return content

    def replace_tag(match):
        hash_value = match.group(1).lower()
        resource_info = hash_map.get(hash_value)
        if not resource_info:
            return match.group(0)

        mime = resource_info.get("mime", "") or ""
        src = resource_info.get("output_path")
        if mime.startswith("image/"):
            return f'<img src="{src}">'  # minimal conversion
        if mime.startswith("audio/"):
            return f'<audio controls src="{src}"></audio>'
        if mime.startswith("video/"):
            return f'<video controls src="{src}"></video>'
        if mime == "application/pdf":
            return f'<a href="{src}">PDF</a>'
        return f'<a href="{src}">Attachment</a>'

    en_media_pattern = re.compile(r"<en-media[^>]*hash=(?:\"|')([0-9a-fA-F]+)(?:\"|')[^>]*/?>")
    return en_media_pattern.sub(replace_tag, content)


def normalize_enml_to_html(enml):
    if not enml:
        return ""

    cleaned = re.sub(r"^\s*<\?xml[^>]*\?>", "", enml, flags=re.IGNORECASE)
    cleaned = re.sub(r"<!DOCTYPE[^>]*>", "", cleaned, flags=re.IGNORECASE)

    match = re.search(r"<en-note[^>]*>(.*)</en-note>", cleaned, flags=re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()

    return cleaned.strip()


def parse_evernote_timestamp(ts):
    if not ts:
        return None
    try:
        dt = datetime.strptime(ts, "%Y%m%dT%H%M%SZ")
        return dt.isoformat() + "Z"
    except Exception:
        return None


def generate_snippet_from_html(html_content, max_length=400):
    if not html_content:
        return ""

    text = re.sub(r"<[^>]+>", " ", html_content)
    text = re.sub(r"https?://\S+", " ", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) <= max_length:
        return text

    return text[: max_length - 1].rstrip() + "…"


def compute_note_id(note):
    title = note.get("title") or ""
    content = note.get("content") or ""
    created = note.get("created")

    if created:
        base_string = f"{created}:{title}"
    else:
        base_string = f"{title}:{content[:200]}"

    return hashlib.md5(base_string.encode("utf-8")).hexdigest()


def build_location_html(note):
    lat = note.get("latitude")
    lon = note.get("longitude")
    alt = note.get("altitude")

    if lat is None or lon is None:
        return ""

    google_maps = f"https://www.google.com/maps?q={lat},{lon}"
    osm_maps = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=18/{lat}/{lon}"
    altitude_text = f" | Alt: {alt:.1f} m" if alt is not None else ""

    return (
        f'<div class="note-location">Location: {lat:.6f}, {lon:.6f}{altitude_text} '
        f'(<a href="{google_maps}">Google Maps</a> | '
        f'<a href="{osm_maps}">OpenStreetMap</a>)</div>'
    )

def process_enex_files(input_dir, output_dir):
    toc_file = os.path.join(output_dir, "index.html")
    notes_dir = os.path.join(output_dir, "notes")
    resources_dir = os.path.join(output_dir, "resources")

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(notes_dir, exist_ok=True)

    all_notes_metadata = []

    for filename in sorted(os.listdir(input_dir)):
        if not filename.endswith(".enex"):
            continue

        input_filepath = os.path.join(input_dir, filename)
        notes = extract_notes_from_enex(input_filepath)
        notes = sorted(
            notes,
            key=lambda n: (
                n.get("created") or "",
                n.get("title") or "",
            ),
        )

        for note in notes:
            title = note.get("title") or "Untitled"
            note_id = compute_note_id(note)
            normalized_content = normalize_enml_to_html(note.get("content"))
            snippet = generate_snippet_from_html(normalized_content)
            hash_map = extract_resources(note, resources_dir, web_prefix="../resources/")
            rendered_content = rewrite_en_media(normalized_content, hash_map)
            location_html = build_location_html(note)

            note_filename = f"{note_id}.html"
            note_filepath = os.path.join(notes_dir, note_filename)

            with open(note_filepath, "w", encoding="utf-8") as individual_out:
                individual_out.write(
                    f"""
                    <html>
                    <head>
                        <meta charset=\"UTF-8\">
                        <title>{title}</title>
                        <style>
                            body {{
                                font-family: 'Open Sans', sans-serif;
                                max-width: 800px;
                                margin: 20px auto;
                                background: #f9f9f9;
                                padding: 20px;
                                color: #333;
                            }}
                            h1 {{
                                font-family: 'Roboto', sans-serif;
                                color: #444;
                                text-align: center;
                                font-weight: 500;
                                border-bottom: 3px solid #4CAF50;
                                padding-bottom: 15px;
                                margin-bottom: 30px;
                            }}
                            .note {{
                                background: #fff;
                                padding: 20px;
                                border-radius: 8px;
                                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                                margin: 0 0 24px 0;
                                display: flow-root;
                                width: 100%;
                                box-sizing: border-box;
                                overflow: auto;
                                float: none;
                            }}
                            .note-title {{
                                font-size: 24px;
                                font-weight: 500;
                                color: #4CAF50;
                                margin-bottom: 10px;
                            }}
                            .note-meta {{
                                font-size: 14px;
                                color: #666;
                                margin-bottom: 8px;
                            }}
                            .note-location {{
                                font-size: 14px;
                                color: #555;
                                margin-bottom: 10px;
                            }}
                            .note-content {{
                                line-height: 1.8;
                                color: #555;
                                font-size: 16px;
                            }}
                            .note-content img, .note-content video {{
                                max-width: 100%;
                                height: auto;
                            }}
                            .note-content iframe {{
                                max-width: 100%;
                            }}
                            .note-content [style*="position:fixed"], .note-content [style*="position: fixed"] {{
                                position: static !important;
                            }}
                            .note-content [style*="position:sticky"], .note-content [style*="position: sticky"] {{
                                position: static !important;
                            }}
                            .note-content [style*="float:right"], .note-content [style*="float: right"] {{
                                float: none !important;
                            }}
                            .note-content [style*="float:left"], .note-content [style*="float: left"] {{
                                float: none !important;
                            }}
                        </style>
                    </head>
                    <body>
                        <h1>{title}</h1>
                        <div class=\"note\" id=\"note-{note_id}\"> 
                            <div class=\"note-title\">{title}</div>
                            <div class=\"note-meta\">Created: {note.get('created') or 'N/A'} | Updated: {note.get('updated') or 'N/A'}</div>
                            {location_html}
                            <div class=\"note-content\">{rendered_content}</div>
                        </div>
                    </body>
                    </html>
                    """
                )

            all_notes_metadata.append(
                {
                    "id": note_id,
                    "title": title,
                    "created": note.get("created"),
                    "updated": note.get("updated"),
                    "createdIso": parse_evernote_timestamp(note.get("created")),
                    "updatedIso": parse_evernote_timestamp(note.get("updated")),
                    "lat": note.get("latitude"),
                    "lon": note.get("longitude"),
                    "alt": note.get("altitude"),
                    "hasLocation": note.get("latitude") is not None and note.get("longitude") is not None,
                    "htmlPath": f"notes/{note_filename}",
                    "sourceEnex": filename,
                    "snippet": snippet,
                }
            )

    all_notes_metadata = sorted(
        all_notes_metadata,
        key=lambda n: (
            n.get("created") or "",
            n.get("title") or "",
        ),
    )

    with open(toc_file, "w", encoding="utf-8") as out:
        out.write(
            """
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Evernote Notes</title>
            <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500&family=Open+Sans:wght@300;400&display=swap" rel="stylesheet">
            <style>
                body {
                    font-family: 'Open Sans', sans-serif;
                    max-width: 1000px;
                    margin: 20px auto;
                    background: #f9f9f9;
                    padding: 20px;
                    color: #333;
                }
                h1 {
                    font-family: 'Roboto', sans-serif;
                    color: #444;
                    text-align: center;
                    font-weight: 500;
                    border-bottom: 3px solid #4CAF50;
                    padding-bottom: 15px;
                    margin-bottom: 30px;
                }
                .toc {
                    margin-bottom: 30px;
                    font-size: 18px;
                    list-style-type: none;
                    padding: 0;
                }
                .toc li {
                    margin-bottom: 12px;
                }
                .toc a {
                    text-decoration: none;
                    font-weight: 500;
                    color: #007BFF;
                    transition: color 0.3s ease, text-decoration 0.3s ease;
                }
                .toc a:hover {
                    color: #0056b3;
                    text-decoration: underline;
                }
                .toc-meta {
                    color: #666;
                    font-size: 14px;
                    margin-left: 6px;
                }
                .toc-location {
                    font-size: 14px;
                    margin-left: 8px;
                }
            </style>
        </head>
        <body>
            <h1>Evernote Notes</h1>
            <h2>Table of Contents</h2>
            <ul class="toc">
        """)

        for entry in all_notes_metadata:
            metadata_parts = []
            if entry.get("created"):
                metadata_parts.append(f"Created: {entry.get('created')}")
            if entry.get("updated"):
                metadata_parts.append(f"Updated: {entry.get('updated')}")

            metadata_text = (
                f" <span class=\"toc-meta\">{' | '.join(metadata_parts)}</span>"
                if metadata_parts
                else ""
            )

            location_snippet = ""
            if entry.get("lat") is not None and entry.get("lon") is not None:
                lat = entry.get("lat")
                lon = entry.get("lon")
                google_maps = f"https://www.google.com/maps?q={lat},{lon}"
                osm_maps = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=18/{lat}/{lon}"
                location_snippet = (
                    f' <span class="toc-location">📍 '
                    f'<a href="{google_maps}">Google</a> | '
                    f'<a href="{osm_maps}">OSM</a></span>'
                )

            out.write(
                f'<li><a href="{entry.get("htmlPath")}">{entry.get("title")}</a>{metadata_text}{location_snippet}</li>'
            )

        out.write("</ul>")

        out.write(
            """
            <div class="note-footer">
                <p>Generated by Python Script | Evernote Notes</p>
            </div>
        </body>
        </html>
        """
        )

    notes_json_path = os.path.join(output_dir, "notes.json")
    with open(notes_json_path, "w", encoding="utf-8") as notes_json:
        import json

        json.dump(all_notes_metadata, notes_json, indent=2, ensure_ascii=False)

    print(f"✅ All ENEX files have been processed and saved to: {output_dir}")
    print(f"✅ Table of Contents saved as: {toc_file}")
    print(f"✅ Individual notes saved in: {notes_dir}")
    print(f"✅ Notes index saved as: {notes_json_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert Evernote .enex files to styled HTML.")
    parser.add_argument("--input-dir", required=True, help="Directory containing .enex files")
    parser.add_argument("--output-dir", required=True, help="Directory to save output HTML files")

    args = parser.parse_args()
    process_enex_files(args.input_dir, args.output_dir)
