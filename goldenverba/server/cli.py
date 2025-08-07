import os

import click
import uvicorn
from dotenv import load_dotenv

load_dotenv()


@click.group()
def cli():
    """Main command group for verba."""
    pass


@cli.command()
@click.option(
    "--port",
    default=8000,
    help="FastAPI Port",
)
@click.option(
    "--host",
    default="localhost",
    help="FastAPI Host",
)
@click.option(
    "--prod/--no-prod",
    default=False,
    help="Run in production mode.",
)
@click.option(
    "--workers",
    default=4,
    help="Workers to run Verba",
)
def start(port, host, prod, workers):
    """
    Run the FastAPI application.
    """
    # Use PORT environment variable if available, otherwise use the provided port
    actual_port = int(os.getenv("PORT", port))

    uvicorn.run(
        "goldenverba.server.api_postgresql:app",
        host=host,
        port=actual_port,
        reload=(not prod),
        workers=workers,
    )


@cli.command()
@click.option(
    "--confirm",
    is_flag=True,
    help="Confirm the reset operation",
)
def reset(confirm):
    """
    Reset the PostgreSQL database (removes all data).
    """
    if not confirm:
        click.echo(
            "This will delete all data in the database. Use --confirm to proceed."
        )
        return

    import asyncio

    from goldenverba.components.postgresql_manager import PostgreSQLManager

    async def async_reset():
        manager = PostgreSQLManager()
        try:
            await manager.connect()

            # Drop and recreate all tables
            async with manager.pool.acquire() as conn:
                await conn.execute("DROP SCHEMA public CASCADE;")
                await conn.execute("CREATE SCHEMA public;")
                await conn.execute("GRANT ALL ON SCHEMA public TO postgres;")
                await conn.execute("GRANT ALL ON SCHEMA public TO public;")

            # Reinitialize schema
            await manager._init_schema()
            click.echo("✅ Database reset completed successfully")

        except Exception as e:
            click.echo(f"❌ Reset failed: {e}")
        finally:
            if manager.pool:
                await manager.disconnect()

    asyncio.run(async_reset())


def main():
    # Configure tracing (optional)
    if os.getenv("LANGCHAIN_API_KEY"):
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        try:
            from langsmith import trace

            trace.configure_tracing(
                project_name=os.getenv("LANGCHAIN_PROJECT", "default"),
                api_key=os.getenv("LANGCHAIN_API_KEY"),
                endpoint=os.getenv(
                    "LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com"
                ),
            )
        except (ImportError, AttributeError):
            # Skip tracing if not available
            pass

    cli()


if __name__ == "__main__":
    main()
