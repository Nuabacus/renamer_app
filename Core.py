import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QPushButton, QShortcut, QHBoxLayout, QLabel, QSizePolicy, QSpacerItem, QMenu, QAction
from PyQt5.QtGui import QKeySequence, QTextCursor, QFont, QIcon, QPixmap, QFontDatabase
from PyQt5.QtCore import Qt, QEvent, QTimer, QPoint

class CustomTitleBar(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(5, 1, 9, 5)  # Adjust these numbers to change padding
        self.layout.setSpacing(15)  # Adjust this number to change spacing

        self.title = QLabel("")

        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.layout.addWidget(self.title)
        self.layout.addItem(spacer)

        self.start = QPoint(0, 0)
        self.pressing = False

    def mousePressEvent(self, event):
        self.start = event.globalPos()
        self.pressing = True

    def mouseMoveEvent(self, event):
        if self.pressing:
            end = event.globalPos()
            delta = end - self.start

            screen = QApplication.screens()[0].geometry()
            window = self.parent.frameGeometry()

            # Calculate the new position.
            new_left = window.left() + delta.x()
            new_right = window.right() + delta.x()
            new_top = window.top() + delta.y()
            new_bottom = window.bottom() + delta.y()

            # Adjust the new position to not exceed screen boundaries.
            if new_left < screen.left():
                delta.setX(delta.x() + screen.left() - new_left)
            if new_right > screen.right():
                delta.setX(delta.x() - new_right + screen.right())
            if new_top < screen.top():
                delta.setY(delta.y() + screen.top() - new_top)
            if new_bottom > screen.bottom():
                delta.setY(delta.y() - new_bottom + screen.bottom())

            self.parent.move(self.parent.pos() + delta)
            self.start = end

    def mouseReleaseEvent(self, QMouseEvent):
        self.pressing = False

    def contextMenuEvent(self, event):
        context_menu = QMenu(self)

        minimize_action = QAction("Minimize", self)
        minimize_action.triggered.connect(self.parent.showMinimized)
        context_menu.addAction(minimize_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.parent.close)
        context_menu.addAction(exit_action)

        context_menu.exec_(event.globalPos())

class TextEditor(QMainWindow):
    def __init__(self, parent=None):
        super(TextEditor, self).__init__(parent)
        self.setWindowFlag(Qt.FramelessWindowHint)  # Set the window to a frameless style
        self.setWindowTitle("Flip2Copy")
        self.setWindowIcon(QIcon())  # This line removes the icon from the title bar

        # Create and set the custom title bar
        self.title_bar = CustomTitleBar(self)
        self.setMenuWidget(self.title_bar)
        self.setMouseTracking(True)
        self.oldPos = self.pos()

        main_layout = QVBoxLayout()
        top_layout = QHBoxLayout()

        widget = QWidget()
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)

        main_layout.addLayout(top_layout)

        self.increase_font_button = QPushButton("+")
        self.increase_font_button.pressed.connect(self.start_increasing_font_size)
        self.increase_font_button.released.connect(self.stop_increasing_font_size)
        top_layout.addWidget(self.increase_font_button)

        self.decrease_font_button = QPushButton("-")
        self.decrease_font_button.pressed.connect(self.start_decreasing_font_size)
        self.decrease_font_button.released.connect(self.stop_decreasing_font_size)
        top_layout.addWidget(self.decrease_font_button)

        self.clipboard_toggle_button = QPushButton("=")
        self.clipboard_toggle_button.setCheckable(True)  # Make the button toggle-able
        self.clipboard_toggle_button.setChecked(False)  # Set initial state of the button
        self.clipboard_toggle_button.clicked.connect(self.toggle_clipboard_copying)
        top_layout.addWidget(self.clipboard_toggle_button)

        self.always_on_top_button = QPushButton("^")
        self.always_on_top_button.setCheckable(True)  # Make the button toggle-able
        self.always_on_top_button.clicked.connect(self.toggle_always_on_top)
        top_layout.addWidget(self.always_on_top_button)

        self.text_edit = SelectableTextEdit(parent_editor=self)
        self.text_edit.copy_to_clipboard = lambda: None
        main_layout.addWidget(self.text_edit)

        self.increment_shortcut = QShortcut(QKeySequence('Ctrl+Up'), self)
        self.increment_shortcut.activated.connect(self.text_edit.increment_value)
        self.decrement_shortcut = QShortcut(QKeySequence('Ctrl+Down'), self)
        self.decrement_shortcut.activated.connect(self.text_edit.decrement_value)

        self.timer = QTimer()
        self.timer.setInterval(1)  # adjust speed here
        self.timer.timeout.connect(self.increase_font_size)

        self.timer_decrease = QTimer()
        self.timer_decrease.setInterval(1)  # adjust speed here
        self.timer_decrease.timeout.connect(self.decrease_font_size)
        

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = event.globalPos()
            self.oldSize = self.size()

            # Determine which region of the window the click occurred in
            self.clickedRegion = self.getClickedRegion(event.pos())

    def getClickedRegion(self, pos):
        top_margin = 30
        side_margin = 10

        if pos.y() < top_margin and pos.x() < side_margin:
            return 'top_left_corner'
        elif pos.y() < top_margin and pos.x() > self.width() - side_margin:
            return 'top_right_corner'
        elif pos.y() > self.height() - side_margin and pos.x() < side_margin:
            return 'bottom_left_corner'
        elif pos.y() > self.height() - side_margin and pos.x() > self.width() - side_margin:
            return 'bottom_right_corner'
        elif pos.y() < top_margin:
            return 'title_bar'
        elif pos.x() < side_margin:
            return 'left_edge'
        elif pos.x() > self.width() - side_margin:
            return 'right_edge'
        elif pos.y() > self.height() - side_margin:
            return 'bottom_edge'
        else:
            return 'center'

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            delta = event.globalPos() - self.oldPos

            # Get screen size
            screen = QApplication.screens()[0].geometry()
            
            if self.clickedRegion == 'title_bar':
                self.move(self.pos() + delta)
            elif self.clickedRegion == 'left_edge':
                new_width = self.oldSize.width() - delta.x()
                if new_width > self.minimumWidth() and new_width + self.x() <= screen.right():
                    self.setGeometry(self.x() + delta.x(), self.y(), new_width, self.oldSize.height())
            elif self.clickedRegion == 'right_edge':
                new_width = self.oldSize.width() + delta.x()
                if new_width + self.x() <= screen.right():
                    self.setGeometry(self.x(), self.y(), new_width, self.oldSize.height())
            elif self.clickedRegion == 'bottom_edge':
                new_height = self.oldSize.height() + delta.y()
                if new_height + self.y() <= screen.bottom():
                    self.setGeometry(self.x(), self.y(), self.oldSize.width(), new_height)
            elif self.clickedRegion == 'top_left_corner':
                new_width = self.oldSize.width() - delta.x()
                new_height = self.oldSize.height() - delta.y()
                if new_width > self.minimumWidth() and new_width + self.x() <= screen.right() and new_height + self.y() <= screen.bottom():
                    self.setGeometry(self.x() + delta.x(), self.y() + delta.y(), new_width, new_height)
            elif self.clickedRegion == 'top_right_corner':
                new_width = self.oldSize.width() + delta.x()
                new_height = self.oldSize.height() - delta.y()
                if new_width + self.x() <= screen.right() and new_height + self.y() <= screen.bottom():
                    self.setGeometry(self.x(), self.y() + delta.y(), new_width, new_height)
            elif self.clickedRegion == 'bottom_left_corner':
                new_width = self.oldSize.width() - delta.x()
                new_height = self.oldSize.height() + delta.y()
                if new_width > self.minimumWidth() and new_width + self.x() <= screen.right() and new_height + self.y() <= screen.bottom():
                    self.setGeometry(self.x() + delta.x(), self.y(), new_width, new_height)
            elif self.clickedRegion == 'bottom_right_corner':
                new_width = self.oldSize.width() + delta.x()
                new_height = self.oldSize.height() + delta.y()
                if new_width + self.x() <= screen.right() and new_height + self.y() <= screen.bottom():
                    self.setGeometry(self.x(), self.y(), new_width, new_height)

            self.oldPos = event.globalPos()
            self.oldSize = self.size()

    def setCursorShape(self, pos):
        clickedRegion = self.getClickedRegion(pos)
        if clickedRegion in ['title_bar', 'center']:
            self.setCursor(Qt.ArrowCursor)
        elif clickedRegion in ['left_edge', 'right_edge']:
            self.setCursor(Qt.SizeHorCursor)
        elif clickedRegion in ['bottom_edge']:
            self.setCursor(Qt.SizeVerCursor)
        elif clickedRegion in ['top_left_corner', 'bottom_right_corner']:
            self.setCursor(Qt.SizeFDiagCursor)
        elif clickedRegion in ['top_right_corner', 'bottom_left_corner']:
            self.setCursor(Qt.SizeBDiagCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def start_increasing_font_size(self):
        self.timer.start(25)  # Font size delay

    def stop_increasing_font_size(self):
        self.timer.stop()

    def start_decreasing_font_size(self):
        self.timer_decrease.start(25)  # Font size delay

    def stop_decreasing_font_size(self):
        self.timer_decrease.stop()

    def toggle_clipboard_copying(self):
        if self.clipboard_toggle_button.isChecked():
            self.text_edit.copy_to_clipboard = self.copy_to_clipboard
        else:
            self.text_edit.copy_to_clipboard = lambda: None

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_edit.toPlainText())

    def toggle_always_on_top(self):
        if self.always_on_top_button.isChecked():
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        self.show()

    def increase_font_size(self):
        font = self.text_edit.font()
        font.setPointSize(font.pointSize() + 1)
        self.text_edit.setFont(font)

    def decrease_font_size(self):
        font = self.text_edit.font()
        font.setPointSize(max(1, font.pointSize() - 1))  # Ensure font size is at least 1
        self.text_edit.setFont(font)

