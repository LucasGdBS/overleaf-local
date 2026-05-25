#!/usr/bin/env python3
"""Download an Overleaf CE project as a zip file."""

import os
import sys
import re
import json
import requests
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
ENV_FILE = REPO_ROOT / ".env"


def load_env():
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def get_csrf_token(session, base_url):
    resp = session.get(f"{base_url}/login", timeout=15)
    resp.raise_for_status()
    for pattern in [
        r'<meta name="ol-csrfToken" content="([^"]+)"',
        r'name="_csrf"[^>]*value="([^"]+)"',
        r'csrf[_-]token.*?content="([^"]+)"',
    ]:
        match = re.search(pattern, resp.text, re.IGNORECASE)
        if match:
            return match.group(1)
    return ""


def login(session, base_url, email, password):
    csrf = get_csrf_token(session, base_url)
    resp = session.post(
        f"{base_url}/login",
        json={"email": email, "password": password, "_csrf": csrf},
        headers={"Content-Type": "application/json"},
        allow_redirects=True,
        timeout=15,
    )
    if resp.status_code not in (200, 302):
        raise RuntimeError(f"Login failed with status {resp.status_code}")
    if "Invalid credentials" in resp.text or "wrong email" in resp.text.lower():
        raise RuntimeError("Login failed: invalid credentials")
    print("  Authenticated.")


def get_projects(session, base_url):
    resp = session.get(f"{base_url}/user/projects", timeout=15)
    if resp.status_code == 200:
        try:
            data = resp.json()
            projects = data.get("projects", [])
            if isinstance(projects, list):
                return projects
        except ValueError:
            pass

    resp = session.get(f"{base_url}/project", timeout=15)
    match = re.search(
        r'<meta name="ol-prefetchedProjectsBlob"[^>]*content="([^"]+)"',
        resp.text,
    )
    if match:
        try:
            raw = match.group(1).replace("&quot;", '"')
            data = json.loads(raw)
            return data.get("projects", [])
        except (ValueError, KeyError):
            pass

    raise RuntimeError("Could not retrieve project list. Check credentials and Overleaf URL.")


def find_project(projects, query):
    query_lower = query.lower()
    exact = [p for p in projects if p.get("name", "").lower() == query_lower]
    if exact:
        return exact[0]
    partial = [p for p in projects if query_lower in p.get("name", "").lower()]
    if len(partial) == 1:
        return partial[0]
    if len(partial) > 1:
        names = [p.get("name") for p in partial]
        raise RuntimeError(f"Ambiguous name '{query}', matches: {names}\nUse a more specific name.")
    raise RuntimeError(f"No project found matching '{query}'.")


def main():
    load_env()

    if len(sys.argv) < 2:
        print("Usage: zip_project.py <project-name> [--output path/to/file.zip]")
        sys.exit(1)

    query = sys.argv[1]
    output_path = None
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx + 1 < len(sys.argv):
            output_path = Path(sys.argv[idx + 1])

    base_url = os.environ.get("OVERLEAF_URL", "http://localhost").rstrip("/")
    email = os.environ.get("OVERLEAF_EMAIL")
    password = os.environ.get("OVERLEAF_PASSWORD")

    if not email or not password:
        print("ERROR: Set OVERLEAF_EMAIL and OVERLEAF_PASSWORD in .env")
        sys.exit(1)

    session = requests.Session()

    print("Authenticating...")
    login(session, base_url, email, password)

    print("Fetching project list...")
    projects = get_projects(session, base_url)

    project = find_project(projects, query)
    project_id = project.get("id") or project.get("_id")
    project_name = project.get("name", query)

    if output_path is None:
        safe_name = re.sub(r"[^\w\-_. ]", "_", project_name).replace(" ", "_")
        output_path = REPO_ROOT / f"{safe_name}.zip"

    print(f"  Downloading '{project_name}' as zip...")
    resp = session.get(
        f"{base_url}/project/{project_id}/download/zip",
        stream=True,
        timeout=60,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Download failed with status {resp.status_code}")

    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    size_kb = output_path.stat().st_size // 1024
    print(f"  Saved: {output_path} ({size_kb} KB)")


if __name__ == "__main__":
    main()
