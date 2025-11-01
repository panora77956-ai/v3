# -*- coding: utf-8 -*-
"""
Unified Theme System v2 - Video Super Ultra v1.0.0.0
Complete vibrant theme with consistent typography across all tabs
"""

# Vibrant Color Palette
COLORS = {
    'primary': '#2196F3',      # Blue - Primary actions
    'primary_dark': '#1976D2',
    'primary_light': '#64B5F6',
    'primary_hover': '#E3F2FD',
    'success': '#4CAF50',      # Green - Success/Save
    'success_hover': '#66BB6A',
    'warning': '#FF9800',      # Orange - Warning/Import
    'warning_hover': '#FFB74D',
    'danger': '#F44336',       # Red - Delete/Danger
    'danger_hover': '#EF5350',
    'info': '#00BCD4',         # Cyan - Info/Check
    'info_hover': '#26C6DA',
    'background': '#FAFAFA',
    'surface': '#FFFFFF',
    'border': '#E0E0E0',
    'divider': '#E0E0E0',
    'hover': '#F5F5F5',
    'text_primary': '#212121',
    'text_secondary': '#757575',
}

# Unified Material Design Stylesheet with +1px typography and vibrant colors
UNIFIED_STYLESHEET = """
/* Global - Base font size increased to 13px */
QWidget {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}

/* Labels - 14px bold */
QLabel {
    color: #424242;
    font-size: 14px;
    font-weight: bold;
}

/* Buttons - 14px bold, vibrant colors (PR#4: Reduced padding for smaller buttons) */
QPushButton {
    background: #2196F3;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 4px 12px;
    min-height: 24px;
    font-weight: bold;
    font-size: 13px;
}

QPushButton:hover {
    background: #64B5F6;
}

QPushButton:pressed {
    background: #1976D2;
}

QPushButton:disabled {
    background: #BDBDBD;
    color: #757575;
}

/* PR#4: Smaller buttons in key lists */
QPushButton[objectName*="btn_check"],
QPushButton[objectName*="btn_delete"],
QPushButton[objectName*="btn_primary"] {
    min-height: 20px;
    padding: 2px 8px;
    font-size: 12px;
}

/* Success Buttons (Green) - Save actions */
QPushButton[objectName*="save"],
QPushButton[objectName*="success"],
QPushButton[objectName*="luu"] {
    background: #4CAF50;
}

QPushButton[objectName*="save"]:hover,
QPushButton[objectName*="success"]:hover,
QPushButton[objectName*="luu"]:hover {
    background: #66BB6A;
}

QPushButton[objectName*="save"]:pressed,
QPushButton[objectName*="success"]:pressed,
QPushButton[objectName*="luu"]:pressed {
    background: #388E3C;
}

/* Warning Buttons (Orange) - Import actions */
QPushButton[objectName*="import"],
QPushButton[objectName*="warning"],
QPushButton[objectName*="nhap"] {
    background: #FF9800;
}

QPushButton[objectName*="import"]:hover,
QPushButton[objectName*="warning"]:hover,
QPushButton[objectName*="nhap"]:hover {
    background: #FFB74D;
}

QPushButton[objectName*="import"]:pressed,
QPushButton[objectName*="warning"]:pressed,
QPushButton[objectName*="nhap"]:pressed {
    background: #F57C00;
}

/* Danger Buttons (Red) - Delete actions */
QPushButton[objectName*="delete"],
QPushButton[objectName*="danger"],
QPushButton[objectName*="xoa"],
QPushButton[objectName*="del"] {
    background: #F44336;
}

QPushButton[objectName*="delete"]:hover,
QPushButton[objectName*="danger"]:hover,
QPushButton[objectName*="xoa"]:hover,
QPushButton[objectName*="del"]:hover {
    background: #EF5350;
}

QPushButton[objectName*="delete"]:pressed,
QPushButton[objectName*="danger"]:pressed,
QPushButton[objectName*="xoa"]:pressed,
QPushButton[objectName*="del"]:pressed {
    background: #C62828;
}

/* Info Buttons (Cyan) - Check/Info actions */
QPushButton[objectName*="check"],
QPushButton[objectName*="info"],
QPushButton[objectName*="kiem"],
QPushButton[objectName*="test"] {
    background: #00BCD4;
}

QPushButton[objectName*="check"]:hover,
QPushButton[objectName*="info"]:hover,
QPushButton[objectName*="kiem"]:hover,
QPushButton[objectName*="test"]:hover {
    background: #26C6DA;
}

QPushButton[objectName*="check"]:pressed,
QPushButton[objectName*="info"]:pressed,
QPushButton[objectName*="kiem"]:pressed,
QPushButton[objectName*="test"]:pressed {
    background: #0097A7;
}

/* Text Inputs */
QLineEdit, QTextEdit, QPlainTextEdit {
    background: white;
    border: 1px solid #E0E0E0;
    border-radius: 4px;
    padding: 12px;
    color: #212121;
    font-size: 13px;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 2px solid #2196F3;
    padding: 11px;
}

QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {
    background: #F5F5F5;
    color: #9E9E9E;
}

/* Combo Box */
QComboBox {
    background: white;
    border: 1px solid #E0E0E0;
    border-radius: 4px;
    padding: 10px;
    min-width: 100px;
    font-size: 13px;
}

QComboBox:hover {
    border: 1px solid #2196F3;
}

QComboBox::drop-down {
    border: none;
    padding-right: 10px;
}

QComboBox QAbstractItemView {
    background: white;
    border: 1px solid #E0E0E0;
    selection-background-color: #E3F2FD;
    selection-color: #212121;
    font-size: 13px;
}

/* Spin Box */
QSpinBox {
    background: white;
    border: 1px solid #E0E0E0;
    border-radius: 4px;
    padding: 10px;
    font-size: 13px;
}

QSpinBox:focus {
    border: 2px solid #2196F3;
    padding: 9px;
}

/* List Widget */
QListWidget {
    background: white;
    border: 1px solid #E0E0E0;
    border-radius: 4px;
    font-size: 13px;
}

QListWidget::item {
    padding: 8px;
    border-bottom: 1px solid #F5F5F5;
}

QListWidget::item:selected {
    background: #E3F2FD;
    color: #212121;
}

QListWidget::item:hover {
    background: #F5F5F5;
}

/* Table Widget */
QTableWidget {
    background: white;
    border: 1px solid #E0E0E0;
    border-radius: 8px;
    gridline-color: #F5F5F5;
    font-size: 13px;
}

QTableWidget::item {
    padding: 8px;
}

QTableWidget::item:selected {
    background: #E3F2FD;
    color: #212121;
}

QTableWidget::item:hover {
    background: #F5F5F5;
}

QHeaderView::section {
    background: #F5F5F5;
    padding: 10px;
    border: none;
    border-bottom: 2px solid #2196F3;
    font-weight: bold;
    font-size: 14px;
    color: #424242;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #E0E0E0;
    border-radius: 4px;
    background: white;
}

/* PR#4: Enhanced tab styling with bold text, colorful backgrounds, wider tabs */
QTabBar::tab {
    font-weight: 700;
    font-size: 14px;
    min-width: 150px;
    padding: 10px 20px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    color: white;
}

/* Different color for each tab (Cài đặt, Image2Video, Text2Video, Video bán hàng) */
QTabBar::tab:nth-child(1) {
    background: #2196F3;  /* Blue - Cài đặt */
}

QTabBar::tab:nth-child(2) {
    background: #4CAF50;  /* Green - Image2Video */
}

QTabBar::tab:nth-child(3) {
    background: #FF9800;  /* Orange - Text2Video */
}

QTabBar::tab:nth-child(4) {
    background: #9C27B0;  /* Purple - Video bán hàng */
}

QTabBar::tab:selected {
    border-bottom: 4px solid white;
    font-size: 15px;
}

QTabBar::tab:hover:!selected {
    opacity: 0.8;
}

/* Group Box - 16px bold title, reduced spacing (6px) */
QGroupBox {
    border: 1px solid #E0E0E0;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 6px;
    background: white;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 6px 10px;
    color: #424242;
    font-weight: bold;
    font-size: 16px;
}

/* Scroll Bar */
QScrollBar:vertical {
    border: none;
    background: #F5F5F5;
    width: 10px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #BDBDBD;
    border-radius: 5px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #9E9E9E;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    border: none;
    background: #F5F5F5;
    height: 10px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background: #BDBDBD;
    border-radius: 5px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background: #9E9E9E;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* Progress Bar */
QProgressBar {
    border: 1px solid #E0E0E0;
    border-radius: 4px;
    text-align: center;
    background: #F5F5F5;
    font-size: 13px;
}

QProgressBar::chunk {
    background: #2196F3;
    border-radius: 3px;
}

/* Checkbox - Blue themed */
QCheckBox {
    spacing: 8px;
    font-size: 13px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #757575;
    border-radius: 3px;
    background: white;
}

QCheckBox::indicator:checked {
    background: #2196F3;
    border: 2px solid #2196F3;
}

QCheckBox::indicator:hover {
    border: 2px solid #2196F3;
}

/* Radio Button - Blue themed */
QRadioButton {
    spacing: 8px;
    font-size: 13px;
}

QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #757575;
    border-radius: 9px;
    background: white;
}

QRadioButton::indicator:checked {
    background: #2196F3;
    border: 2px solid #2196F3;
}

QRadioButton::indicator:hover {
    border: 2px solid #2196F3;
}

/* Tool Button */
QToolButton {
    background: transparent;
    border: none;
    padding: 8px;
    border-radius: 4px;
    font-size: 13px;
}

QToolButton:hover {
    background: #F5F5F5;
}

QToolButton:pressed {
    background: #E0E0E0;
}
"""


def apply_theme(app):
    """
    Apply unified Material Design v2 theme to the application
    
    Args:
        app: QApplication instance
    """
    app.setStyleSheet(UNIFIED_STYLESHEET)
