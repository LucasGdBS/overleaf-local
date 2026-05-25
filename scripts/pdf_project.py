#!/usr/bin/env python3
"""Compile and download the PDF of an Overleaf CE project."""

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


def find_csrf_after_login(session, base_url):
    resp = session.get(f"{base_url}/project", timeout=15)
    for pattern in [
        r'<meta name="ol-csrfToken" content="([^"]+)"',
        r'name="_csrf"[^>]*value="([^"]+)"',
        r'"csrfToken"\s*:\s*"([^"]+)"',
    ]:
        match = re.search(pattern, resp.text, re.IGNORECASE)
        if match:
            return match.group(1)
    for cookie in session.cookies:
        if "csrf" in cookie.name.lower():
            return cookie.value
    return ""


def compile_project(session, base_url, project_id):
    csrf = find_csrf_after_login(session, base_url)
    resp = session.post(
        f"{base_url}/project/{project_id}/compile",
        json={
            "rootResourcePath": "main.tex",
            "draft": False,
            "check": "silent",
            "incrementalCompilesEnabled": False,
            "stopOnFirstError": False,
        },
        headers={"X-CSRF-Token": csrf} if csrf else {},
        timeout=120,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Compile request failed with status {resp.status_code}")
    return resp.json()


def main():
    load_env()

    if len(sys.argv) < 2:
        print("Usage: pdf_project.py <project-name> [--output path/to/file.pdf]")
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
        output_path = REPO_ROOT / f"{safe_name}.pdf"

    print(f"  Compiling '{project_name}'...")
    result = compile_project(session, base_url, project_id)

    compile_data = result.get("compile", result)
    status = compile_data.get("status")
    if status not in ("success", "clsi-maintenance"):
        print(f"  Compile status: {status}")
        output_files = compile_data.get("outputFiles", [])
        errors = [f for f in output_files if f.get("type") == "log"]
        if errors:
            print("  Check the compile log for errors.")
        if status != "success":
            raise RuntimeError(f"Compilation failed with status: {status}")

    output_files = compile_data.get("outputFiles", [])
    pdf_file = next((f for f in output_files if f.get("type") == "pdf"), None)
    if not pdf_file:
        raise RuntimeError("No PDF output found. The project may not have compiled successfully.")

    pdf_url = pdf_file.get("url")
    if not pdf_url:
        build = pdf_file.get("build", "")
        pdf_url = f"/project/{project_id}/output/output.pdf?build={build}&compileGroup=standard"

    if pdf_url.startswith("/"):
        pdf_url = base_url + pdf_url

    print(f"  Downloading PDF...")
    resp = session.get(pdf_url, stream=True, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"PDF download failed with status {resp.status_code}")

    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    size_kb = output_path.stat().st_size // 1024
    print(f"  Saved: {output_path} ({size_kb} KB)")


if __name__ == "__main__":
    main()
