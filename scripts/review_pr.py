#!/usr/bin/env python3
"""Review a single pull request and post findings-first comment.

Designed to run inside a reusable GitHub Actions workflow.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

import requests

MARKER_PREFIX = "<!-- code-review-pro:"
MAX_FILES = 80
MAX_PATCH_CHARS = 120_000


def env_required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def gh_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def gh_get(url: str, token: str, params: dict[str, Any] | None = None) -> Any:
    resp = requests.get(url, headers=gh_headers(token), params=params, timeout=30)
    if resp.status_code >= 400:
        raise RuntimeError(f"GitHub GET failed {resp.status_code}: {url}: {resp.text[:300]}")
    return resp.json()


def gh_post(url: str, token: str, payload: dict[str, Any]) -> Any:
    resp = requests.post(url, headers=gh_headers(token), json=payload, timeout=30)
    if resp.status_code >= 400:
        raise RuntimeError(f"GitHub POST failed {resp.status_code}: {url}: {resp.text[:300]}")
    return resp.json()


def gh_patch(url: str, token: str, payload: dict[str, Any]) -> Any:
    resp = requests.patch(url, headers=gh_headers(token), json=payload, timeout=30)
    if resp.status_code >= 400:
        raise RuntimeError(f"GitHub PATCH failed {resp.status_code}: {url}: {resp.text[:300]}")
    return resp.json()


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def has_marker(comments: list[dict[str, Any]], sha: str) -> bool:
    marker = f"{MARKER_PREFIX}{sha} -->"
    return any(marker in str(c.get("body") or "") for c in comments)


def find_existing_review_comment(comments: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Find our existing code-review-pro comment (by marker, any PR version)."""
    marker_start = MARKER_PREFIX
    for comment in comments:
        body = str(comment.get("body") or "")
        if body.startswith(marker_start):
            return comment
    return None