class SelectableTextEdit(QTextEdit):
    def __init__(self, parent_editor=None, *args, **kwargs):
        super(SelectableTextEdit, self).__init__(*args, **kwargs)
        self.parent_editor = parent_editor

    def wheelEvent(self, event):
        if self.textCursor().hasSelection():
            delta = event.angleDelta().y()
            selected_text = self.textCursor().selectedText()

            if selected_text.isdigit():
                if delta > 0:  # Scroll up
                    self.increment_value()
                elif delta < 0:  # Scroll down
                    self.decrement_value()
        else:
            super(SelectableTextEdit, self).wheelEvent(event)

    def copy_to_clipboard(self):
        self.parent_editor.copy_to_clipboard()

    def increment_value(self):
        self._change_value(1)

    def decrement_value(self):
        cursor = self.textCursor()
        selected_text = cursor.selectedText()

        if selected_text.isdigit():
            if int(selected_text) == 0:  # If value is 0, don't decrement it.
                return
            else:
                self._change_value(-1)

    def _change_value(self, delta):
        cursor = self.textCursor()
        selected_text = cursor.selectedText()

        if selected_text.isdigit():
            start = cursor.selectionStart()
            old_length = cursor.selectionEnd() - start

            new_value = str(int(selected_text) + delta)

            cursor.beginEditBlock()
            cursor.removeSelectedText()
            cursor.insertText(new_value)
            cursor.endEditBlock()

            new_length = len(new_value)

            cursor.setPosition(start)
            cursor.setPosition(start + new_length, QTextCursor.KeepAnchor)  # Use new_length here
            self.setTextCursor(cursor)
            self.copy_to_clipboard()  # Call copy to clipboard

def load_stylesheet(qss_file_path):
    with open(qss_file_path, "r") as f:
        return f.read()

app = QApplication(sys.argv)
font = QFont("Helvetica, Arial, sans-serif")
app.setFont(font)
window = TextEditor()
window.show()

# Apply the stylesheet
app.setStyleSheet(load_stylesheet("C:\Portable Programs\CMD Projects\Renamer\Geoo.qss"))

sys.exit(app.exec_())
