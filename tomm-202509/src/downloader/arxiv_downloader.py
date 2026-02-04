"""ArXiv Paper Downloader

This module provides comprehensive ArXiv paper downloading functionality
for the chunking strategies demo system.
"""

import asyncio
import aiohttp
import aiofiles
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
import logging
from urllib.parse import urlencode
from datetime import datetime
import re

from rich.console import Console
from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    SpinnerColumn
)
from rich.table import Table

from ..config import (
    RAW_DATA_DIR,
    ARXIV_BASE_URL,
    MAX_CONCURRENT_DOWNLOADS
)

console = Console()
logger = logging.getLogger(__name__)


@dataclass
class ArxivPaper:
    """Represents an ArXiv paper with metadata."""
    arxiv_id: str
    title: str
    authors: List[str]
    abstract: str
    categories: List[str]
    published: datetime
    pdf_url: str
    entry_id: str
    summary: str = ""
    
    def __post_init__(self):
        """Clean up the data after initialization."""
        self.title = self._clean_text(self.title)
        self.abstract = self._clean_text(self.abstract)
        self.authors = [self._clean_text(author) for author in self.authors]
        if len(self.abstract) > 500:
            self.summary = self.abstract[:500] + "..."
        else:
            self.summary = self.abstract
    
    def _clean_text(self, text: str) -> str:
        """Clean text by removing extra whitespace and newlines."""
        if not text:
            return ""
        # Remove extra whitespace and normalize newlines
        text = re.sub(r'\s+', ' ', text.strip())
        return text
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'arxiv_id': self.arxiv_id,
            'title': self.title,
            'authors': self.authors,
            'abstract': self.abstract,
            'categories': self.categories,
            'published': self.published.isoformat(),
            'pdf_url': self.pdf_url,
            'entry_id': self.entry_id,
            'summary': self.summary
        }


