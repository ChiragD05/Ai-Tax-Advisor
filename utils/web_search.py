from duckduckgo_search import DDGS


def duckduckgo_search(
    query,
    max_results=5
):

    results = []

    with DDGS() as ddgs:

        search_results = ddgs.text(
            query,
            max_results=max_results
        )

        for r in search_results:

            results.append({
                "title": r.get("title", ""),
                "body": r.get("body", ""),
                "link": r.get("href", "")
            })

    return results