#!/usr/bin/env python3
"""Review a single pull request and post findings-first comment.

Designed to run inside a reusable GitHub Actions workflow.
"""

from __future__ import annotations

import json
import os
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


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def has_marker(comments: list[dict[str, Any]], sha: str) -> bool:
    marker = f"{MARKER_PREFIX}{sha} -->"
    return any(marker in str(c.get("body") or "") for c in comments)


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
        "Always return findings-first output with severity ordering and concrete remediation."
    )
    user_prompt = (
        "Skill instructions:\n"
        f"{skill_text}\n\n"
        "Review this pull request diff now. Focus on correctness, security, performance, maintainability, tests, and API compatibility.\n\n"
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
    return str(content)


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
    if isinstance(comments, list) and has_marker(comments, pr_sha):
        print(f"Review already posted for SHA {pr_sha[:8]}. Skipping.")
        return 0

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
        print("DRY_RUN enabled. Would post review comment:")
        print(body[:1200])
        return 0

    gh_post(comments_url, github_token, {"body": body})
    print(f"Posted review to {repo_full} PR #{pr_number} for SHA {pr_sha[:8]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
