"""Dark theme stylesheet matching frontend design."""

DARK_THEME_STYLESHEET = """
/* Main Window Styles */
QMainWindow {
    background-color: #0f172a;
    color: #ffffff;
}

/* Card Styles (Glassmorphism) */
QWidget[class="card"] {
    background-color: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
}

/* Button Styles */
QPushButton {
    background-color: #f59e0b;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #fbbf24;
}

QPushButton:pressed {
    background-color: #d97706;
}

QPushButton:disabled {
    background-color: rgba(245, 158, 11, 0.5);
    color: rgba(255, 255, 255, 0.5);
}

/* Input Styles */
QLineEdit, QTextEdit, QComboBox {
    background-color: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    padding: 8px 12px;
    color: #ffffff;
    font-size: 14px;
}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 1px solid rgba(245, 158, 11, 0.5);
    background-color: rgba(255, 255, 255, 0.15);
}

QLineEdit::placeholder {
    color: rgba(255, 255, 255, 0.4);
}

/* Label Styles */
QLabel {
    color: #ffffff;
    font-size: 14px;
}

QLabel[class="title"] {
    font-size: 24px;
    font-weight: 700;
    color: #ffffff;
}

QLabel[class="description"] {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.7);
}

QLabel[class="error"] {
    color: #ef4444;
    font-size: 12px;
}

/* Tab Widget Styles */
QTabWidget::pane {
    border: 1px solid rgba(255, 255, 255, 0.1);
    background-color: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
}

QTabBar::tab {
    background-color: rgba(255, 255, 255, 0.05);
    color: rgba(255, 255, 255, 0.7);
    border: none;
    padding: 10px 20px;
    margin-right: 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
}

QTabBar::tab:selected {
    background-color: rgba(255, 255, 255, 0.1);
    color: #f59e0b;
    font-weight: 600;
}

QTabBar::tab:hover {
    background-color: rgba(255, 255, 255, 0.08);
}

/* Table Styles */
QTableWidget {
    background-color: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    gridline-color: rgba(255, 255, 255, 0.1);
    color: #ffffff;
}

QTableWidget::item {
    padding: 8px;
}

QTableWidget::item:selected {
    background-color: rgba(245, 158, 11, 0.2);
    color: #ffffff;
}

QHeaderView::section {
    background-color: rgba(255, 255, 255, 0.1);
    color: #ffffff;
    padding: 8px;
    border: none;
    font-weight: 600;
}

/* Scrollbar Styles */
QScrollBar:vertical {
    background-color: rgba(255, 255, 255, 0.05);
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: rgba(255, 255, 255, 0.2);
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: rgba(255, 255, 255, 0.3);
}

QScrollBar:horizontal {
    background-color: rgba(255, 255, 255, 0.05);
    height: 12px;
    border-radius: 6px;
}

QScrollBar::handle:horizontal {
    background-color: rgba(255, 255, 255, 0.2);
    border-radius: 6px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: rgba(255, 255, 255, 0.3);
}

/* Progress Bar Styles */
QProgressBar {
    background-color: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 4px;
    text-align: center;
    color: #ffffff;
    height: 20px;
}

QProgressBar::chunk {
    background-color: #f59e0b;
    border-radius: 3px;
}

/* Checkbox Styles */
QCheckBox {
    color: #ffffff;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-radius: 4px;
    background-color: rgba(255, 255, 255, 0.1);
}

QCheckBox::indicator:checked {
    background-color: #f59e0b;
    border-color: #f59e0b;
}

QCheckBox::indicator:hover {
    border-color: #fbbf24;
}

/* Dialog Styles */
QDialog {
    background-color: #0f172a;
    color: #ffffff;
}

/* Message Box Styles */
QMessageBox {
    background-color: #0f172a;
    color: #ffffff;
}

QMessageBox QPushButton {
    min-width: 80px;
}
"""


















