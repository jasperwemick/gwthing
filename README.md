# GW2 Black Lion Market Tool

A Python-based tool to track market traction on the Guild Wars 2 Black Lion Market by the hour.

## Setup
1. Install requirements: `pip install -r requirements.txt`
2. Add your API key to `main.py` (or configure a `.env` file).

## Usage
- **Sync Items** - Creates a local database for referencing GW2 items, recipes, and currencies: `python main.py --sync`
- **Start Tracker** - Runs an API scraper on the Black Lion Market to gather data on current listings: `python main.py --track`
