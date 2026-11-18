import sys
import argparse
from src.scraper import sync_all_items
from src.tracker import MarketTracker

def main():
    parser = argparse.ArgumentParser(description="GW2 Black Lion Market Trading Tool")
    parser.add_argument("--sync", action="store_true", help="Sync all item data from the API")
    parser.add_argument("--track", action="store_true", help="Start the automated hourly price tracker")
    args = parser.parse_args()

    # In a real app, this should be loaded from a .env file or config.
    API_KEY = "YOUR_API_KEY"

    if args.sync:
        sync_all_items(API_KEY)
        print("Sync complete.")
    elif args.track:
        tracker = MarketTracker(API_KEY)
        tracker.run_forever()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
