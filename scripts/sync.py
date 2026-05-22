#!/usr/bin/env python3
"""Sync Overleaf CE projects to local directories for version control."""

import os
import sys
import json
import zipfile
import shutil
import re
import requests
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
ENV_FILE = REPO_ROOT / ".env"
PROJECTS_DIR = REPO_ROOT / "projects"


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
    # Primary: /user/projects returns {"projects": [{"_id": ..., "name": ...}]}
    resp = session.get(f"{base_url}/user/projects", timeout=15)
    if resp.status_code == 200:
        try:
            data = resp.json()
            projects = data.get("projects", [])
            if isinstance(projects, list):
                return projects
        except ValueError:
            pass

    # Fallback: parse ol-prefetchedProjectsBlob from the project listing page
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

    raise RuntimeError(
        "Could not retrieve project list. Check credentials and Overleaf URL."
    )


def sanitize_name(name):
    name = re.sub(r"[^\w\-_. ]", "_", name).strip()
    name = re.sub(r"\s+", "_", name)
    return name or "unnamed_project"


def sync_project(session, base_url, project):
    project_id = project.get("id") or project.get("_id")
    name = sanitize_name(project.get("name", project_id))

    print(f"  Downloading: {project.get('name', name)}")
    resp = session.get(
        f"{base_url}/project/{project_id}/download/zip",
        stream=True,
        timeout=60,
    )
    if resp.status_code != 200:
        print(f"    ERROR: status {resp.status_code}")
        return False

    zip_path = PROJECTS_DIR / f"_{name}.zip"
    try:
        with open(zip_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        target = PROJECTS_DIR / name
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True)

        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(target)
    finally:
        if zip_path.exists():
            zip_path.unlink()

    print(f"    -> projects/{name}/")
    return True



def main():
    load_env()

    base_url = os.environ.get("OVERLEAF_URL", "http://localhost").rstrip("/")
    email = os.environ.get("OVERLEAF_EMAIL")
    password = os.environ.get("OVERLEAF_PASSWORD")

    if not email or not password:
        print("ERROR: Set OVERLEAF_EMAIL and OVERLEAF_PASSWORD in .env")
        sys.exit(1)

    PROJECTS_DIR.mkdir(exist_ok=True)

    session = requests.Session()

    print("Authenticating...")
    login(session, base_url, email, password)

    print("Fetching project list...")
    projects = get_projects(session, base_url)

    active = [p for p in projects if not p.get("archived") and not p.get("trashed")]
    print(f"Found {len(active)} active project(s) (of {len(projects)} total)")

    success = 0
    for project in active:
        if sync_project(session, base_url, project):
            success += 1

    print(f"\nSynced {success}/{len(active)} projects.")


if __name__ == "__main__":
    main()
