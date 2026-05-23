#!/usr/bin/env python3
"""Upload a local directory or zip file as a new Overleaf CE project."""

import os
import sys
import uuid
import zipfile
import tempfile
import re
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


def get_csrf_token(session, base_url, path="/login"):
    resp = session.get(f"{base_url}{path}", timeout=15)
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
    csrf = get_csrf_token(session, base_url, "/login")
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


def pack_directory(source_dir: Path, dest_zip: Path):
    """Pack a directory into a zip, files at root level (no subdirectory wrapper)."""
    with zipfile.ZipFile(dest_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in sorted(source_dir.rglob("*")):
            if file.is_file():
                zf.write(file, file.relative_to(source_dir))


def find_csrf(session, base_url):
    """Try multiple strategies to get a valid CSRF token after login."""
    resp = session.get(f"{base_url}/project", timeout=15)
    for pattern in [
        r'<meta name="ol-csrfToken" content="([^"]+)"',
        r'name="_csrf"[^>]*value="([^"]+)"',
        r'"csrfToken"\s*:\s*"([^"]+)"',
        r'csrf[_-]token.*?content="([^"]+)"',
    ]:
        match = re.search(pattern, resp.text, re.IGNORECASE)
        if match:
            return match.group(1)

    # Fallback: check cookies (some versions set XSRF-TOKEN cookie)
    for cookie in session.cookies:
        if "csrf" in cookie.name.lower():
            return cookie.value

    return ""


def upload_zip(session, base_url, zip_path: Path, project_name: str):
    csrf = find_csrf(session, base_url)
    if not csrf:
        print("  WARNING: CSRF token not found — request may be rejected")
    else:
        print(f"  CSRF token: {csrf[:12]}...")

    zip_filename = f"{project_name}.zip"
    file_size = zip_path.stat().st_size

    print(f"  Uploading '{project_name}' ({file_size // 1024} KB)...")

    with open(zip_path, "rb") as f:
        resp = session.post(
            f"{base_url}/project/new/upload",
            files={"qqfile": (zip_filename, f, "application/zip")},
            data={
                "_csrf": csrf,
                "name": project_name,
                "qquuid": str(uuid.uuid4()),
                "qqfilename": zip_filename,
                "qqtotalfilesize": file_size,
            },
            headers={"X-CSRF-Token": csrf} if csrf else {},
            timeout=120,
        )

    if resp.status_code != 200:
        print(f"  Response body: {resp.text[:500]}")
        raise RuntimeError(f"Upload failed with status {resp.status_code}")

    try:
        data = resp.json()
    except ValueError:
        raise RuntimeError(f"Unexpected response: {resp.text[:300]}")

    if not data.get("success"):
        raise RuntimeError(f"Upload rejected: {data}")

    project_id = data.get("project_id")
    print(f"  Created: '{project_name}'")
    print(f"  URL: {base_url}/project/{project_id}")
    return project_id


def main():
    load_env()

    if len(sys.argv) < 2:
        print("Usage: upload.py <path/to/dir_or_zip> [--name 'Project Name']")
        print("")
        print("  path  - directory to pack and upload, or a .zip file to upload directly")
        print("  --name - optional project name (defaults to directory/file name)")
        sys.exit(1)

    source = Path(sys.argv[1])

    project_name = source.stem if source.suffix == ".zip" else source.name
    if "--name" in sys.argv:
        idx = sys.argv.index("--name")
        if idx + 1 < len(sys.argv):
            project_name = sys.argv[idx + 1]

    if not source.exists():
        print(f"ERROR: '{source}' does not exist.")
        sys.exit(1)

    base_url = os.environ.get("OVERLEAF_URL", "http://localhost").rstrip("/")
    email = os.environ.get("OVERLEAF_EMAIL")
    password = os.environ.get("OVERLEAF_PASSWORD")

    if not email or not password:
        print("ERROR: Set OVERLEAF_EMAIL and OVERLEAF_PASSWORD in .env")
        sys.exit(1)

    session = requests.Session()

    print("Authenticating...")
    login(session, base_url, email, password)

    if source.is_dir():
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        try:
            print(f"  Packing '{source}' into zip...")
            pack_directory(source, tmp_path)
            upload_zip(session, base_url, tmp_path, project_name)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()
    elif source.suffix == ".zip":
        upload_zip(session, base_url, source, project_name)
    else:
        print(f"ERROR: '{source}' must be a directory or a .zip file.")
        sys.exit(1)


if __name__ == "__main__":
    main()
