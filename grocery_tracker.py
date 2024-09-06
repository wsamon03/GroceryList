import os
import sys
import sqlite3  # Add this line
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QListWidget, QComboBox, QLabel, QSizePolicy, QListWidgetItem, QCheckBox, QCompleter, QStyle, QStackedWidget, QTreeWidget, QTreeWidgetItem
from PyQt6.QtGui import QPainter, QColor, QPen, QPixmap, QIcon
from PyQt6.QtCore import Qt, QRect, QStringListModel, QSize

from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPen, QPixmap
from PyQt6.QtCore import Qt, QPoint

class DrawingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.drawing = False
        self.last_point = QPoint()
        self.pixmap = QPixmap(self.size())
        self.pixmap.fill(QColor(255, 192, 203, 25))  # Light pink with 90% transparency

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.pixmap)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = True
            self.last_point = event.position().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton and self.drawing:
            painter = QPainter(self.pixmap)
            painter.setPen(QPen(Qt.GlobalColor.black, 3, Qt.PenStyle.SolidLine))
            painter.drawLine(self.last_point, event.position().toPoint())
            self.last_point = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = False

    def clear(self):
        self.pixmap.fill(QColor(255, 192, 203, 25))  # Light pink with 90% transparency
        self.update()

    def get_image(self):
        return self.pixmap

    def resizeEvent(self, event):
        super().resizeEvent(event)
        new_pixmap = QPixmap(self.size())
        new_pixmap.fill(QColor(255, 192, 203, 25))  # Light pink with 90% transparency
        painter = QPainter(new_pixmap)
        painter.drawPixmap(0, 0, self.pixmap)
        self.pixmap = new_pixmap

class GroceryTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Grocery Tracker")
        self.setGeometry(100, 100, 800, 600)
        self.init_ui()
        self.init_db()
        self.setup_autocomplete()  # Add this line
        self.current_view = 'normal'  # Add this line

    def create_plus_icon(self, size):
        pixmap = QPixmap(size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Set up the pen for drawing
        pen = QPen(QColor(0, 200, 0))  # Green color
        pen.setWidth(2)
        painter.setPen(pen)
        
        # Draw the plus sign
        painter.drawLine(size.width() // 2, 5, size.width() // 2, size.height() - 5)
        painter.drawLine(5, size.height() // 2, size.width() - 5, size.height() // 2)
        
        painter.end()
        return QIcon(pixmap)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Input fields
        input_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Item Name")
        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText("Quantity")
        self.category_input = QComboBox()
        self.category_input.addItems(["Fruits", "Vegetables", "Dairy", "Meat", "Grains", "Other"])
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Location")
        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("Price")

        input_layout.addWidget(self.name_input)
        input_layout.addWidget(self.quantity_input)
        input_layout.addWidget(self.category_input)
        input_layout.addWidget(self.location_input)
        input_layout.addWidget(self.price_input)

        # Buttons
        button_layout = QHBoxLayout()
        
        # Define icon_size here
        icon_size = QSize(32, 32)
        
        # Update the Add Item button with custom plus icon
        add_button = QPushButton()
        add_icon = self.create_plus_icon(icon_size)
        add_button.setIcon(add_icon)
        add_button.setIconSize(icon_size)
        add_button.setFixedSize(icon_size)
        add_button.clicked.connect(self.add_item)
        add_button.setToolTip("Add To List")

        # Update the Clear Drawing button with the dialog cancel icon
        clear_button = QPushButton()
        clear_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton)
        clear_button.setIcon(clear_icon)
        clear_button.setIconSize(icon_size)
        clear_button.setFixedSize(icon_size)
        clear_button.clicked.connect(self.clear_drawing)
        clear_button.setToolTip("Erase handwriting")

        # Update the Recognize Text button
        recognize_button = QPushButton()
        recognize_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)
        recognize_button.setIcon(recognize_icon)
        recognize_button.setIconSize(icon_size)
        recognize_button.setFixedSize(icon_size)
        recognize_button.clicked.connect(self.recognize_text)
        recognize_button.setToolTip("Recognize Text")
        
        # Create the remove button with a standard delete icon
        remove_button = QPushButton()
        remove_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogDiscardButton)
        icon_size = QSize(32, 32)
        remove_button.setIcon(remove_icon)
        remove_button.setIconSize(icon_size)
        remove_button.setFixedSize(icon_size)
        remove_button.clicked.connect(self.remove_item)
        remove_button.setToolTip("Remove selected items")

        button_layout.addWidget(add_button)
        button_layout.addWidget(clear_button)
        button_layout.addWidget(recognize_button)
        button_layout.addWidget(remove_button)

        # Replace the existing container setup with this:
        self.container = QWidget()
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        self.stacked_widget = QStackedWidget()
        self.item_list = QListWidget()
        self.item_list.itemClicked.connect(self.populate_item_info)
        self.item_list.setStyleSheet("QListWidget::item { border-bottom: 1px solid #ddd; }")

        self.category_tree = QTreeWidget()
        self.category_tree.setHeaderHidden(True)
        self.category_tree.itemClicked.connect(self.populate_item_info_from_tree)

        self.location_tree = QTreeWidget()  # Add this line
        self.location_tree.setHeaderHidden(True)  # Add this line
        self.location_tree.itemClicked.connect(self.populate_item_info_from_tree)  # Add this line

        self.stacked_widget.addWidget(self.item_list)
        self.stacked_widget.addWidget(self.category_tree)
        self.stacked_widget.addWidget(self.location_tree)  # Add this line

        container_layout.addWidget(self.stacked_widget)

        # Add toggle button
        self.toggle_view_button = QPushButton("Toggle View")
        self.toggle_view_button.clicked.connect(self.toggle_view)
        button_layout.addWidget(self.toggle_view_button)

        self.drawing_widget = DrawingWidget()

        # Set size policy to expand
        self.container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Add widgets to main layout
        layout.addLayout(input_layout)
        layout.addLayout(button_layout)
        layout.addWidget(self.container)

        # Set up the drawing widget to overlay the list
        self.drawing_widget.setParent(self.container)
        self.drawing_widget.raise_()

        # Connect the name_input's textChanged signal to load_item_info
        self.name_input.textChanged.connect(self.load_item_info)

    def init_db(self):
        self.conn = sqlite3.connect('grocery_items.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS items
            (name TEXT PRIMARY KEY, category TEXT, location TEXT, price REAL)
        ''')
        self.conn.commit()

    def setup_autocomplete(self):
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.name_input.setCompleter(self.completer)
        self.update_autocomplete_list()

    def update_autocomplete_list(self):
        self.cursor.execute("SELECT name FROM items")
        items = [row[0] for row in self.cursor.fetchall()]
        model = QStringListModel(items)
        self.completer.setModel(model)

    def toggle_view(self):
        if self.current_view == 'normal':
            self.current_view = 'category'
            self.stacked_widget.setCurrentWidget(self.category_tree)
            self.update_category_tree()
        elif self.current_view == 'category':
            self.current_view = 'location'
            self.stacked_widget.setCurrentWidget(self.location_tree)
            self.update_location_tree()
        else:
            self.current_view = 'normal'
            self.stacked_widget.setCurrentWidget(self.item_list)

    def update_category_tree(self):
        self.category_tree.clear()
        categories = {}

        for i in range(self.item_list.count()):
            item = self.item_list.item(i)
            widget = self.item_list.itemWidget(item)
            if widget is None:
                continue

            label = widget.findChild(QLabel)
            if label:
                item_text = label.text()
                name, details = item_text.split(' - ', 1)
                quantity = details.split(', ')[0].split(': ')[1]
                category = details.split(', ')[1].split(': ')[1]
                location = details.split(', ')[2].split(': ')[1]

                if category not in categories:
                    categories[category] = []
                categories[category].append(f"{name} - Qty: {quantity}, Location: {location}")

        for category, items in categories.items():
            category_item = QTreeWidgetItem(self.category_tree, [category])
            category_item.setExpanded(True)
            font = category_item.font(0)
            font.setBold(True)
            font.setPointSize(12)
            category_item.setFont(0, font)

            for item in items:
                QTreeWidgetItem(category_item, [item])

    def update_location_tree(self):
        self.location_tree.clear()
        locations = {}

        for i in range(self.item_list.count()):
            item = self.item_list.item(i)
            widget = self.item_list.itemWidget(item)
            if widget is None:
                continue

            label = widget.findChild(QLabel)
            if label:
                item_text = label.text()
                name, details = item_text.split(' - ', 1)
                quantity = details.split(', ')[0].split(': ')[1]
                category = details.split(', ')[1].split(': ')[1]
                location = details.split(', ')[2].split(': ')[1]

                if location not in locations:
                    locations[location] = []
                locations[location].append(f"{name} - Qty: {quantity}, Category: {category}")

        for location, items in locations.items():
            location_item = QTreeWidgetItem(self.location_tree, [location])
            location_item.setExpanded(True)
            font = location_item.font(0)
            font.setBold(True)
            font.setPointSize(12)
            location_item.setFont(0, font)

            for item in items:
                QTreeWidgetItem(location_item, [item])

    def add_item(self):
        name = self.name_input.text()
        quantity = self.quantity_input.text()
        category = self.category_input.currentText()
        location = self.location_input.text()
        price = self.price_input.text()

        if name and quantity:
            item_text = f"{name} - Qty: {quantity}, Category: {category}, Location: {location}, Price: ${price}"
            
            # Create a list item first
            list_item = QListWidgetItem(self.item_list)
            
            # Create a custom widget for the list item
            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(5, 2, 5, 2)
            
            # Add the item text
            item_label = QLabel(item_text)
            item_layout.addWidget(item_label, stretch=1)
            
            # Add the checkbox
            checkbox = QCheckBox()
            checkbox.stateChanged.connect(lambda state, item=list_item: self.checkbox_state_changed(state, item))
            item_layout.addWidget(checkbox)
            
            # Set the custom widget for the list item
            list_item.setSizeHint(item_widget.sizeHint())
            self.item_list.setItemWidget(list_item, item_widget)

            # Save to database (excluding quantity)
            self.cursor.execute('''
                INSERT OR REPLACE INTO items (name, category, location, price)
                VALUES (?, ?, ?, ?)
            ''', (name, category, location, float(price) if price else 0))
            self.conn.commit()

            # Clear input fields
            self.name_input.clear()
            self.quantity_input.clear()
            self.location_input.clear()
            self.price_input.clear()

            # Clear the drawing
            self.drawing_widget.clear()

            self.update_autocomplete_list()  # Add this line
            self.update_category_tree()  # Add this line
            self.update_location_tree()  # Add this line

    def checkbox_state_changed(self, state, item):
        if state == Qt.CheckState.Checked.value:
            self.item_list.setCurrentItem(item)
            self.populate_item_info(item)
        else:
            self.item_list.setCurrentItem(None)
            self.clear_input_fields()

    def clear_input_fields(self):
        self.name_input.clear()
        self.quantity_input.clear()
        self.category_input.setCurrentIndex(0)
        self.location_input.clear()
        self.price_input.clear()

    def recognize_text(self):
        # Save the drawing as an image file
        self.drawing_widget.get_image().save("temp_drawing.png")

        # Load Google API key from environment variable
        google_api_key = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')

        # Use Google Cloud Vision API to recognize text
        client = vision.ImageAnnotatorClient.from_service_account_json(google_api_key)
        with open("temp_drawing.png", "rb") as image_file:
            content = image_file.read()
        image = vision.Image(content=content)
        response = client.text_detection(image=image)
        texts = response.text_annotations

        if texts:
            recognized_text = texts[0].description.strip()
            # Check if the text ends with a number
            words = recognized_text.split()
            if words and words[-1].isdigit():
                quantity = words.pop()  # Remove and store the last word (number)
                name = ' '.join(words)  # Join the remaining words
                self.name_input.setText(name)
                self.quantity_input.setText(quantity)
            else:
                self.name_input.setText(recognized_text)
            
            # The load_item_info method will be called automatically due to the textChanged signal connection

    def load_item_info(self, name):
        self.cursor.execute("SELECT category, location, price FROM items WHERE name = ?", (name,))
        result = self.cursor.fetchone()
        if result:
            category, location, price = result
            self.category_input.setCurrentText(category)
            self.location_input.setText(location)
            self.price_input.setText(str(price))
        else:
            # Clear the fields if the item is not found in the database
            self.category_input.setCurrentIndex(0)  # Set to the first category
            self.location_input.clear()
            self.price_input.clear()

    def clear_drawing(self):
        self.drawing_widget.clear()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'drawing_widget'):
            list_rect = self.stacked_widget.geometry()
            checkbox_width = 30  # Adjust this value based on your checkbox width
            self.drawing_widget.setGeometry(list_rect.x(), list_rect.y(), 
                                            list_rect.width() - checkbox_width, list_rect.height())

    def closeEvent(self, event):
        self.conn.close()
        super().closeEvent(event)

    def remove_item(self):
        items_to_remove = []
        for i in range(self.item_list.count()):
            item = self.item_list.item(i)
            widget = self.item_list.itemWidget(item)
            if widget is None:
                continue  # Skip this item if no widget is associated
            
            checkbox = widget.findChild(QCheckBox)
            if checkbox and checkbox.isChecked():
                label = widget.findChild(QLabel)
                if label:
                    item_text = label.text()
                    name = item_text.split(' - ')[0]  # Extract the item name
                    items_to_remove.append((i, name))
        
        # Remove items in reverse order to avoid index issues
        for index, name in reversed(items_to_remove):
            self.item_list.takeItem(index)
            
            # Remove from the database
            self.cursor.execute("DELETE FROM items WHERE name = ?", (name,))
        
        self.conn.commit()
        self.update_autocomplete_list()  # Add this line
        self.update_category_tree()  # Add this line
        self.update_location_tree()  # Add this line
        self.clear_input_fields()

    def populate_item_info(self, item):
        widget = self.item_list.itemWidget(item)
        item_text = widget.findChild(QLabel).text()
        
        # Extract quantity, category, location, and price from the item text
        details = item_text.split(' - ')[1].split(', ')
        quantity = details[0].split(': ')[1]
        category = details[1].split(': ')[1]
        location = details[2].split(': ')[1]
        price = details[3].split(': $')[1]

        # Populate input fields
        self.name_input.setText(item_text.split(' - ')[0])
        self.quantity_input.setText(quantity)
        self.category_input.setCurrentText(category)
        self.location_input.setText(location)
        self.price_input.setText(price)

    def populate_item_info_from_tree(self, item, column):
        if item.parent() is None:
            return  # This is a category or location item, not an actual grocery item

        item_text = item.text(0)
        name, details = item_text.split(' - ', 1)
        quantity = details.split(', ')[0].split(': ')[1]

        if self.current_view == 'category':
            category = item.parent().text(0)
            self.cursor.execute("SELECT location, price FROM items WHERE name = ?", (name,))
            result = self.cursor.fetchone()
            location, price = result if result else ("", "")
        else:  # location view
            category = details.split(', ')[1].split(': ')[1]
            location = item.parent().text(0)
            self.cursor.execute("SELECT price FROM items WHERE name = ?", (name,))
            result = self.cursor.fetchone()
            price = result[0] if result else ""

        # Populate input fields
        self.name_input.setText(name)
        self.quantity_input.setText(quantity)
        self.category_input.setCurrentText(category)
        self.location_input.setText(location)
        self.price_input.setText(str(price))

    def clear_input_fields(self):
        self.name_input.clear()
        self.quantity_input.clear()
        self.category_input.setCurrentIndex(0)
        self.location_input.clear()
        self.price_input.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    tracker = GroceryTracker()
    tracker.show()
    sys.exit(app.exec())