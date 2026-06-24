import os
from tavily import TavilyClient

client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY", ""))


def search_web(query: str) -> dict:
    """
    Search the web using Tavily and return a list of results.

    Args:
        query (str): The search query.

    Returns:
        dict: A dictionary containing the search results.

    Example:

    >>> results = search_web("Who is Leo Messi?")
    >>> print(results)
    >>> {
    "query": "Who is Leo Messi?",
    "answer": "Lionel Messi, born in 1987, is an Argentine footballer widely regarded as one of the greatest players of his generation. He spent the majority of his career playing for FC Barcelona, where he won numerous domestic league titles and UEFA Champions League titles. Messi is known for his exceptional dribbling skills, vision, and goal-scoring ability. He has won multiple FIFA Ballon d'Or awards, numerous La Liga titles with Barcelona, and holds the record for most goals scored in a calendar year. In 2014, he led Argentina to the World Cup final, and in 2015, he helped Barcelona capture another treble. Despite turning 36 in June, Messi remains highly influential in the sport.",
    "images": [],
    "results": [
        {
        "title": "Lionel Messi Facts | Britannica",
        "url": "https://www.britannica.com/facts/Lionel-Messi",
        "content": "Lionel Messi, an Argentine footballer, is widely regarded as one of the greatest football players of his generation. Born in 1987, Messi spent the majority of his career playing for Barcelona, where he won numerous domestic league titles and UEFA Champions League titles. Messi is known for his exceptional dribbling skills, vision, and goal",
        "score": 0.81025416,
        "raw_content": null,
        "favicon": "https://britannica.com/favicon.png",
        "images": [
            {
            "url": "<string>",
            "description": "<string>"
            }
        ]
        }
    ],
    "response_time": "1.67",
    "auto_parameters": {
        "topic": "general",
        "search_depth": "basic"
    },
    "usage": {
        "credits": 1
    },
    "request_id": "123e4567-e89b-12d3-a456-426614174111"
    }
    """
    results = client.search(query)
    return results


def extract_web_content(url: str) -> dict:
    """
    Extract content from a web page using Tavily.

    Args:
        url (str): The URL of the web page to extract content from.

    Returns:
        dict: A dictionary containing the extracted content.

    Example:
    >>> content = extract_web_content(""https://en.wikipedia.org/wiki/Artificial_intelligence"")
    >>> print(content)
    >>> {
    "results": [
        {
        "url": "https://en.wikipedia.org/wiki/Artificial_intelligence",
        "raw_content": "\"Jump to content\\nMain menu\\nSearch\\nAppearance\\nDonate\\nCreate account\\nLog in\\nPersonal tools\\n        Photograph your local culture, help Wikipedia and win!\\nToggle the table of contents\\nArtificial intelligence\\n161 languages\\nArticle\\nTalk\\nRead\\nView source\\nView history\\nTools\\nFrom Wikipedia, the free encyclopedia\\n\\\"AI\\\" redirects here. For other uses, see AI (disambiguation) and Artificial intelligence (disambiguation).\\nPart of a series on\\nArtificial intelligence (AI)\\nshow\\nMajor goals\\nshow\\nApproaches\\nshow\\nApplications\\nshow\\nPhilosophy\\nshow\\nHistory\\nshow\\nGlossary\\nvte\\nArtificial intelligence (AI), in its broadest sense, is intelligence exhibited by machines, particularly computer systems. It is a field of research in computer science that develops and studies methods and software that enable machines to perceive their environment and use learning and intelligence to take actions that maximize their chances of achieving defined goals.[1] Such machines may be called AIs.\\nHigh-profile applications of AI include advanced web search engines (e.g., Google Search); recommendation systems (used by YouTube, Amazon, and Netflix); virtual assistants (e.g., Google Assistant, Siri, and Alexa); autonomous vehicles (e.g., Waymo); generative and creative tools (e.g., ChatGPT and AI art); and superhuman play and analysis in strategy games (e.g., chess and Go)...................",
        "images": [],
        "favicon": "https://en.wikipedia.org/static/favicon/wikipedia.ico"
        }
    ],
    "failed_results": [],
    "response_time": 0.02,
    "usage": {
        "credits": 1
    },
    "request_id": "123e4567-e89b-12d3-a456-426614174111"
    }

    """
    content = client.extract(url)
    return content


