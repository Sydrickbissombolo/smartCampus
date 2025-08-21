import click
from backend.database import init_db
from backend.models import get_ticket_counts_by_week

@click.group()
def cli():
    pass

@cli.command()
def init():
    init_db()
    click.echo("Database initialized.")

@cli.command()
def report():
    data = get_ticket_counts_by_week()
    for row in data:
        click.echo(f"Week {row['week']}: {row['count']} tickets")

if __name__ == "__main__":
    cli()
