"""Command-line interface for Baseball Manager AI"""
import click

@click.group()
def cli():
    """Baseball Manager AI - AI-powered baseball management assistant"""
    pass

@cli.command()
def download_data():
    """Download and process baseball data"""
    from baseball_manager_ai.data_processing.statcast_loader import download_statcast_data
    download_statcast_data()
    click.echo("✅ Data download complete")

@cli.command()
@click.option('--config', default='config/training_config.yaml', help='Training config file')
def train(config):
    """Train the baseball manager models"""
    from baseball_manager_ai.scripts.train_model import main
    main(config)
    click.echo("✅ Model training complete")

@cli.command()
@click.option('--team', help='Team to analyze')
@click.option('--date', help='Date for lineup (YYYY-MM-DD)')
def lineup(team, date):
    """Generate optimal lineup for a team"""
    from baseball_manager_ai.models.lineup_optimizer import LineupOptimizer
    optimizer = LineupOptimizer()
    lineup = optimizer.optimize_lineup(team, date)
    click.echo(f"🎯 Optimal lineup for {team} on {date}:")
    for i, player in enumerate(lineup, 1):
        click.echo(f"{i}. {player}")

def main():
    cli()

if __name__ == '__main__':
    main()
