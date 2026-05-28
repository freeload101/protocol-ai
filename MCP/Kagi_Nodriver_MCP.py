import asyncio
import random
import os
import json
import logging
import traceback
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import nodriver
from markdownify import markdownify as md

# Requirements file for Kagi Nodriver MCP
# This ensures the correct nodriver version is used

# Chromium installed in the working path .\Chromium\
# nodriver==0.47.0 markdownify mcp tiktoken


# Log to file — never to stdout (stdout is reserved for MCP JSON-RPC)
logging.basicConfig(
    filename="kagi_mcp.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("kagi-mcp")

app = Server("kagi-search")

RESULTS_DIR = r".\results"
BROWSER_PATH = r".\Chromium\Application\chrome.exe"
USER_DATA_DIR = r".\Default"


async def launch_browser():
    return await nodriver.start(
        headless=False,
        user_data_dir=USER_DATA_DIR,
        browser_executable_path=BROWSER_PATH,
        browser_args=["--some-browser-arg=true"],
        lang="en-US",
        no_sandbox=True,
    )


async def run_search(search_query: str, lines_to_return: int, verbose: bool) -> str:
    os.makedirs(RESULTS_DIR, exist_ok=True)
    log.info(f"Starting search for: {search_query}")

    browser = await launch_browser()

    # Track only files created in this run
    current_run_ref_files: list[str] = []

    try:
        tab = await browser.get(f"https://kagi.com/search?token=AAAAAAAAAAAAAAAAAAAAAAAAAAAAADERPAAAAAAAAAAAAAA&q={search_query}")
        await asyncio.sleep(random.randint(1, 2))

        # Click Quick Answer button
        try:
            quick_answer_button = await tab.find("Quick Answer", best_match=True)
            if quick_answer_button:
                await quick_answer_button.scroll_into_view()
                await asyncio.sleep(random.uniform(0.5, 1.5))
                await quick_answer_button.click()
                log.info("Clicked Quick Answer button")
            else:
                log.warning("Quick Answer button not found")
        except Exception as e:
            log.warning(f"Could not interact with Quick Answer button: {e}")

        await asyncio.sleep(5)

        # Extract reference links via JavaScript
        js_script = """
            (() => {
                const results = [];
                const selectors = [
                    'div._0_qa_references_box ol li a',
                    'div._0_qa_more_info_box ol li a',
                    '.qa-content ol li a',
                    'ol[data-ref-list] li a'
                ];
                for (const sel of selectors) {
                    const anchors = document.querySelectorAll(sel);
                    if (anchors.length > 0) {
                        anchors.forEach(a => {
                            results.push({ href: a.href, text: a.innerText.trim() });
                        });
                        break;
                    }
                }
                return JSON.stringify(results);
            })()
        """
        try:
            raw = await tab.evaluate(js_script)
            links = json.loads(raw)
            log.info(f"Found {len(links)} reference links")
        except Exception as e:
            log.error(f"JS extraction failed: {e}")
            links = []

        # Process reference links in parallel
        async def process_link(i, link):
            try:
                new_tab = await browser.get(link["href"], new_window=True)
                await asyncio.sleep(10)
                page_html = await new_tab.evaluate("document.body.innerHTML")
                page_markdown = md(page_html)
                clean_text = "".join(
                    c for c in link["text"][:50] if c.isalnum() or c == " "
                ).replace(" ", "_")
                clean_text = "".join(c for c in clean_text if c.isalnum() or c == "_")
                filename = f"reference_{i+1}_{clean_text}.md"
                filepath = os.path.join(RESULTS_DIR, filename)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(page_markdown)
                log.info(f"Saved reference {i+1} to {filepath}")
                # Register this file as part of the current run
                current_run_ref_files.append(filename)
                await new_tab.close()
            except Exception as e:
                log.error(f"Failed to process link {i+1}: {e}\n{traceback.format_exc()}")

        if links:
            tasks = [process_link(i, link) for i, link in enumerate(links)]
            await asyncio.gather(*tasks)
        else:
            log.warning("No reference links found")

        # Export Quick Answer content to markdown (saved to disk only, not returned to LLM)
        content_script = """
            (() => {
                const contentBox = document.querySelector('.qa-content')
                                || document.querySelector('.qa-container-box');
                return contentBox ? contentBox.innerHTML : document.body.innerHTML;
            })()
        """
        qa_filepath = os.path.join(RESULTS_DIR, "quick_answer_output.md")
        try:
            html_content = await tab.evaluate(content_script)
            markdown_content = md(html_content)
            with open(qa_filepath, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            log.info("Saved Quick Answer content to quick_answer_output.md (excluded from LLM output)")
        except Exception as e:
            log.error(f"Failed to export Quick Answer: {e}\n{traceback.format_exc()}")

        await asyncio.sleep(1)

        # Build return string using only current-run reference files
        # quick_answer_output.md is intentionally excluded from LLM output
        output_parts = []

        # Sort by reference index (reference_1_..., reference_2_..., etc.)
        for ref_file in sorted(current_run_ref_files, key=lambda x: int(x.split("_")[1])):
            ref_path = os.path.join(RESULTS_DIR, ref_file)
            if not os.path.exists(ref_path):
                continue
            with open(ref_path, "r", encoding="utf-8") as f:
                content = f.read()
            if lines_to_return > 0:
                content = content[: lines_to_return * 100]
            output_parts.append(f"## {ref_file}\n\n{content}")

        return "\n\n---\n\n".join(output_parts) if output_parts else "No content retrieved."

    except Exception as e:
        err = f"Error: {e}\n{traceback.format_exc()}"
        log.error(err)
        return err

    finally:
        try:
            browser.stop()
            log.info("Browser stopped")
        except Exception:
            pass


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="kagi_search",
            description=(
                "Performs a Kagi search, clicks the Quick Answer button, "
                "collects reference links, and returns the markdown content."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "search_query": {
                        "type": "string",
                        "description": "The search query to send to Kagi.",
                        "default": "freeload101",
                    },
                    "lines_to_return": {
                        "type": "integer",
                        "description": "Approximate number of lines to return per reference file (0 = full content).",
                        "default": 200,
                    },
                    "verbose": {
                        "type": "boolean",
                        "description": "Enable verbose logging to kagi_mcp.log.",
                        "default": False,
                    },
                },
                "required": ["search_query"],
            },
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name != "kagi_search":
        raise ValueError(f"Unknown tool: {name}")

    search_query = arguments.get("search_query", "freeload101")
    lines_to_return = int(arguments.get("lines_to_return", 20))
    verbose = bool(arguments.get("verbose", False))

    log.info(f"Tool called: kagi_search | query={search_query} | lines={lines_to_return}")
    result = await run_search(search_query, lines_to_return, verbose)
    return [TextContent(type="text", text=result)]


async def main():
    log.info("MCP server starting...")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
