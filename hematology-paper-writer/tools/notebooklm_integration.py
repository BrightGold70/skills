"""
NotebookLM Integration Module
==============================
Thin HTTP wrapper around the open-notebook REST API (self-hosted, port 5055).
Open Notebook is an open-source alternative to Google NotebookLM that provides
a full REST API — see https://github.com/lfnovo/open-notebook

Primary interface consumed by StatisticalBridge._enrich_with_nlm():
  nlm = NotebookLMIntegration(base_url="http://localhost:5055")
  answer = nlm.ask("What is MMR per ELN 2020?", notebook_id="<id>", timeout=5)

All methods fail silently (return falsy values) when the server is unavailable.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

try:
    import requests as _requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

logger = logging.getLogger(__name__)

_DEFAULT_BASE_URL = "http://localhost:5055"


class NotebookLMIntegration:
    """
    Stateless HTTP client for the open-notebook REST API.

    Parameters
    ----------
    base_url : str
        Base URL of the open-notebook server, e.g. ``http://localhost:5055``.
    """

    def __init__(self, base_url: str = _DEFAULT_BASE_URL) -> None:
        self._base = base_url.rstrip("/")

    # ── Core Q&A ──────────────────────────────────────────────────────────────

    def ask(
        self,
        question: str,
        notebook_id: Optional[str] = None,
        timeout: int = 5,
    ) -> str:
        """
        Ask a free-text question via the open-notebook search/ask endpoint.

        Uses ``POST /api/search/ask/simple`` (stateless, no session).

        Parameters
        ----------
        question : str
            The natural-language question to ask.
        notebook_id : str, optional
            If provided, restrict the search to this notebook; otherwise
            queries the global knowledge base.
        timeout : int
            HTTP timeout in seconds (default 5).

        Returns
        -------
        str
            The answer text, or an empty string on failure.
        """
        if not _HAS_REQUESTS:
            logger.debug("NotebookLMIntegration: 'requests' not installed — skipping ask()")
            return ""

        payload: dict = {"query": question}
        if notebook_id:
            payload["notebook_id"] = notebook_id

        try:
            resp = _requests.post(
                f"{self._base}/api/search/ask/simple",
                json=payload,
                timeout=timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            # open-notebook returns {"answer": "...", ...}
            return str(data.get("answer", "")).strip()
        except Exception as exc:  # noqa: BLE001
            logger.debug("NotebookLMIntegration.ask failed: %s", exc)
            return ""

    # ── Notebook management (used by bootstrap_notebooks.py) ──────────────────

    def create_notebook(self, name: str, description: str = "") -> Optional[str]:
        """
        Create a new notebook. Returns the notebook ID or None on failure.

        POST /api/notebooks
        """
        if not _HAS_REQUESTS:
            return None
        try:
            resp = _requests.post(
                f"{self._base}/api/notebooks",
                json={"name": name, "description": description},
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json().get("id")
        except Exception as exc:  # noqa: BLE001
            logger.debug("NotebookLMIntegration.create_notebook failed: %s", exc)
            return None

    def add_source_url(self, notebook_id: str, url: str) -> bool:
        """
        Add a URL source to a notebook. Returns True on success.

        POST /api/sources  (multipart form: url + notebook_id + process_async)
        """
        if not _HAS_REQUESTS:
            return False
        try:
            resp = _requests.post(
                f"{self._base}/api/sources",
                data={
                    "url": url,
                    "notebook_id": notebook_id,
                    "process_async": "true",
                },
                timeout=30,
            )
            resp.raise_for_status()
            return True
        except Exception as exc:  # noqa: BLE001
            logger.debug("NotebookLMIntegration.add_source_url failed for %s: %s", url, exc)
            return False

    def add_source_file(self, notebook_id: str, file_path: str) -> bool:
        """
        Upload a local file as a notebook source. Returns True on success.

        POST /api/sources  (multipart form: file + notebook_id)
        """
        if not _HAS_REQUESTS:
            return False
        path = Path(file_path)
        if not path.exists():
            logger.warning("NotebookLMIntegration.add_source_file: file not found: %s", file_path)
            return False
        try:
            with open(path, "rb") as fh:
                resp = _requests.post(
                    f"{self._base}/api/sources",
                    data={"notebook_id": notebook_id},
                    files={"file": (path.name, fh, "application/octet-stream")},
                    timeout=60,
                )
            resp.raise_for_status()
            return True
        except Exception as exc:  # noqa: BLE001
            logger.debug("NotebookLMIntegration.add_source_file failed for %s: %s", file_path, exc)
            return False

    def health_check(self) -> bool:
        """
        Returns True when the open-notebook server is reachable.

        GET /api/notebooks  (cheap list endpoint used as a health probe)
        """
        if not _HAS_REQUESTS:
            return False
        try:
            resp = _requests.get(f"{self._base}/api/notebooks", timeout=3)
            return resp.status_code < 500
        except Exception:  # noqa: BLE001
            return False

    # ── Project notebook discovery ─────────────────────────────────────────────

    def list_notebooks(self, timeout: int = 5) -> list:
        """
        List all notebooks. Returns a list of dicts (id, name, ...) or [] on failure.

        GET /api/notebooks
        """
        if not _HAS_REQUESTS:
            return []
        try:
            resp = _requests.get(f"{self._base}/api/notebooks", timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            return data if isinstance(data, list) else data.get("notebooks", [])
        except Exception as exc:  # noqa: BLE001
            logger.debug("list_notebooks failed: %s", exc)
            return []

    def find_by_name(self, prefix: str) -> Optional[dict]:
        """
        Return the first notebook whose name starts with ``prefix`` (case-insensitive).
        Returns None if no match is found.
        """
        prefix_lower = prefix.lower()
        for nb in self.list_notebooks():
            if nb.get("name", "").lower().startswith(prefix_lower):
                return nb
        return None

    def get_notebook(self, notebook_id: str, timeout: int = 5) -> Optional[dict]:
        """
        Fetch a single notebook by ID. Returns None on 404 or any error.

        GET /api/notebooks/{id}
        """
        if not _HAS_REQUESTS:
            return None
        try:
            resp = _requests.get(
                f"{self._base}/api/notebooks/{notebook_id}", timeout=timeout
            )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:  # noqa: BLE001
            logger.debug("get_notebook(%s) failed: %s", notebook_id, exc)
            return None

    def add_source_pmid(self, notebook_id: str, pmid: str) -> bool:
        """
        Add a PubMed article as a notebook source by PMID.

        Convenience wrapper around add_source_url() using the canonical
        PubMed URL pattern.
        """
        url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        return self.add_source_url(notebook_id, url)
