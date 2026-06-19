from ddgs import DDGS

with DDGS() as ddgs:
    q1 = "any latest finance news around the world?"
    print(f"--- news search: {q1} ---")
    try:
        res1 = list(ddgs.news(q1, max_results=5))
        print("Count:", len(res1))
        for r in res1:
            print("- Title:", r.get("title"))
            print("  Body:", r.get("body"))
            print("  URL:", r.get("url"))
    except Exception as e:
        print("Error:", e)

    q2 = "is us-iran deal signed?"
    print(f"\n--- text search (timelimit='w'): {q2} ---")
    try:
        res2 = list(ddgs.text(q2, timelimit="w", max_results=5))
        print("Count:", len(res2))
        for r in res2:
            print("- Title:", r.get("title"))
            print("  Body:", r.get("body"))
            print("  URL:", r.get("href"))
    except Exception as e:
        print("Error:", e)

    print(f"\n--- news search: {q2} ---")
    try:
        res3 = list(ddgs.news(q2, max_results=5))
        print("Count:", len(res3))
        for r in res3:
            print("- Title:", r.get("title"))
            print("  Body:", r.get("body"))
            print("  URL:", r.get("url"))
    except Exception as e:
        print("Error:", e)
