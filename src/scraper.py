from client import GW2Client
from models import Currency, Item, Recipe
from database import Database
import logging
import os
import time
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

def sync_all_items(api_key: str):
    client = GW2Client(api_key)
    db = Database()
    
    logger.info("Fetching all items from GW2 API...")
    
    page = 0
    while True:
        raw_items = client.get_items(page=page)
        if not raw_items:
            break
            
        items_to_upsert = []
        for raw in raw_items:
            if raw.get('text') is not None: continue
            
            # Ensure 'details' is a dict even if missing from API
            details = raw.get('details')
            if details is None:
                details = {}
                
            items_to_upsert.append(Item(
                id=raw['id'],
                name=raw['name'],
                type=raw['type'],
                rarity=raw['rarity'],
                level=raw['level'],
                vendor_value=raw['vendor_value'],
                description=raw.get('description'),
                flags=raw.get('flags', []),
                details=details
            ))
        
        if items_to_upsert:
            db.upsert_items(items_to_upsert)
            logger.info(f"Successfully synced {len(items_to_upsert)} items (Page {page}).")
        
        page += 1
        time.sleep(1) # Small delay to be polite to API

def sync_all_currencies(api_key: str):
    client = GW2Client(api_key)
    db = Database()
    
    logger.info("Fetching all currencies from GW2 API...")
    
    page = 0
    while True:
        raw_currencies = client.get_currencies(page=page)
        if not raw_currencies:
            break
            
        currencies_to_upsert = []
        for raw in raw_currencies:
            if raw.get('text') is not None: continue
                
            currencies_to_upsert.append(Currency(
                id=raw['id'],
                name=raw['name'],
                description=raw.get('description'),
            ))
        
        if currencies_to_upsert:
            db.upsert_currencies(currencies_to_upsert)
            logger.info(f"Successfully synced {len(currencies_to_upsert)} currencies (Page {page}).")
        
        page += 1
        time.sleep(1)


def sync_all_recipes(api_key: str):
    client = GW2Client(api_key)
    db = Database()
    
    logger.info("Fetching all recipes from GW2 API...")
    
    page = 0
    while True:
        raw_recipes = client.get_recipes(page=page)
        if not raw_recipes:
            break
            
        recipes_to_upsert = []
        for raw in raw_recipes:
            if raw.get('text') is not None: continue

            item_ing = [i for i in raw.get('ingredients', []) if i['type'] == "Item"]
            currency_ing = [i for i in raw.get('ingredients', []) if i['type'] == "Currency"]
            
            recipes_to_upsert.append(Recipe(
                id=raw['id'],
                type=raw['type'],
                output_item_id=raw['output_item_id'],
                output_item_count=raw['output_item_count'],
                time_to_craft_ms=raw['time_to_craft_ms'],
                disciplines=raw.get('disciplines', []),
                min_rating=raw['min_rating'],
                item_ingredients=item_ing,
                currency_ingredients=currency_ing
            ))
        
        if recipes_to_upsert:
            db.upsert_recipes(recipes_to_upsert)
            logger.info(f"Successfully synced {len(recipes_to_upsert)} recipes (Page {page}).")
        
        page += 1
        time.sleep(1) # Small delay to be polite to API

if __name__ == "__main__":
    KEY = os.getenv("API_KEY")
    # sync_all_items(KEY)
    # sync_all_currencies(KEY)
    sync_all_recipes(KEY)
