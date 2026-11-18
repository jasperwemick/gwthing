from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class Item:
    id: int
    name: str
    type: str
    rarity: str
    level: int
    vendor_value: int
    description: Optional[str] = None
    flags: List[str] = field(default_factory=list)
    details: Dict = field(default_factory=dict)

@dataclass
class ArmorDetails:
    item_id: int
    type: str
    weight_class: str

@dataclass
class BagDetails:
    item_id: int
    size: int

@dataclass
class ConsumableDetails:
    item_id: int
    type: str
    description: Optional[str] = None
    duration_ms: Optional[int] = None
    unlock_type: Optional[str] = None

@dataclass
class ContainerDetails:
    item_id: int
    type: str

@dataclass
class GatheringDetails:
    item_id: int
    type: str

@dataclass
class GizmoDetails:
    item_id: int
    type: str

@dataclass
class TrinketDetails:
    item_id: int
    type: str

@dataclass
class UpgradeComponentDetails:
    item_id: int
    type: str

@dataclass
class WeaponDetails:
    item_id: int
    type: str
    damage_type: str

@dataclass
class Currency:
    id : int
    name : str
    description : str

@dataclass
class ItemRecipeIngredient:
    item_id : int
    count : int

@dataclass
class CurrencyRecipeIngredient:
    currency_id : int
    count : int

@dataclass
class Recipe:
    id : int
    type : str
    output_item_id : int
    output_item_count : int
    time_to_craft_ms : int
    min_rating : int
    disciplines : List[str] = field(default_factory=list)
    item_ingredients : List[ItemRecipeIngredient] = field(default_factory=list)
    currency_ingredients : List[CurrencyRecipeIngredient] = field(default_factory=list)

@dataclass
class PriceEntry:
    id: int
    buy_price: int
    buy_quantity: int
    num_buyers : int
    sell_price: int
    sell_quantity: int
    num_sellers : int
    buyers_delta : int
    sellers_delta : int
    buy_quantity_delta : int
    sell_quantity_delta : int
    timestamp: datetime
