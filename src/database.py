import os
import sqlite3
from typing import List, Optional, Dict, Any
from models import Currency, Item, PriceEntry, Recipe
from datetime import datetime

class Database:
    def __init__(self, db_path: str = "../data/gw2_market.db"):
        # Ensure the directory exists before connecting
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        # self.delete_table()
        self.create_tables()

    def delete_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            DROP TABLE IF EXISTS price_history
        ''')
        self.conn.commit()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        # Items
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY,
                name TEXT,
                type TEXT,
                rarity TEXT,
                level INTEGER,
                vendor_value INTEGER,
                description TEXT
            )
        ''')
        # Item flags
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS item_flags (
                item_id INTEGER,
                flag TEXT,
                PRIMARY KEY (item_id, flag),
                FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE CASCADE
            )
        ''')

        # Item type details
        # Armor
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS armor_details (
                item_id INTEGER PRIMARY KEY,
                type TEXT,
                weight_class TEXT,
                FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE CASCADE
            )
        ''')
        # Bags
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bag_details (
                item_id INTEGER PRIMARY KEY,
                size INTEGER,
                FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE CASCADE
            )
        ''')
        # Consumables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS consumable_details (
                item_id INTEGER PRIMARY KEY,
                type TEXT,
                description TEXT,
                duration_ms INTEGER,
                unlock_type TEXT,
                FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE CASCADE
            )
        ''')
        # Container
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS container_details (
                item_id INTEGER PRIMARY KEY,
                type TEXT,
                FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE CASCADE
            )
        ''')
        # Gathering
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gathering_details (
                item_id INTEGER PRIMARY KEY,
                type TEXT,
                FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE CASCADE
            )
        ''')
        # Gizmo
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gizmo_details (
                item_id INTEGER PRIMARY KEY,
                type TEXT,
                FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE CASCADE
            )
        ''')
        # Trinket
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trinket_details (
                item_id INTEGER PRIMARY KEY,
                type TEXT,
                FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE CASCADE
            )
        ''')
        # Upgrade Component
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS upgrade_component_details (
                item_id INTEGER PRIMARY KEY,
                type TEXT,
                FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE CASCADE
            )
        ''')
        # Weapons
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS weapon_details (
                item_id INTEGER PRIMARY KEY,
                type TEXT,
                damage_type TEXT,
                FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE CASCADE
            )
        ''')

        #Currencies
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS currencies (
                id INTEGER PRIMARY KEY,
                name TEXT,
                description TEXT
            )
        ''')

        #Recipes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY,
                type TEXT,
                output_item_id INTEGER,
                output_item_count INTEGER,
                time_to_craft_ms INTEGER,
                min_rating INTEGER
            )
        ''')
        # Recipe Disciplines
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recipe_disciplines (
                recipe_id INTEGER,
                discipline TEXT,
                PRIMARY KEY (recipe_id, discipline),
                FOREIGN KEY(recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            )
        ''')
        # Recipe Ingredients
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recipe_item_ingredients (
                recipe_id INTEGER,
                item_id INTEGER,
                count INTEGER,
                PRIMARY KEY (recipe_id, item_id),
                FOREIGN KEY(recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
                FOREIGN KEY(item_id) REFERENCES items(id)
            )
        ''') 
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recipe_currency_ingredients (
                recipe_id INTEGER,
                currency_id INTEGER,
                count INTEGER,
                PRIMARY KEY (recipe_id, currency_id),
                FOREIGN KEY(recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
                FOREIGN KEY(currency_id) REFERENCES currencies(id)
            )
        ''') 

        # Price History & Traction (Existing)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                buy_price INTEGER,
                buy_quantity INTEGER,
                num_buyers INTEGER,
                sell_price INTEGER,
                sell_quantity INTEGER,
                num_sellers INTEGER,
                buyers_delta INTEGER,
                sellers_delta INTEGER,
                buy_quantity_delta INTEGER, 
                sell_quantity_delta INTEGER,
                timestamp DATETIME,
                FOREIGN KEY(item_id) REFERENCES items(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS traction_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                demand_delta REAL,
                supply_delta REAL,
                timestamp DATETIME,
                FOREIGN KEY(item_id) REFERENCES items(id)
            )
        ''')
        self.conn.commit()

    # Insert into items database, on matching id update the item instead
    def upsert_items(self, items: List[Item]):
        cursor = self.conn.cursor()
        for item in items:
            # Insert core item
            cursor.execute('''
                INSERT INTO items (id, name, type, rarity, level, vendor_value, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    type=excluded.type,
                    rarity=excluded.rarity,
                    level=excluded.level,
                    vendor_value=excluded.vendor_value,
                    description=excluded.description
            ''', (item.id, item.name, item.type, item.rarity, item.level, item.vendor_value, item.description))

            # Handle Flags
            if item.flags:
                cursor.executemany('''
                    INSERT OR REPLACE INTO item_flags (item_id, flag)
                    VALUES (?, ?)
                ''', [(item.id, flag) for flag in item.flags])

            # Handle Type-Specific Details
            details = getattr(item, 'details', {})
            if not details:
                continue

            if item.type == "Armor":
                cursor.execute('''
                    INSERT OR REPLACE INTO armor_details (item_id, type, weight_class)
                    VALUES (?, ?, ?)
                ''', (item.id, details.get('type'), details.get('weight_class')))
            elif item.type == "Bag":
                cursor.execute('''
                    INSERT OR REPLACE INTO bag_details (item_id, size)
                    VALUES (?, ?)
                ''', (item.id, details.get('size')))
            elif item.type == "Consumable":
                cursor.execute('''
                    INSERT OR REPLACE INTO consumable_details (item_id, type, description, duration_ms, unlock_type)
                    VALUES (?, ?, ?, ?, ?)
                ''', (item.id, details.get('type'), details.get('description'), 
                      details.get('duration_ms'), details.get('unlock_type')))
            elif item.type == "Container":
                cursor.execute('''
                    INSERT OR REPLACE INTO container_details (item_id, type)
                    VALUES (?, ?)
                ''', (item.id, details.get('type')))
            elif item.type == "Gathering":
                cursor.execute('''
                    INSERT OR REPLACE INTO gathering_details (item_id, type)
                    VALUES (?, ?)
                ''', (item.id, details.get('type')))
            elif item.type == "Gizmo":
                cursor.execute('''
                    INSERT OR REPLACE INTO gizmo_details (item_id, type)
                    VALUES (?, ?)
                ''', (item.id, details.get('type')))
            elif item.type == "Trinket":
                cursor.execute('''
                    INSERT OR REPLACE INTO trinket_details (item_id, type)
                    VALUES (?, ?)
                ''', (item.id, details.get('type')))
            elif item.type == "UpgradeComponent":
                cursor.execute('''
                    INSERT OR REPLACE INTO upgrade_component_details (item_id, type)
                    VALUES (?, ?)
                ''', (item.id, details.get('type')))
            elif item.type == "Weapon":
                cursor.execute('''
                    INSERT OR REPLACE INTO weapon_details (item_id, type, damage_type)
                    VALUES (?, ?, ?)
                ''', (item.id, details.get('type'), details.get('damage_type')))

        self.conn.commit()

    def upsert_currencies(self, currencies: List[Currency]):
        cursor = self.conn.cursor()
        for currency in currencies:
            cursor.execute('''
                INSERT INTO currencies (id, name, description)
                VALUES (?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    description=excluded.description
            ''', (currency.id, currency.name, currency.description))

        self.conn.commit()


    # Insert into items database, on matching id update the item instead
    def upsert_recipes(self, recipes: List[Recipe]):
        cursor = self.conn.cursor()
        for recipe in recipes:
            cursor.execute('''
                INSERT INTO recipes (id, type, output_item_id, output_item_count, time_to_craft_ms, min_rating)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    type=excluded.type,
                    output_item_id=excluded.output_item_id,
                    output_item_count=excluded.output_item_count,
                    time_to_craft_ms=excluded.time_to_craft_ms,
                    min_rating=excluded.min_rating
            ''', (recipe.id, recipe.type, recipe.output_item_id, recipe.output_item_count, recipe.time_to_craft_ms, recipe.min_rating))

            # Handle Disciplines
            if recipe.disciplines:
                cursor.executemany('''
                    INSERT OR REPLACE INTO recipe_disciplines (recipe_id, discipline)
                    VALUES (?, ?)
                ''', [(recipe.id, discipline) for discipline in recipe.disciplines])

            # Handle Ingredients
            if recipe.item_ingredients:
                cursor.executemany('''
                    INSERT OR REPLACE INTO recipe_item_ingredients (recipe_id, item_id, count)
                    VALUES (?, ?, ?)
                ''', [(recipe.id, ingredient['id'], ingredient['count']) for ingredient in recipe.item_ingredients])
            
            if recipe.currency_ingredients:
                cursor.executemany('''
                    INSERT OR REPLACE INTO recipe_currency_ingredients (recipe_id, currency_id, count)
                    VALUES (?, ?, ?)
                ''', [(recipe.id, ingredient['id'], ingredient['count']) for ingredient in recipe.currency_ingredients])

        self.conn.commit()

    def record_price(self, price_entries: List[PriceEntry]):
        cursor = self.conn.cursor()
        cursor.executemany('''
            INSERT INTO price_history (
                item_id, buy_price, buy_quantity, num_buyers, 
                sell_price, sell_quantity, num_sellers, 
                buyers_delta, sellers_delta, buy_quantity_delta, sell_quantity_delta, 
                timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', [(price_entry.id, price_entry.buy_price, price_entry.buy_quantity, price_entry.num_buyers,
               price_entry.sell_price, price_entry.sell_quantity, price_entry.num_sellers,
               price_entry.buyers_delta, price_entry.sellers_delta, price_entry.buy_quantity_delta, price_entry.sell_quantity_delta,
               price_entry.timestamp) for price_entry in price_entries])
        self.conn.commit()

    def get_item_ids(self, limit: int = 50, offset: int = 0, filter: dict = {}) -> List[int]:
        item_type = filter.get('type')
        
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id FROM items 
            WHERE (type = ? OR ? IS NULL)
            LIMIT ?
            OFFSET ?
        ''', (item_type, item_type, limit, offset * limit))
        
        return [row[0] for row in cursor.fetchall()]
    
    def update_traction(self, item_id: int, demand_delta: float, supply_delta: float):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO traction_metrics (item_id, demand_delta, supply_delta, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (item_id, demand_delta, supply_delta, datetime.now()))
        self.conn.commit()

    def get_active_listings(self) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM active_listings")
        return [dict(row) for row in cursor.fetchall()]
    
    def clear_active_listings(self):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM active_listings")
        self.conn.commit()

    def cleanup_old_prices(self):
        cursor = self.conn.cursor()
        # Remove records older than 7 days
        cursor.execute('''
            DELETE FROM price_history 
            WHERE timestamp < datetime('now', '-7 days')
        ''')
        self.conn.commit()
        print("Cleaned up price history older than 7 days.")