def crawl_paths(url: str, instructions: str = "") -> dict:
    """
    Crawl a website and extract content from multiple pages using Tavily.

    Args:
        url (str): The URL of the website to crawl.
        instructions (str): Optional instructions for the crawling process.

    Returns:
        dict: A dictionary containing the extracted content from multiple pages.

    Example:
    >>> crawl_results = crawl_paths("https://docs.tavily.com", "Find all pages on the Python SDK")
    >>> print(crawl_results)
    >>> {
    "base_url": "docs.tavily.com",
    "results": [
        {
        "url": "https://docs.tavily.com/welcome",
        "raw_content": "Welcome - Tavily Docs\n\n[Tavily Docs home page![light logo](https://mintlify.s3.us-west-1.amazonaws.com/tavilyai/logo/light.svg)![dark logo](https://mintlify.s3.us-west-1.amazonaws.com/tavilyai/logo/dark.svg)](https://tavily.com/)\n\nSearch or ask...\n\nCtrl K\n\n- [Support](mailto:support@tavily.com)\n- [Get an API key](https://app.tavily.com)\n- [Get an API key](https://app.tavily.com)\n\nSearch...\n\nNavigation\n\n[Home](/welcome)[Documentation](/documentation/about)[SDKs](/sdk/python/quick-start)[Examples](/examples/use-cases/data-enrichment)[FAQ](/faq/faq)\n\nExplore our docs\n\nYour journey to state-of-the-art web search starts right here.\n\n[## Quickstart\n\nStart searching with Tavily in minutes](documentation/quickstart)[## API Reference\n\nStart using Tavily's powerful APIs](documentation/api-reference/endpoint/search)[## API Credits Overview\n\nLearn how to get and manage your Tavily API Credits](documentation/api-credits)[## Rate Limits\n\nLearn about Tavily's API rate limits for both development and production environments](documentation/rate-limits)[## Python\n\nGet started with our Python SDK, `tavily-python`](sdk/python/quick-start)[## Playground\n\nExplore Tavily's APIs with our interactive playground](https://app.tavily.com/playground)",
        "favicon": "https://mintlify.s3-us-west-1.amazonaws.com/tavilyai/_generated/favicon/apple-touch-icon.png?v=3"
        },
        {
        "url": "https://docs.tavily.com/documentation/api-credits",
        "raw_content": "Credits & Pricing - Tavily Docs\n\n[Tavily Docs home page![light logo](https://mintlify.s3.us-west-1.amazonaws.com/tavilyai/logo/light.svg)![dark logo](https://mintlify.s3.us-west-1.amazonaws.com/tavilyai/logo/dark.svg)](https://tavily.com/)\n\nSearch or ask...\n\nCtrl K\n\n- [Support](mailto:support@tavily.com)\n- [Get an API key](https://app.tavily.com)\n- [Get an API key](https://app.tavily.com)\n\nSearch...\n\nNavigation\n\nOverview\n\nCredits & Pricing\n\n[Home](/welcome)[Documentation](/documentation/about)[SDKs](/sdk/python/quick-start)[Examples](/examples/use-cases/data-enrichment)[FAQ](/faq/faq)\n\n- [API Playground](https://app.tavily.com/playground)\n- [Community](https://community.tavily.com)\n- [Blog](https://blog.tavily.com)\n\n##### Overview\n\n- [About](/documentation/about)\n- [Quickstart](/documentation/quickstart)\n- [Credits & Pricing](/documentation/api-credits)\n- [Rate Limits](/documentation/rate-limits)\n\n##### API Reference\n\n- [Introduction](/documentation/api-reference/introduction)\n- [POST\n\n  Tavily Search](/documentation/api-reference/endpoint/search)\n- [POST\n\n  Tavily Extract](/documentation/api-reference/endpoint/extract)\n- [POST\n\n  Tavily Crawl](/documentation/api-reference/endpoint/crawl)\n- [POST\n\n  Tavily Map](/documentation/api-reference/endpoint/map)\n\n##### Best Practices\n\n- [Best Practices for Search](/documentation/best-practices/best-practices-search)\n- [Best Practices for Extract](/documentation/best-practices/best-practices-extract)\n\n##### Tavily MCP Server\n\n- [Tavily MCP Server](/documentation/mcp)\n\n##### Integrations\n\n- [LangChain](/documentation/integrations/langchain)\n- [LlamaIndex](/documentation/integrations/llamaindex)\n- [Zapier](/documentation/integrations/zapier)\n- [Dify](/documentation/integrations/dify)\n- [Composio](/documentation/integrations/composio)\n- [Make](/documentation/integrations/make)\n- [Agno](/documentation/integrations/agno)\n- [Pydantic AI](/documentation/integrations/pydantic-ai)\n- [FlowiseAI](/documentation/integrations/flowise)\n\n##### Legal\n\n- [Security & Compliance](https://trust.tavily.com)\n- [Privacy Policy](https://tavily.com/privacy)\n\n##### Help\n\n- [Help Center](https://help.tavily.com)\n\n##### Tavily Search Crawler\n\n- [Tavily Search Crawler](/documentation/search-crawler)\n\nOverview\n\n# Credits & Pricing\n\nLearn how to get and manage your Tavily API Credits.\n\n## [​](#free-api-credits) Free API Credits\n\n[## Get your free API key\n\nYou get 1,000 free API Credits every month.\n**No credit card required.**](https://app.tavily.com)\n\n## [​](#pricing-overview) Pricing Overview\n\nTavily operates on a simple, credit-based model:\n\n- **Free**: 1,000 credits/month\n- **Pay-as-you-go**: $0.008 per credit (allows you to be charged per credit once your plan's credit limit is reached).\n- **Monthly plans**: $0.0075 - $0.005 per credit\n- **Enterprise**: Custom pricing and volume\n\n| **Plan** | **Credits per month** | **Monthly price** | **Price per credit** |\n| --- | --- | --- | --- |\n| **Researcher** | 1,000 | Free | - |\n| **Project** | 4,000 | $30 | $0.0075 |\n| **Bootstrap** | 15,000 | $100 | $0.0067 |\n| **Startup** | 38,000 | $220 | $0.0058 |\n| **Growth** | 100,000 | $500 | $0.005 |\n| **Pay as you go** | Per usage | $0.008 / Credit | $0.008 |\n| **Enterprise** | Custom | Custom | Custom |\n\nHead to [my plan](https://app.tavily.com/account/plan) to explore our different options and manage your plan.\n\n## [​](#api-credits-costs) API Credits Costs\n\n### [​](#tavily-search) Tavily Search\n\nYour [search depth](/api-reference/endpoint/search#body-search-depth) determines the cost of your request.\n\n- **Basic Search (`basic`):**\n  Each request costs **1 API credit**.\n- **Advanced Search (`advanced`):**\n  Each request costs **2 API credits**.\n\n### [​](#tavily-extract) Tavily Extract\n\nThe number of successful URL extractions and your [extraction depth](/api-reference/endpoint/extract#body-extract-depth) determines the cost of your request. You never get charged if a URL extraction fails.\n\n- **Basic Extract (`basic`):**\n  Every 5 successful URL extractions cost **1 API credit**\n- **Advanced Extract (`advanced`):**\n  Every 5 successful URL extractions cost **2 API credits**\n\n[Quickstart](/documentation/quickstart)[Rate Limits](/documentation/rate-limits)\n\n[x](https://x.com/tavilyai)[github](https://github.com/tavily-ai)[linkedin](https://linkedin.com/company/tavily)[website](https://tavily.com)\n\n[Powered by Mintlify](https://mintlify.com/preview-request?utm_campaign=poweredBy&utm_medium=docs&utm_source=docs.tavily.com)\n\nOn this page\n\n- [Free API Credits](#free-api-credits)\n- [Pricing Overview](#pricing-overview)\n- [API Credits Costs](#api-credits-costs)\n- [Tavily Search](#tavily-search)\n- [Tavily Extract](#tavily-extract)",
        "favicon": "https://mintlify.s3-us-west-1.amazonaws.com/tavilyai/_generated/favicon/apple-touch-icon.png?v=3"
        },
        {
        "url": "https://docs.tavily.com/documentation/about",
        "raw_content": "Who are we?\n-----------\n\nWe're a team of AI researchers and developers passionate about helping you build the next generation of AI assistants. Our mission is to empower individuals and organizations with accurate, unbiased, and factual information.\n\nWhat is the Tavily Search Engine?\n---------------------------------\n\nBuilding an AI agent that leverages realtime online information is not a simple task. Scraping doesn't scale and requires expertise to refine, current search engine APIs don't provide explicit information to queries but simply potential related articles (which are not always related), and are not very customziable for AI agent needs. This is why we're excited to introduce the first search engine for AI agents - [Tavily](https://app.tavily.com/).\n\nTavily is a search engine optimized for LLMs, aimed at efficient, quick and persistent search results. Unlike other search APIs such as Serp or Google, Tavily focuses on optimizing search for AI developers and autonomous AI agents. We take care of all the burden of searching, scraping, filtering and extracting the most relevant information from online sources. All in a single API call!\n\nTo try the API in action, you can now use our hosted version on our [API Playground](https://app.tavily.com/playground).\n\nWhy choose Tavily?\n------------------\n\nTavily shines where others fail, with a Search API optimized for LLMs.\n\nHow does the Search API work?\n-----------------------------\n\nTraditional search APIs such as Google, Serp and Bing retrieve search results based on a user query. However, the results are sometimes irrelevant to the goal of the search, and return simple URLs and snippets of content which are not always relevant. Because of this, any developer would need to then scrape the sites to extract relevant content, filter irrelevant information, optimize the content to fit LLM context limits, and more. This task is a burden and requires a lot of time and effort to complete. The Tavily Search API takes care of all of this for you in a single API call.\n\nThe Tavily Search API aggregates up to 20 sites per a single API call, and uses proprietary AI to score, filter and rank the top most relevant sources and content to your task, query or goal. In addition, Tavily allows developers to add custom fields such as context and limit response tokens to enable the optimal search experience for LLMs.\n\nTavily can also help your AI agent make better decisions by including a short answer for cross-agent communication.\n\nGetting started\n---------------\n\n[Sign up](https://app.tavily.com/) for Tavily to get your API key. You get **1,000 free API Credits every month**. No credit card required.\n\n[Get your free API key --------------------- You get 1,000 free API Credits every month. **No credit card required.**](https://app.tavily.com/)Head to our [API Playground](https://app.tavily.com/playground) to familiarize yourself with our API.\n\nTo get started with Tavily's APIs and SDKs using code, head to our [Quickstart Guide](https://docs.tavily.com/guides/quickstart) and follow the steps.",
        "favicon": "https://mintlify.s3-us-west-1.amazonaws.com/tavilyai/_generated/favicon/apple-touch-icon.png?v=3"
        }
    ],
    "response_time": 1.23,
    "usage": {
        "credits": 1
    },
    "request_id": "123e4567-e89b-12d3-a456-426614174111"
    }
    """
    crawl_results = client.crawl(url, instructions=instructions)
    return crawl_results


def map_website(url: str) -> dict:
    """
    Map a website and extract its structure using Tavily.

    Args:
        url (str): The URL of the website to map.

    Returns:
        dict: A dictionary containing the mapped structure of the website.

    Example:
    >>> map_results = map_website("https://docs.tavily.com")
    >>> print(map_results)
    >>> {
    "base_url": "docs.tavily.com",
    "results": [
        "https://docs.tavily.com/welcome",
        "https://docs.tavily.com/documentation/api-credits",
        "https://docs.tavily.com/documentation/about"
    ],
    "response_time": 1.23,
    "usage": {
        "credits": 1
    },
    "request_id": "123e4567-e89b-12d3-a456-426614174111"
    }

    """
    map_results = client.map(url)
    return map_results
