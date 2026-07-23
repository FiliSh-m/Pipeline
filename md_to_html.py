# -*- coding: utf-8 -*-
import sys
import re
import markdown
from pathlib import Path

# -------- CONFIG --------
INPUT_MD = "Obrazová pipeline - verze 02.00.md"
OUTPUT_HTML = "pipeline.html"
CSS_FILE = "obsidian_atom.css"
# -----------------------

def remove_first_h1(html):
    """
    Removes the first <h1>...</h1> from the HTML body
    """
    return re.sub(r'<h1>.*?</h1>', '', html, count=1, flags=re.DOTALL)

def convert_obsidian_images(text):
    """
    Converts Obsidian image syntax:
    ![[image.png|800]] → <img src="images/image.png" width="800">
    ![[images/file.png]] → stays correct (no duplication)
    """

    pattern = r'!\[\[(.*?)\]\]'

    def repl(match):
        content = match.group(1)

        if "|" in content:
            path, size = content.split("|", 1)
        else:
            path, size = content, None

        # Normalize path → ensure it starts with "images/"
        path = path.strip()

        if not path.startswith("images/"):
            path = f"images/{path}"

        if size:
            return f'<img src="{path}" width="{size}">'
        else:
            return f'<img src="{path}">'

    return re.sub(pattern, repl, text)


def convert_internal_links(text):
    """
    Converts Obsidian-style links [[Page]] → Page (plain text for now)
    """
    return re.sub(r'\[\[(.*?)\]\]', r'\1', text)


def convert_pdf_links(text):
    """
    Rewrites GitHub PDF links to direct download relative links:
    [PDF verze ke stažení](https://github.com/...) -> <a href="Obrazová pipeline - verze 02.01.pdf" download="Obrazová pipeline - verze 02.01.pdf">PDF verze ke stažení</a>
    """
    import urllib.parse
    pattern = r'\[([^\]]+)\]\((https://github\.com/[^)]+\.pdf)\)'
    
    def repl(match):
        label = match.group(1)
        url = match.group(2)
        filename = url.split('/')[-1]
        decoded_filename = urllib.parse.unquote(filename)
        return f'<a href="{decoded_filename}" download="{decoded_filename}">{label}</a>'
        
    return re.sub(pattern, repl, text)


def load_markdown(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def build_html(body_html, title="Document"):
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="{CSS_FILE}?v=2">
</head>

<body>
    <header class="pipeline-header">
        <div class="nav-container">
            <a class="nav-back-link" href="index_cz.html">← Zpět na úvodní stránku</a>
            <a class="nav-back-link" href="./">← Back to Landing Page</a>
        </div>
        <h1>{title}</h1>
    </header>

    <section>
        {body_html}
    </section>
</body>
</html>
"""


def main():
    # Read the markdown input path from command line arguments if specified
    if len(sys.argv) > 1:
        input_md_path = Path(sys.argv[1])
    else:
        # Fallback: dynamically look for any markdown file matching pattern
        md_files = list(Path(".").glob("Obrazov*.md"))
        if not md_files:
            raise FileNotFoundError("No markdown file specified and could not find any Obrazov*.md file.")
        input_md_path = md_files[0]

    if not input_md_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {input_md_path}")

    print(f"Compiling: {input_md_path}")
    md_text = load_markdown(input_md_path)

    # Obsidian-specific fixes
    md_text = convert_obsidian_images(md_text)
    md_text = convert_internal_links(md_text)
    md_text = convert_pdf_links(md_text)

    # Convert Markdown → HTML
    html_body = markdown.markdown(
        md_text,
        extensions=["extra", "tables"]
    )

    # Extract title (first heading)
    title_match = re.search(r'<h1>(.*?)</h1>', html_body)
    title = title_match.group(1) if title_match else "Document"

    # REMOVE duplicated title from body
    html_body = remove_first_h1(html_body)

    full_html = build_html(html_body, title)

    Path(OUTPUT_HTML).write_text(full_html, encoding="utf-8")

    print(f"Done! Output saved to {OUTPUT_HTML}")


if __name__ == "__main__":
    main()