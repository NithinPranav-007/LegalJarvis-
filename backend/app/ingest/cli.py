"""CLI application for corpus ingestion and administrative management."""

import typer

from app.db.session import sync_session_maker
from app.ingest.download import ingest_supreme_court_year
from app.ingest.embed import embed_unindexed_chunks, get_embedder

app = typer.Typer(help="LegalJarvis Ingestion and Data Management CLI")


@app.command()
def embed(
    batch_size: int = typer.Option(
        64, "--batch-size", "-b", help="Batch size for embedding generation"
    ),
) -> None:
    """Generate dense vector embeddings for unindexed chunks."""
    typer.echo(f"Starting batch embedding: batch_size={batch_size}")
    embedder = get_embedder()
    typer.echo(f"Using embedder: {embedder.__class__.__name__} (dim={embedder.dimension})")

    with sync_session_maker() as db:
        count = embed_unindexed_chunks(db=db, batch_size=batch_size, embedder=embedder)
        typer.echo(f"Batch embedding complete: {count} chunks embedded and persisted.")


@app.command()
def ingest(
    source: str = typer.Option("sc", "--source", "-s", help="Corpus source: 'sc' or 'hc'"),
    years: int = typer.Option(2023, "--years", "-y", help="Year to ingest (default: 2023)"),
    sample_limit: int = typer.Option(
        None, "--sample-limit", "-n", help="Limit number of documents for testing"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Bypass MAX_DOWNLOAD_GB gate"),
) -> None:
    """Ingest, checksum, and register court judgments."""
    typer.echo(f"Starting ingestion: source={source}, year={years}, sample_limit={sample_limit}")

    if source.lower() == "sc":
        with sync_session_maker() as db:
            result = ingest_supreme_court_year(
                db=db,
                year=years,
                sample_limit=sample_limit,
            )
            typer.echo(f"Ingestion finished: status={result['status']}")
            typer.echo(f"  Downloaded: {result['n_downloaded']}")
            typer.echo(f"  Registered: {result['n_registered']}")
            typer.echo(f"  Skipped (idempotent): {result['n_skipped']}")
            typer.echo(f"  Failed: {result['n_failed']}")
    else:
        typer.echo(f"Source '{source}' is not yet supported in Phase 1.")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
