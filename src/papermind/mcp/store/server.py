from dotenv import load_dotenv
load_dotenv()

from mcp.server.fastmcp import FastMCP
from papermind.mcp.store.tools import search_papers, get_paper_section, list_indexed_papers

mcp = FastMCP("paper-store", host="0.0.0.0", port=8008)

search_papers.register(mcp)
get_paper_section.register(mcp)
list_indexed_papers.register(mcp)


def main():
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
