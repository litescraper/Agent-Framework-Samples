"""Opt-in Serper-compatible snippet search for marketing research."""

# Candidate for etheia-agent-map — no equivalent could be inspected (404).
# See: https://github.com/Etheia-Consulting-LLC/etheia-agent-map

from __future__ import annotations

import os
from typing import Annotated, Any

import requests
from agent_framework import ai_function


class SerperSearchTools:
    """Expose the workflow's search interface without changing its default."""

    def __init__(self, *, api_key: str | None = None) -> None:
        self._api_key = api_key or os.getenv("SERPER_API_KEY")
        self._base_url = (
            os.getenv("SERPER_BASE_URL") or "https://google.serper.dev"
        ).rstrip("/")
        self._search_tool = self._create_search_tool()

    @property
    def search(self) -> Any:
        return self._search_tool

    def _create_search_tool(self) -> Any:
        @ai_function(
            description="Search Google for titles, source URLs and snippets. This tool does not crawl pages or provide an advanced search depth."
        )
        def web_search(
            query: Annotated[str, "The search query."],
            search_depth: Annotated[
                str,
                "Compatibility option; both basic and advanced return snippets only.",
            ] = "basic",
            max_results: Annotated[int, "Maximum number of results (1-10)."] = 5,
        ) -> dict[str, Any]:
            return self._do_search(query, search_depth, max_results)

        return web_search

    def _do_search(
        self, query: str, search_depth: str = "basic", max_results: int = 5
    ) -> dict[str, Any]:
        empty = {"query": query, "results": [], "answer": ""}
        if not self._api_key:
            return {**empty, "error": "Set SERPER_API_KEY for web search"}
        if search_depth not in ("basic", "advanced"):
            return {**empty, "error": "Invalid search_depth"}
        try:
            max_results = max(1, min(10, max_results))
            response = requests.post(
                self._base_url + "/search",
                json={"q": query, "num": max_results},
                headers={
                    "X-API-KEY": self._api_key,
                    "Content-Type": "application/json",
                },
                timeout=30,
            )
            response.raise_for_status()
            results = [
                {
                    "title": item.get("title", ""),
                    "url": item["link"],
                    "content": item.get("snippet", ""),
                    "score": 0,
                }
                for item in response.json().get("organic", [])
                if item.get("link")
            ]
            return {"query": query, "results": results, "answer": ""}
        except (requests.RequestException, ValueError, TypeError, KeyError) as exc:
            response = getattr(exc, "response", None)
            detail = (
                f"HTTP {response.status_code}"
                if response is not None
                else type(exc).__name__
            )
            return {**empty, "error": f"Web search failed ({detail})"}
