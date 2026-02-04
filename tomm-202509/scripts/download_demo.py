#!/usr/bin/env python3
"""ArXiv Download Demo Script

This script demonstrates the ArXiv download functionality as part of the
preprocessing pipeline for chunker strategies comparison.
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel

from src.downloader import ArxivDownloader, download_papers_by_category
from src.config import RAW_DATA_DIR

console = Console()


async def demo_cs_ai_papers(max_papers: int = 5):
    """Download sample CS.AI papers for demonstration."""
    console.print(
        Panel.fit(
            "[bold blue]ArXiv Download Demo - CS.AI Papers[/bold blue]\n\n"
            f"Downloading {max_papers} recent papers from cs.AI category...",
            title="🔍 ArXiv Download Demo"
        )
    )
    
    try:
        results = await download_papers_by_category("cs.AI", max_papers)
        
        successful = sum(1 for _, path in results if path is not None)
        console.print(f"\n✅ Successfully downloaded {successful}/{len(results)} papers")
        
        if successful > 0:
            console.print(f"📁 Papers saved to: {RAW_DATA_DIR}")
            console.print("\n📋 Downloaded papers:")
            for paper, path in results:
                if path:
                    console.print(f"   • {paper.arxiv_id}: {paper.title}")
        
        return results
        
    except Exception as e:
        console.print(f"[red]❌ Download failed: {e}[/red]")
        return []


async def demo_search_query(query: str, max_papers: int = 3):
    """Download papers by search query."""
    console.print(
        Panel.fit(
            f"[bold green]Search Query Demo[/bold green]\n\n"
            f"Query: '{query}'\n"
            f"Max papers: {max_papers}",
            title="🔍 Custom Search"
        )
    )
    
    async with ArxivDownloader() as downloader:
        papers = await downloader.search_papers(query, max_papers)
        downloader.display_papers(papers)
        results = await downloader.download_papers(papers)
        
        successful = sum(1 for _, path in results if path is not None)
        console.print(f"\n✅ Downloaded {successful}/{len(results)} papers")
        
        return results


async def main():
    """Main demo function."""
    parser = argparse.ArgumentParser(
        description="ArXiv Download Demo - part of chunker strategies pipeline"
    )
    parser.add_argument(
        "--papers", "-n", type=int, default=5,
        help="Number of papers to download (default: 5)"
    )
    parser.add_argument(
        "--query", "-q", type=str,
        help="Custom search query (optional)"
    )
    parser.add_argument(
        "--category", "-c", type=str, default="cs.AI",
        help="ArXiv category (default: cs.AI)"
    )
    
    args = parser.parse_args()
    
    console.print(
        Panel.fit(
            "[bold cyan]ArXiv Downloader Demo[/bold cyan]\n\n"
            "This demo downloads ArXiv papers for the chunker strategies "
            "comparison system.\n\n"
            "Papers will be saved to the raw data directory and can then be "
            "processed using the preprocessing pipeline.",
            title="📚 Demo Setup"
        )
    )
    
    if args.query:
        await demo_search_query(args.query, args.papers)
    else:
        console.print(f"\n🔍 Downloading papers from category: {args.category}")
        results = await download_papers_by_category(args.category, args.papers)
        
        successful = sum(1 for _, path in results if path is not None)
        console.print(f"\n📊 Final Results: {successful}/{len(results)} papers downloaded")
    
    console.print(
        Panel.fit(
            "[bold green]Next Steps[/bold green]\n\n"
            "1. Run preprocessing pipeline: "
            "[cyan]python scripts/run_preprocessing_demo.py[/cyan]\n"
            "2. Compare chunking strategies using the processed papers\n"
            "3. Evaluate retrieval performance",
            title="🚀 What's Next?"
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