class ArxivDownloader:
    """ArXiv paper downloader with search and download capabilities."""
    
    def __init__(self, download_dir: Optional[Path] = None):
        """Initialize the ArXiv downloader.
        
        Args:
            download_dir: Directory to save downloaded papers.
                         Defaults to RAW_DATA_DIR.
        """
        self.download_dir = download_dir or RAW_DATA_DIR
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=300)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def _build_search_url(self, query: str, max_results: int = 10,
                          start: int = 0) -> str:
        """Build ArXiv API search URL."""
        params = {
            'search_query': query,
            'start': start,
            'max_results': max_results,
            'sortBy': 'relevance',
            'sortOrder': 'descending'
        }
        return f"{ARXIV_BASE_URL}?{urlencode(params)}"
    
    async def search_papers(self, query: str,
                            max_results: int = 10) -> List[ArxivPaper]:
        """Search for papers on ArXiv.
        
        Args:
            query: Search query (can include categories, keywords, etc.)
            max_results: Maximum number of results to return
            
        Returns:
            List of ArxivPaper objects
        """
        if not self.session:
            msg = "ArxivDownloader must be used as async context manager"
            raise RuntimeError(msg)
        
        url = self._build_search_url(query, max_results)
        console.print(f"[blue]Searching ArXiv with query:[/blue] {query}")
        
        try:
            async with self.session.get(url) as response:
                response.raise_for_status()
                xml_content = await response.text()
                return self._parse_arxiv_response(xml_content)
        except Exception as e:
            logger.error(f"Failed to search ArXiv: {e}")
            console.print(f"[red]Search failed: {e}[/red]")
            return []
    
    def _parse_arxiv_response(self, xml_content: str) -> List[ArxivPaper]:
        """Parse ArXiv API XML response."""
        try:
            root = ET.fromstring(xml_content)
            papers = []
            
            # Define namespace
            ns = {'atom': 'http://www.w3.org/2005/Atom',
                  'arxiv': 'http://arxiv.org/schemas/atom'}
            
            for entry in root.findall('atom:entry', ns):
                try:
                    # Extract basic info
                    entry_id = entry.find('atom:id', ns).text
                    arxiv_id = entry_id.split('/')[-1].split('v')[0]
                    title = entry.find('atom:title', ns).text
                    
                    # Extract authors
                    authors = []
                    for author in entry.findall('atom:author', ns):
                        name_elem = author.find('atom:name', ns)
                        if name_elem is not None:
                            authors.append(name_elem.text)
                    
                    # Extract abstract
                    summary_elem = entry.find('atom:summary', ns)
                    if summary_elem is not None:
                        abstract = summary_elem.text
                    else:
                        abstract = ""
                    
                    # Extract categories
                    categories = []
                    for category in entry.findall('atom:category', ns):
                        term = category.get('term')
                        if term:
                            categories.append(term)
                    
                    # Extract publication date
                    published_elem = entry.find('atom:published', ns)
                    if published_elem is not None:
                        published_str = published_elem.text
                    else:
                        published_str = ""
                    published = datetime.fromisoformat(
                        published_str.replace('Z', '+00:00')
                    )
                    
                    # Find PDF link
                    pdf_url = ""
                    for link in entry.findall('atom:link', ns):
                        if link.get('type') == 'application/pdf':
                            pdf_url = link.get('href', '')
                            break
                    
                    if not pdf_url:
                        pdf_url = f"http://arxiv.org/pdf/{arxiv_id}.pdf"
                    
                    paper = ArxivPaper(
                        arxiv_id=arxiv_id,
                        title=title,
                        authors=authors,
                        abstract=abstract,
                        categories=categories,
                        published=published,
                        pdf_url=pdf_url,
                        entry_id=entry_id
                    )
                    papers.append(paper)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse entry: {e}")
                    continue
            
            return papers
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse XML response: {e}")
            console.print(f"[red]XML parsing failed: {e}[/red]")
            return []
    
    async def download_paper(self, paper: ArxivPaper,
                             progress: Optional[Progress] = None,
                             task_id: Optional[int] = None
                             ) -> Optional[Path]:
        """Download a single paper PDF.
        
        Args:
            paper: ArxivPaper object to download
            progress: Rich progress object for display
            task_id: Progress task ID for updates
            
        Returns:
            Path to downloaded file or None if failed
        """
        async with self.semaphore:  # Limit concurrent downloads
            if not self.session:
                msg = "ArxivDownloader must be used as async context manager"
                raise RuntimeError(msg)
            
            # Create filename
            safe_title = re.sub(r'[<>:"/\\|?*]', '_', paper.title[:50])
            filename = f"{paper.arxiv_id}_{safe_title}.pdf"
            filepath = self.download_dir / filename
            
            # Skip if already exists
            if filepath.exists():
                if progress and task_id:
                    desc = f"[green]Skipped[/green] {paper.arxiv_id}"
                    progress.update(task_id, description=desc)
                return filepath
            
            try:
                if progress and task_id:
                    desc = f"[blue]Downloading[/blue] {paper.arxiv_id}"
                    progress.update(task_id, description=desc)
                
                async with self.session.get(paper.pdf_url) as response:
                    response.raise_for_status()
                    
                    async with aiofiles.open(filepath, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                
                if progress and task_id:
                    desc = f"[green]Downloaded[/green] {paper.arxiv_id}"
                    progress.update(task_id, description=desc)
                
                return filepath
                
            except Exception as e:
                logger.error(f"Failed to download {paper.arxiv_id}: {e}")
                if progress and task_id:
                    desc = f"[red]Failed[/red] {paper.arxiv_id}"
                    progress.update(task_id, description=desc)
                
                # Clean up partial file
                if filepath.exists():
                    filepath.unlink()
                
                return None
    
    async def download_papers(
            self, papers: List[ArxivPaper]
    ) -> List[Tuple[ArxivPaper, Optional[Path]]]:
        """Download multiple papers with progress tracking.
        
        Args:
            papers: List of ArxivPaper objects to download
            
        Returns:
            List of (paper, filepath) tuples
        """
        if not papers:
            console.print("[yellow]No papers to download[/yellow]")
            return []
        
        console.print(f"[blue]Downloading {len(papers)} papers...[/blue]")
        
        results = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            
            # Create tasks for each paper
            tasks = []
            for paper in papers:
                desc = f"Queued {paper.arxiv_id}"
                task_id = progress.add_task(desc, total=1)
                tasks.append((paper, task_id))
            
            # Download papers concurrently
            download_tasks = [
                self.download_paper(paper, progress, task_id)
                for paper, task_id in tasks
            ]
            
            downloaded_paths = await asyncio.gather(
                *download_tasks, return_exceptions=True
            )
            
            # Collect results
            for (paper, task_id), result in zip(tasks, downloaded_paths):
                if isinstance(result, Exception):
                    desc = f"[red]Error[/red] {paper.arxiv_id}"
                    progress.update(task_id, description=desc)
                    results.append((paper, None))
                else:
                    progress.advance(task_id)
                    results.append((paper, result))
        
        # Summary
        successful = sum(1 for _, path in results if path is not None)
        console.print(f"\n[green]Download complete:[/green] {successful}/{len(papers)} papers downloaded")
        
        return results
    
    def display_papers(self, papers: List[ArxivPaper]) -> None:
        """Display papers in a formatted table."""
        if not papers:
            console.print("[yellow]No papers found[/yellow]")
            return
        
        table = Table(title="ArXiv Papers", show_header=True, header_style="bold magenta")
        table.add_column("ID", style="cyan", width=12)
        table.add_column("Title", style="white", width=50)
        table.add_column("Authors", style="yellow", width=30)
        table.add_column("Categories", style="green", width=15)
        table.add_column("Published", style="blue", width=12)
        
        for paper in papers:
            authors_str = ", ".join(paper.authors[:2])
            if len(paper.authors) > 2:
                authors_str += f" +{len(paper.authors)-2}"
            
            categories_str = ", ".join(paper.categories[:2])
            if len(paper.categories) > 2:
                categories_str += "..."
            
            table.add_row(
                paper.arxiv_id,
                paper.title[:47] + "..." if len(paper.title) > 50 else paper.title,
                authors_str,
                categories_str,
                paper.published.strftime("%Y-%m-%d")
            )
        
        console.print(table)


async def download_papers_by_query(query: str, max_results: int = 10,
                                  download_dir: Optional[Path] = None) -> List[Tuple[ArxivPaper, Optional[Path]]]:
    """Download papers by search query.
    
    Args:
        query: Search query
        max_results: Maximum papers to download
        download_dir: Directory to save papers
        
    Returns:
        List of (paper, filepath) tuples
    """
    async with ArxivDownloader(download_dir) as downloader:
        papers = await downloader.search_papers(query, max_results)
        downloader.display_papers(papers)
        return await downloader.download_papers(papers)


async def download_papers_by_category(category: str, max_results: int = 10,
                                     download_dir: Optional[Path] = None) -> List[Tuple[ArxivPaper, Optional[Path]]]:
    """Download papers by ArXiv category.
    
    Args:
        category: ArXiv category (e.g., 'cs.AI', 'math.CO')
        max_results: Maximum papers to download
        download_dir: Directory to save papers
        
    Returns:
        List of (paper, filepath) tuples
    """
    query = f"cat:{category}"
    return await download_papers_by_query(query, max_results, download_dir)


if __name__ == "__main__":
    import argparse
    
    def main():
        """CLI interface for ArXiv downloader."""
        parser = argparse.ArgumentParser(description="Download ArXiv papers")
        parser.add_argument("query", help="Search query or category")
        parser.add_argument("--max-results", "-n", type=int, default=10,
                           help="Maximum papers to download")
        parser.add_argument("--category", "-c", action="store_true",
                           help="Treat query as category (e.g., cs.AI)")
        parser.add_argument("--output-dir", "-o", type=Path,
                           help="Output directory")
        
        args = parser.parse_args()
        
        async def run():
            if args.category:
                results = await download_papers_by_category(
                    args.query, args.max_results, args.output_dir
                )
            else:
                results = await download_papers_by_query(
                    args.query, args.max_results, args.output_dir
                )
            
            successful = sum(1 for _, path in results if path is not None)
            console.print(f"\n[bold green]Summary:[/bold green] Downloaded {successful}/{len(results)} papers")
        
        asyncio.run(run())
    
    main()
