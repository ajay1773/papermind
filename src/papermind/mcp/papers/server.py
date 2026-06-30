from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

from mcp.server.fastmcp import FastMCP
from papermind.config import settings
from papermind.mcp.papers.tools import (
    search_openalex,
    get_paper_tldr,
    get_related_papers,
    fetch_and_index,
    get_citation_network,
)

mcp = FastMCP("papers", host=settings.mcp_host, port=settings.mcp_papers_port)

search_openalex.register(mcp)
get_paper_tldr.register(mcp)
get_related_papers.register(mcp)
fetch_and_index.register(mcp)
get_citation_network.register(mcp)


def main():
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
