import os
from pydantic_ai import FunctionToolset
from tavily import TavilyClient
from typing import Annotated
from pydantic import Field

from schematico.schemas.tool_schemas import UrlArg

client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY", ""))


def search_web(
    query: str,
    max_results: Annotated[int, Field(ge=1, le=20)] = 5,
    topic: str = "general",
    include_answer: bool = False,
) -> dict:
    """Search the web with Tavily.

    Args:
        query: Search query.
        max_results: Number of results to return (1-20).
        topic: "general" or "news".
        include_answer: If True, include an LLM-generated answer summarizing results.

    Returns:
        dict with keys:
            query (str): Echoed query.
            answer (str | None): Present when `include_answer` is True.
            results (list[dict]): Each item has `title`, `url`, `content`, `score`.
            response_time (float): Seconds.
    """
    return client.search(
        query,
        max_results=max_results,
        topic=topic,
        include_answer=include_answer,
    )


def extract_web_content(url: UrlArg) -> dict:
    """Extract the main content of a web page with Tavily.

    Args:
        url: Page URL to extract.

    Returns:
        dict with keys:
            results (list[dict]): Each item has `url` and `raw_content` (markdown).
            failed_results (list[dict]): URLs that failed, with error messages.
            response_time (float): Seconds.
    """
    return client.extract(url)


def crawl_paths(url: UrlArg, instructions: str = "") -> dict:
    """Crawl a site from `url`, following links, and return page contents.

    Args:
        url: Root URL to crawl.
        instructions: Optional natural-language guidance for which pages to follow.

    Returns:
        dict with keys:
            base_url (str): Root of the crawl.
            results (list[dict]): Each item has `url` and `raw_content` (markdown).
            response_time (float): Seconds.
    """
    return client.crawl(url, instructions=instructions)


def map_website(url: UrlArg) -> dict:
    """Discover URLs reachable from `url` without fetching their contents.

    Args:
        url: Root URL to map.

    Returns:
        dict with keys:
            base_url (str): Root of the map.
            results (list[str]): Discovered URLs.
            response_time (float): Seconds.
    """
    return client.map(url)


web_search_toolset = FunctionToolset(
    tools=[search_web, extract_web_content, crawl_paths, map_website]
)
