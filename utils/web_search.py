from ddgs import DDGS
import logging

logger = logging.getLogger(__name__)


def duckduckgo_search(
    query,
    max_results=5
):

    results = []

    query_lower = query.lower()
    is_news_query = any(k in query_lower for k in ["news", "headline", "today", "latest", "recent"])

    try:
        with DDGS() as ddgs:
            search_results = None
            if is_news_query:
                # Try news search first
                try:
                    search_results = list(ddgs.news(
                        query,
                        max_results=max_results
                    ))
                except Exception as e:
                    logger.warning(f"DDGS news search failed, falling back to text search: {e}")
                    # Fallback to text search
                    try:
                        search_results = list(ddgs.text(
                            query,
                            timelimit="w",
                            max_results=max_results
                        ))
                    except Exception as ex:
                        logger.warning(f"DDGS text search with timelimit failed: {ex}")
                        search_results = list(ddgs.text(
                            query,
                            max_results=max_results
                        ))
            else:
                # Try text search with timelimit='w' (weekly)
                try:
                    search_results = list(ddgs.text(
                        query,
                        timelimit="w",
                        max_results=max_results
                    ))
                except Exception as e:
                    logger.warning(f"DDGS text search with timelimit failed: {e}")
                    # Fallback to text search without timelimit
                    search_results = list(ddgs.text(
                        query,
                        max_results=max_results
                    ))

            if search_results:
                for r in search_results:
                    results.append({
                        "title": r.get("title", ""),
                        "body": r.get("body", ""),
                        "link": r.get("url") or r.get("href") or ""
                    })
    except Exception as e:
        logger.error(f"DuckDuckGo search completely failed: {e}")
        results = []

    return results