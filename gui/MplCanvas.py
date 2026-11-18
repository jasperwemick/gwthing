import sys
import os
import logging
from typing import List, Dict, Any

src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))

if src_path not in sys.path:
    sys.path.append(src_path)

from database import Database
from client import GW2Client
from models import PriceEntry

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QLabel, QPushButton, QComboBox,
    QLineEdit, QSplitter, QFrame, QTextEdit, QHeaderView
)

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi, facecolor='#2b2b2b')
        fig.tight_layout(pad=0)
        super().__init__(fig)
        self.setParent(parent)
        self.axes = fig.add_subplot(111)
        self.axes.set_facecolor('#1e1e1e')
        self.axes.tick_params(colors='white')
        self.axes.set_title('Supply & Demand Over Time', color='white')


        
    def plot_data(self, history_data, buy_price, sell_price):
        self.axes.clear()
        if history_data:
            # history_data is a list of (timestamp, buy_price, sell_price)
            times = [d[0] for d in history_data]
            buys = [d[1] for d in history_data]
            sells = [d[2] for d in history_data]
            
            self.axes.plot(times, buys, label='Buy Price', color='#4caf50')
            self.axes.plot(times, sells, label='Sell Price', color='#f44336')
            self.axes.set_ylabel('Price', color='white')
            self.axes.set_xlabel('Time', color='white')
            self.axes.legend()
        
        self.axes.set_title(f"High Buy: {buy_price} | Low Sell: {sell_price}", color='white')
        self.draw()
class MarketDashboard(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("GW2 Market Tracker - Pro Dashboard")
        self.resize(1200, 800)
        
        self.db = Database()
        self.client = GW2Client(os.getenv("API_KEY", ""))
        
        self.setup_ui()
        self.load_item_list()

    def setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        header = QLabel("GW2 Market Tracker")
        header.setFont(QFont("Arial", pointSize=18, weight=1, italic=False))
        header.setStyleSheet("color: white; padding: 10px;")
        main_layout.addWidget(header)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        left_panel = QFrame()
        left_panel.setFrameStyle(QFrame.Shape.StyledPanel)
        left_layout = QVBoxLayout(left_panel)
        filter_layout = QHBoxLayout()
        self.type_filter = QComboBox()
        self.type_filter.addItems(["All", "Armor", "Bag", "Consumable", "Container", "Gathering", "Gizmo", "Trinket", "UpgradeComponent", "Weapon"])
        self.type_filter.currentTextChanged.connect(self.load_item_list)
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search items...")
        self.search_bar.textChanged.connect(self.load_item_list)
        
        filter_layout.addWidget(QLabel("Type:"))
        filter_layout.addWidget(self.type_filter)
        filter_layout.addWidget(self.search_bar)
        left_layout.addLayout(filter_layout)
        
        self.item_table = QTableWidget(0, 4)
        self.item_table.setHorizontalHeaderLabels(["ID", "Name", "Type", "Traction"])
        self.item_table.setColumnHidden(0, True)
        self.item_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.item_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.item_table.itemClicked.connect(self.on_item_selected)
        left_layout.addWidget(self.item_table)
        
        right_panel = QFrame()
        right_panel.setFrameStyle(QFrame.Shape.StyledPanel)
        right_layout = QVBoxLayout(right_panel)
        self.canvas = MplCanvas(right_panel)
        right_layout.addWidget(self.canvas, stretch=2)
        
        self.ingredients_label = QLabel("Ingredients:")
        self.ingredients_label.setStyleSheet("font-weight: bold; color: white;")
        right_layout.addWidget(self.ingredients_label)
        
        self.ingredients_box = QTextEdit()
        self.ingredients_box.setReadOnly(True)
        self.ingredients_box.setPlaceholderText("No recipe found.")
        right_layout.addWidget(self.ingredients_box)
        
        self.tx_label = QLabel("Recent User Transactions:")
        self.tx_label.setStyleSheet("font-weight: bold; color: white;")
        right_layout.addWidget(self.tx_label)
        
        self.tx_list = QTextEdit()
        self.tx_list.setReadOnly(True)
        self.tx_list.setPlaceholderText("Fetching transactions...")
        right_layout.addWidget(self.tx_list)
        
        self.splitter.addWidget(left_panel)
        self.splitter.addWidget(right_panel)
        main_layout.addWidget(self.splitter)

    def load_item_list(self):
        query = """
            SELECT i.id, i.name, i.type, 
                   (SELECT COUNT(*) FROM traction_metrics tm WHERE tm.item_id = i.id) as traction_count
            FROM items i
        """
        if self.type_filter.currentText() != "All":
            query += f" WHERE i.type = '{self.type_filter.currentText()}'"
        
        query += " ORDER BY traction_count DESC"
        
        search_text = self.search_bar.text()
        if search_text:
            query += f" AND i.name LIKE '%{search_text}%'"
            
        cursor = self.db.conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        
        self.item_table.setRowCount(0)
        for row in rows:
            idx = self.item_table.rowCount()
            self.item_table.insertRow(idx)
            self.item_table.setItem(idx, 0, QTableWidgetItem(str(row[0])))
            self.item_table.setItem(idx, 1, QTableWidgetItem(str(row[1])))
            self.item_table.setItem(idx, 2, QTableWidgetItem(str(row[2])))
            self.item_table.setItem(idx, 3, QTableWidgetItem(str(row[3])))

    def on_item_selected(self, index):
        item_id = int(self.item_table.item(index, 0).text())
        self.update_display(item_id)

    def update_display(self, item_id):
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT timestamp, buy_price, sell_price FROM price_history WHERE item_id = ? ORDER BY timestamp ASC", (item_id,))
        history = cursor.fetchall()
        
        buy_prices = [h[1] for h in history]
        sell_prices = [h[2] for h in history]
        high_buy = max(buy_prices) if buy_prices else 0
        low_sell = min(sell_prices) if sell_prices else 0
        
        self.canvas.plot_data(history, high_buy, low_sell)
        
        cursor.execute("SELECT * FROM recipes WHERE output_item_id = ?", (item_id,))
        recipe = cursor.fetchone()
        if recipe:
            cursor.execute("SELECT * FROM recipe_item_ingredients WHERE recipe_id = ?", (recipe[0],))
            items = cursor.fetchall()
            cursor.execute("SELECT * FROM recipe_currency_ingredients WHERE recipe_id = ?", (recipe[0],))
            currencies = cursor.fetchall()
            
            ingredients_str = ""
            for i in items:
                ingredients_str += f"- Item {i[1]} (x{i[2]})\n"
            for c in currencies:
                ingredients_str += f"- Currency {c[1]} (x{c[2]})\n"
            self.ingredients_box.setPlainText(ingredients_str)
        else:
            self.ingredients_box.setPlainText("No recipe available for this item.")
            
        raw_tx = self.client.get_transactions(second_level="current", third_level="sells")
        if raw_tx:
            tx_text = ""
            for tx in raw_tx[:10]:
                tx_text += f"ID: {tx['id']} | Item: {tx['item_id']} | Price: {tx['price']} | Qty: {tx['quantity']}\n"
            self.tx_list.setPlainText(tx_text)
        else:
            self.tx_list.setPlainText("No recent transactions.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MarketDashboard()
    window.show()
    sys.exit(app.exec())