def build_patch_blob(pr: dict[str, Any], files: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    lines.append(f"PR: {pr.get('title', '-')}")
    lines.append(f"URL: {pr.get('html_url', '-')}")
    lines.append(f"Author: {((pr.get('user') or {}).get('login') or '-')}")
    lines.append("")

    for f in files[:MAX_FILES]:
        filename = str(f.get("filename") or "")
        status = str(f.get("status") or "")
        patch = str(f.get("patch") or "")
        lines.append(f"File: {filename} ({status})")
        lines.append("```diff")
        lines.append(patch)
        lines.append("```")
        lines.append("")

    text = "\n".join(lines)
    if len(text) > MAX_PATCH_CHARS:
        return text[:MAX_PATCH_CHARS] + "\n\n[TRUNCATED]"
    return text


def call_llm(skill_text: str, patch_blob: str, model: str, base_url: str, api_key: str) -> str:
    system_prompt = (
        "You are a strict senior code reviewer. Follow the provided skill instructions exactly. "
        "Always return findings-first output with severity ordering and concrete remediation. "
        "CRITICAL: Every finding MUST include the exact file path and line number in the Location field. "
        "Use format: filename.ext:42 or path/to/file.ext:100 or path/to/file.py (line 25). "
        "No finding is valid without a specific line number."
    )
    user_prompt = (
        "Skill instructions:\n"
        f"{skill_text}\n\n"
        "Review this pull request diff now. Focus on correctness, security, performance, maintainability, tests, and API compatibility.\n"
        "IMPORTANT: For each finding, MUST include the file path and line number in the Location column. "
        "Examples: src/auth.ts:45, lib/utils.py (line 12), config/database.yml:8\n\n"
        f"{patch_blob}"
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    endpoint_url = f"{base_url}/chat/completions" if not base_url.endswith("/chat/completions") else base_url
    resp = requests.post(endpoint_url, headers=headers, data=json.dumps(payload), timeout=90)
    if resp.status_code >= 400:
        raise RuntimeError(f"LLM call failed {resp.status_code}: {resp.text[:300]}")

    data = resp.json()
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("LLM response has no choices")

    content = ((choices[0] or {}).get("message") or {}).get("content")
    if not content:
        raise RuntimeError("LLM response has empty content")
    
    # Debug: log first part of review
    print(f"[DEBUG] LLM Review (first 500 chars):\n{content[:500]}\n...")
    
    return str(content)


def parse_findings_with_locations(review_md: str) -> list[tuple[str, int, str]]:
    """Extract (file_path, line_number, finding_text) from review markdown.
    
    Looks for patterns like:
    - "file.ts:42" or "file.ts:L42" or "file.ts (line 42)"
    - In markdown tables or prose
    """
    findings: list[tuple[str, int, str]] = []
    
    # Pattern 1: "path/to/file.ext:42" or "path/to/file.ext:L42"
    # More robust: matches word chars, slashes, dots, dashes in path + any extension
    pattern1 = r'([\w/.\-]+\.\w+):(?:L)?(\d+)'
    # Pattern 2: "path/to/file.ext (line 42)"
    pattern2 = r'([\w/.\-]+\.\w+)\s+\(line\s+(\d+)\)'
    
    lines = review_md.split('\n')
    debug_lines_checked = 0
    for line in lines:
        debug_lines_checked += 1
        # Try pattern 1
        match1 = re.search(pattern1, line, re.IGNORECASE)
        if match1:
            file_path, line_num_str = match1.groups()
            try:
                line_num = int(line_num_str)
                findings.append((file_path, line_num, line.strip()))
            except ValueError:
                continue
        
        # Try pattern 2
        match2 = re.search(pattern2, line, re.IGNORECASE)
        if match2:
            file_path, line_num_str = match2.groups()
            try:
                line_num = int(line_num_str)
                findings.append((file_path, line_num, line.strip()))
            except ValueError:
                continue
    
    print(f"[DEBUG] Parsed {len(findings)} line-level findings from {debug_lines_checked} lines")
    if findings:
        for f in findings[:3]:
            print(f"[DEBUG]   - {f[0]}:{f[1]}")
    
    return findings


def post_review_comments(
    owner: str,
    repo: str,
    pr_number: int,
    pr_sha: str,
    github_token: str,
    findings: list[tuple[str, int, str]],
) -> None:
    """Post fresh line-level comments for each commit, avoiding duplicates.
    
    - Each commit gets new line-level comments based on current diff lines
    - Checks if identical comment already exists at that line/file
    - Skips posting if same finding already commented
    """
    if not findings:
        return
    
    print(f"[DEBUG] Processing {len(findings)} line-level findings...")
    
    # Get existing PR comments to check for duplicates
    pr_comments_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/comments"
    try:
        existing_comments = gh_get(pr_comments_url, github_token, params={"per_page": 100})
        if not isinstance(existing_comments, list):
            existing_comments = []
    except RuntimeError:
        existing_comments = []
    
    # Build a set of (file_path, line_num) -> comment_body for existing comments
    existing_by_location: dict[tuple[str, int], set[str]] = {}
    for comment in existing_comments:
        file_path = comment.get("path", "")
        line = comment.get("line")
        body = str(comment.get("body", "")).lower()
        
        if file_path and line:
            key = (file_path, line)
            if key not in existing_by_location:
                existing_by_location[key] = set()
            existing_by_location[key].add(body)
    
    # Post line comments, skipping duplicates
    posted_count = 0
    skipped_count = 0
    
    for file_path, line_num, finding_text in findings:
        comment_body = finding_text.replace("|", "").strip()
        if not comment_body or len(comment_body) < 3:
            continue
        
        # Check if identical comment already exists at this location
        key = (file_path, line_num)
        existing_bodies = existing_by_location.get(key, set())
        body_normalized = comment_body.lower()
        
        if any(body_normalized in existing_body for existing_body in existing_bodies):
            print(f"[DEBUG] ⊘ Skipping duplicate comment at {file_path}:{line_num}")
            skipped_count += 1
            continue
        
        payload = {
            "commit_sha": pr_sha,
            "path": file_path,
            "line": line_num,
            "side": "RIGHT",
            "body": f"🔍 {comment_body[:500]}",
        }
        
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/comments"
        try:
            gh_post(url, github_token, payload)
            print(f"[DEBUG] ✓ Posted line comment at {file_path}:{line_num}")
            posted_count += 1
        except RuntimeError as e:
            # Line might not be in diff - silently continue
            print(f"[DEBUG] Could not post at {file_path}:{line_num} (may not be in diff)")
            continue
    
    print(f"[DEBUG] Line comments: {posted_count} posted, {skipped_count} skipped (duplicates)")


def main() -> int:
    github_token = env_required("GITHUB_TOKEN")
    llm_api_key = env_required("LLM_API_KEY")
    llm_model = os.getenv("LLM_MODEL", "gpt-4o").strip() or "gpt-4o"
    llm_base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1/chat/completions").strip()

    repo_full = env_required("TARGET_REPO")
    pr_number = int(env_required("PR_NUMBER"))
    pr_sha = env_required("PR_SHA")
    skill_path = os.getenv("SKILL_PATH", ".github/skills/code-review-pro/SKILL.md").strip()
    dry_run = os.getenv("DRY_RUN", "false").lower() == "true"

    owner, repo = repo_full.split("/", 1)
    pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    files_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
    comments_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"

    pr = gh_get(pr_url, github_token)
    if bool(pr.get("draft")):
        print("Draft PR detected. Skipping review.")
        return 0

    comments = gh_get(comments_url, github_token, params={"per_page": 100})
    if not isinstance(comments, list):
        comments = []

    files = gh_get(files_url, github_token, params={"per_page": 100})
    if not isinstance(files, list) or not files:
        print("No changed files detected. Skipping.")
        return 0

    skill_text = read_text(skill_path)
    patch_blob = build_patch_blob(pr, files)
    review_md = call_llm(skill_text, patch_blob, llm_model, llm_base_url, llm_api_key)

    marker = f"{MARKER_PREFIX}{pr_sha} -->"
    body = f"{marker}\n## Automated Code Review (code-review-pro)\n\n{review_md}"

    if dry_run:
        print("DRY_RUN enabled. Would post/update review comment:")
        print(body[:1200])
        findings = parse_findings_with_locations(review_md)
        if findings:
            print(f"\nFound {len(findings)} line-level findings in output")
            for file_path, line_num, text in findings[:5]:
                print(f"  - {file_path}:{line_num}")
        return 0

    # Find existing review comment or create new one (unified summary)
    existing_comment = find_existing_review_comment(comments)
    
    if existing_comment:
        # Update existing comment
        comment_id = existing_comment.get("id")
        comment_url = f"https://api.github.com/repos/{owner}/{repo}/issues/comments/{comment_id}"
        gh_patch(comment_url, github_token, {"body": body})
        print(f"Updated review comment on {repo_full} PR #{pr_number} for SHA {pr_sha[:8]}")
    else:
        # Post new comment
        gh_post(comments_url, github_token, {"body": body})
        print(f"Posted review comment to {repo_full} PR #{pr_number} for SHA {pr_sha[:8]}")
    
    # Post fresh line-level comments for this commit
    findings = parse_findings_with_locations(review_md)
    if findings:
        post_review_comments(owner, repo, pr_number, pr_sha, github_token, findings)
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
