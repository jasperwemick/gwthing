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
        super().__init__(fig)
        self.setParent(parent)
        self.axes = fig.add_subplot(111)
        self.axes.set_facecolor('#1e1e1e')
        self.axes.tick_params(colors='white')
        self.axes.set_title('Market Data', color='white')
        fig.tight_layout(pad=0)
        self.current_view = "traction"

    def plot_data(self, history_data, item_id, view_type="traction"):
        self.axes.clear()
        if not history_data:
            self.axes.text(0.5, 0.5, "No data available", ha='center')
            self.draw()
            return
        # Extract data based on requested view
        # history_data is a list of tuples/dicts: (timestamp, buy_price, buy_qty, num_buyers, sell_price, sell_qty, num_sellers, buyers_delta, sellers_delta, buy_qty_delta, sell_qty_delta)
        # Note: Order depends on DB query result. Assume correct order based on query.
        
        times = [d[11] for d in history_data] # timestamp is index 11
        
        if view_type == "buy_vs_sell_qty":
            buys = [d[2] for d in history_data] # buy_quantity
            sells = [d[5] for d in history_data] # sell_quantity
            label_b, label_s = "Buy Qty", "Sell Qty"
        elif view_type == "high_buy_low_sell":
            buys = [d[1] for d in history_data] # buy_price
            sells = [d[4] for d in history_data] # sell_price
            label_b, label_s = "High Buy", "Low Sell"
        elif view_type == "buyers_vs_sellers":
            buys = [d[3] for d in history_data] # num_buyers
            sells = [d[6] for d in history_data] # num_sellers
            label_b, label_s = "Buyers", "Sellers"
        else: # traction
            buys = [d[7] for d in history_data] # buyers_delta
            sells = [d[8] for d in history_data] # sellers_delta
            label_b, label_s = "Buyer Delta", "Seller Delta"
        self.axes.plot(times, buys, label=label_b, color='#4caf50')
        self.axes.plot(times, sells, label=label_s, color='#f44336')
        self.axes.set_ylabel('Value', color='white')
        self.axes.set_xlabel('Time', color='white')
        self.axes.set_title(f"View: {view_type}", color='white')
        self.axes.legend()
        self.draw()

class MarketDashboard(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("GW2 Market Tracker - Pro Dashboard")
        self.resize(1400, 900)

        self.db = Database(db_path="data/gw2_market.db")
        self.client = GW2Client(os.getenv("API_KEY", ""))
        self.item_page = 0
        
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
        
        self.item_table = QTableWidget(0, 5)
        self.item_table.setHorizontalHeaderLabels(["ID", "Name", "Type", "Traction", "Demand"])
        self.item_table.setColumnHidden(0, True)
        self.item_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.item_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.item_table.itemClicked.connect(self.on_item_selected)
        left_layout.addWidget(self.item_table)

        pagination_layout = QHBoxLayout()
        self.prev_button = QPushButton("« Previous")
        self.prev_button.clicked.connect(self.load_item_list)
        self.next_button = QPushButton("Next »")
        self.next_button.clicked.connect(self.load_item_list)
        
        pagination_layout.addWidget(self.prev_button)
        pagination_layout.addWidget(self.next_button)
        left_layout.addLayout(pagination_layout)
        
        right_panel = QFrame()
        right_panel.setFrameStyle(QFrame.Shape.StyledPanel)
        right_layout = QVBoxLayout(right_panel)

        graph_container = QFrame()
        graph_layout = QVBoxLayout(graph_container)
        
        btn_layout = QHBoxLayout()
        views = ["traction", "buy_vs_sell_qty", "high_buy_low_sell", "buyers_vs_sellers"]
        for v in views:
            btn = QPushButton(v.replace('_', ' ').title())
            btn.clicked.connect(lambda checked, view=v: self.update_graph_view(view))
            btn_layout.addWidget(btn)
        
        graph_layout.addLayout(btn_layout)

        self.canvas = MplCanvas(right_panel)
        right_layout.addWidget(self.canvas, stretch=2)
        
        self.ingredients_label = QLabel("Recipe Tree:")
        self.ingredients_label.setStyleSheet("font-weight: bold; color: white;")
        right_layout.addWidget(self.ingredients_label)
        
        self.recipe_tree_container = QFrame()
        self.recipe_tree_layout = QVBoxLayout(self.recipe_tree_container)
        right_layout.addWidget(self.recipe_tree_container)
        
        self.tx_label = QLabel("Recent User Transactions:")
        self.tx_label.setStyleSheet("font-weight: bold; color: white;")
        right_layout.addWidget(self.tx_label)
        
        self.tx_list = QTextEdit()
        self.tx_list.setReadOnly(True)
        right_layout.addWidget(self.tx_list)
        
        self.splitter.addWidget(left_panel)
        self.splitter.addWidget(right_panel)
        main_layout.addWidget(self.splitter)

    def update_graph_view(self, view_type):
        if hasattr(self, '_last_history') and self._last_history:
            self.canvas.plot_data(self._last_history, self._last_selected_id, view_type)

    def load_item_list(self):
        item_type = self.type_filter.currentText()
        search_text = self.search_bar.text()
        
        query = """
            SELECT 
                i.id,
                i.name, 
                i.type,
                t.current_traction, 
                t.demand_ratio
            FROM items i
            LEFT JOIN (
                SELECT 
                    item_id, 
                    (buyers_delta + sellers_delta) as current_traction, 
                    CAST(buy_quantity_delta AS FLOAT) / NULLIF(sell_quantity_delta, 0) as demand_ratio
                FROM (
                    SELECT *, 
                        ROW_NUMBER() OVER (PARTITION BY item_id ORDER BY timestamp DESC) as rn
                    FROM price_history
                ) sub
                WHERE rn = 1
            ) t ON i.id = t.item_id
        """

        if item_type != 'All': query += f" WHERE i.type = {item_type}"
        else : query += " WHERE 1 = 1"
        
        if search_text:
            query += f" AND i.name LIKE '%{search_text}%'"

        query += f" ORDER BY t.current_traction DESC LIMIT {50} OFFSET {self.item_page * 50}"

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
            self.item_table.setItem(idx, 3, QTableWidgetItem(str(row[3]) if row[3] else "0.0"))
            self.item_table.setItem(idx, 4, QTableWidgetItem(str(row[4]) if row[4] else "0.0"))

    def on_item_selected(self, index):
        item_id = int(self.item_table.item(index, 0).text())
        self._last_selected_id = item_id
        self.update_display(item_id)

    def update_display(self, item_id):
        cursor = self.db.conn.cursor()
        # Fetch history for the graph
        cursor.execute("SELECT * FROM price_history WHERE item_id = ? ORDER BY timestamp ASC", (item_id,))
        self._last_history = cursor.fetchall()
        
        # Initial graph plot
        self.canvas.plot_data(self._last_history, item_id, "traction")
        
        # Recipe Tree Logic
        for i in reversed(range(self.recipe_tree_layout.count())): 
            widget = self.recipe_tree_layout.item(i).widget()
            if widget: widget.deleteLater()
            
        cursor.execute("SELECT * FROM recipes WHERE output_item_id = ?", (item_id,))
        recipes = cursor.fetchall()
        
        for r in recipes:
            # logic to build tree...
            pass
        # Transactions
        raw_tx = self.client.get_transactions(second_level="current", third_level="sells")
        if raw_tx:
            # Sort by Most Profitable Flip
            raw_tx.sort(key=lambda x: x.get('profit', 0), reverse=True)
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