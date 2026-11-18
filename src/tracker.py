from typing import List, Dict, Any
import time
import logging
from datetime import datetime
import os
from dotenv import load_dotenv
from functools import reduce
import sys

import requests

from client import GW2Client
from models import PriceEntry
from database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

class MarketTracker:
    def __init__(self, api_key: str):
        self.client = GW2Client(api_key)
        self.db = Database()

    # def sync_active_listings(self):
    #     """Update the local record of the user's current listings."""
    #     logger.info("Syncing active listings...")
    #     # This would ideally call /v2/commerce/transactions/current/sells
    #     # and update the active_listings table.
    #     raw_transactions = self.client.get_transactions(second_level="current", third_level="sells")
        
    #     self.db.clear_active_listings()
    #     for tx in raw_transactions:
    #         self.db.conn.execute(
    #             "INSERT INTO active_listings (listing_id, item_id, unit_price, quantity, listing_type) \
    #              VALUES (?, ?, ?, ?, ?)",
    #             (tx['id'], tx['item_id'], tx['price'], tx['quantity'], 'sell')
    #         )
    #     self.db.conn.commit()

    def update_prices_and_traction(self):
        """Fetch prices, update history, and calculate traction."""

        # Remove prices from a week ago so ssd doesn't explode
        self.db.cleanup_old_prices()

        # query = """
        #     SELECT 
        #         item_id,
        #         timestamp,
        #         num_sellers - LAG(num_sellers) OVER (ORDER BY timestamp) as sellers_delta,
        #         num_buyers - LAG(num_buyers) OVER (ORDER BY timestamp) as buyers_delta
        #     FROM price_history
        #     ORDER BY timestamp ASC
        # """

        query = """
            SELECT * FROM (
                SELECT *, 
                    ROW_NUMBER() OVER (PARTITION BY item_id ORDER BY timestamp DESC) as rn
                FROM price_history
            ) t
            WHERE rn = 1
        """

        cursor = self.db.conn.cursor()
        cursor.execute(query)
        price_list = [ PriceEntry(*(row[1:-1])) for row in cursor.fetchall() ]
        prev_prices : dict[int, PriceEntry] = { ph.id : ph for ph in price_list }

        page : int = 0
        price_entries : list[PriceEntry] = []

        while True:
            item_ids = self.db.get_item_ids(limit=100, offset=page)
            if not item_ids:
                break

            logger.info(f"Fetching listings for {len(item_ids)} items...")
            raw_prices = self.client.get_listings(ids=item_ids)
            if not raw_prices:
                page += 1
                time.sleep(1)
                continue
            
            # Get the most recent traction records to calculate deltas
            # For simplicity, we compare against the last hour's scan
            
            for data in raw_prices:

                if data.get('text') is not None: continue

                item_id : int = data['id']
                buy : list[dict[str, int]] = data.get('buys', [])
                flat_buys : dict[str, int] = {}
                for d in buy:
                    for k, v in d.items():
                        if k == 'unit_price': 
                            flat_buys[k] = v if v > flat_buys.get(k, 0) else flat_buys.get(k, 0)
                        else: 
                            flat_buys[k] = flat_buys.get(k, 0) + v

                sell : list[dict[str, int]] = data.get('sells', [])
                flat_sales : dict[str, int] = {}
                for d in sell:
                    for k, v in d.items():
                        if k == 'unit_price': 
                            flat_sales[k] = v if v < flat_sales.get(k, sys.maxsize) else flat_sales.get(k, sys.maxsize)
                        else: 
                            flat_sales[k] = flat_sales.get(k, 0) + v


                price_entries.append(PriceEntry(
                    id=item_id,
                    buy_price=flat_buys.get('unit_price', 0),
                    buy_quantity=flat_buys.get('quantity', 0),
                    num_buyers=flat_buys.get('listings', 0),
                    sell_price=flat_sales.get('unit_price', 0),
                    sell_quantity=flat_sales.get('quantity', 0),
                    num_sellers=flat_sales.get('listings', 0),
                    buyers_delta=flat_buys.get('listings', 0) - prev_prices[item_id].num_buyers if prev_prices.get(item_id, 0) else flat_buys.get('listings', 0),
                    sellers_delta=flat_sales.get('listings', 0) - prev_prices[item_id].num_sellers if prev_prices.get(item_id, 0) else flat_sales.get('listings', 0),
                    buy_quantity_delta=flat_buys.get('quantity', 0) - prev_prices[item_id].buy_quantity if prev_prices.get(item_id, 0) else flat_buys.get('quantity', 0),
                    sell_quantity_delta=flat_sales.get('quantity', 0) - prev_prices[item_id].sell_quantity if prev_prices.get(item_id, 0) else flat_sales.get('quantity', 0),
                    timestamp=datetime.now()
                ))

            page += 1
            time.sleep(1)

        self.db.record_price(price_entries)

        logger.info("Price update complete.")

    def check_undercuts(self):
        """Check if any active listings have a lower unit price in the market."""
        active_listings = self.db.get_active_listings()
        if not active_listings:
            return

        # Fetch current prices for these specific item_ids
        ids = [l['item_id'] for l in active_listings]
        current_prices = self.client.get_prices(ids=ids)
        price_map = {p['id']: p for p in current_prices}

        for listing in active_listings:
            market_price_data = price_map.get(listing['item_id'])
            if market_price_data:
                market_sell_price = float(market_price_data['sells'].get('unit_price', 0))
                if market_sell_price < listing['unit_price']:
                    logger.warning(f"UNDERCUT! Item {listing['item_id']} (Listing {listing['listing_id']}) "
                                   f"at {listing['unit_price']} is being sold for {market_sell_price}")

    def run_forever(self):
        logger.info("Starting automated tracker (hourly loop)...")
        while True:
            try:
                # self.sync_active_listings()
                self.update_prices_and_traction()
                # self.check_undercuts()
                logger.info("Cycle complete. Sleeping for 1 hour...")
                time.sleep(3600)
            except Exception as e:
                logger.error(f"Error in loop: {e}")
                time.sleep(60)

if __name__ == "__main__":
    KEY = os.getenv("API_KEY")
    tracker = MarketTracker(KEY)
    tracker.run_forever()
