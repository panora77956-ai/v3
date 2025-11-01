# -*- coding: utf-8 -*-
"""
Unified Theme System v2 - Video Super Ultra v1.0.0.0
Complete vibrant theme with consistent typography across all tabs
PR#5: Fixed QSS syntax, unified Segoe UI font, flat darker palette
"""

# Flat Darker Color Palette (PR#5: Less garish)
COLORS = {
    'primary': '#1565C0',      # Darker Blue - Primary actions
    'primary_dark': '#0D47A1',
    'primary_light': '#1976D2',
    'primary_hover': '#BBDEFB',
    'success': '#2E7D32',      # Darker Green - Success/Save
    'success_hover': '#388E3C',
    'warning': '#E65100',      # Darker Orange - Warning/Import
    'warning_hover': '#EF6C00',
    'danger': '#C62828',       # Darker Red - Delete/Danger
    'danger_hover': '#D32F2F',
    'info': '#00838F',         # Darker Cyan - Info/Check
    'info_hover': '#00ACC1',
    'background': '#FAFAFA',
    'surface': '#FFFFFF',
    'border': '#E0E0E0',
    'divider': '#E0E0E0',
    'hover': '#F5F5F5',
    'text_primary': '#212121',
    'text_secondary': '#757575',
}

# Unified Material Design Stylesheet with Segoe UI and flat darker colors (PR#5)
UNIFIED_STYLESHEET = """
/* Global - Unified Segoe UI, 13px base (PR#5) */
QWidget {
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
    color: #212121;
}

/* Labels - 13px normal weight (PR#5: not all labels should be bold) */
QLabel {
    color: #424242;
    font-size: 13px;
    font-weight: normal;
}

/* Buttons - 13px, flat darker colors (PR#5) */
QPushButton {
    background: #1565C0;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    min-height: 32px;
    font-weight: 600;
    font-size: 13px;
    font-family: "Segoe UI", Arial, sans-serif;
}

QPushButton:hover {
    background: #1976D2;
}

QPushButton:pressed {
    background: #0D47A1;
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

/* Success Buttons (Darker Green) - Save actions (PR#5) */
QPushButton[objectName*="save"],
QPushButton[objectName*="success"],
QPushButton[objectName*="luu"] {
    background: #2E7D32;
}

QPushButton[objectName*="save"]:hover,
QPushButton[objectName*="success"]:hover,
QPushButton[objectName*="luu"]:hover {
    background: #388E3C;
}

QPushButton[objectName*="save"]:pressed,
QPushButton[objectName*="success"]:pressed,
QPushButton[objectName*="luu"]:pressed {
    background: #1B5E20;
}

/* Warning Buttons (Darker Orange) - Import actions (PR#5) */
QPushButton[objectName*="import"],
QPushButton[objectName*="warning"],
QPushButton[objectName*="nhap"] {
    background: #E65100;
}

QPushButton[objectName*="import"]:hover,
QPushButton[objectName*="warning"]:hover,
QPushButton[objectName*="nhap"]:hover {
    background: #EF6C00;
}

QPushButton[objectName*="import"]:pressed,
QPushButton[objectName*="warning"]:pressed,
QPushButton[objectName*="nhap"]:pressed {
    background: #BF360C;
}

/* Danger Buttons (Darker Red) - Delete actions (PR#5) */
QPushButton[objectName*="delete"],
QPushButton[objectName*="danger"],
QPushButton[objectName*="xoa"],
QPushButton[objectName*="del"] {
    background: #C62828;
}

QPushButton[objectName*="delete"]:hover,
QPushButton[objectName*="danger"]:hover,
QPushButton[objectName*="xoa"]:hover,
QPushButton[objectName*="del"]:hover {
    background: #D32F2F;
}

QPushButton[objectName*="delete"]:pressed,
QPushButton[objectName*="danger"]:pressed,
QPushButton[objectName*="xoa"]:pressed,
QPushButton[objectName*="del"]:pressed {
    background: #B71C1C;
}

/* Info Buttons (Darker Cyan) - Check/Info actions (PR#5) */
QPushButton[objectName*="check"],
QPushButton[objectName*="info"],
QPushButton[objectName*="kiem"],
QPushButton[objectName*="test"] {
    background: #00838F;
}

QPushButton[objectName*="check"]:hover,
QPushButton[objectName*="info"]:hover,
QPushButton[objectName*="kiem"]:hover,
QPushButton[objectName*="test"]:hover {
    background: #00ACC1;
}

QPushButton[objectName*="check"]:pressed,
QPushButton[objectName*="info"]:pressed,
QPushButton[objectName*="kiem"]:pressed,
QPushButton[objectName*="test"]:pressed {
    background: #006064;
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

/* PR#5: Bold tab styling with flat darker colorful backgrounds */
QTabBar::tab {
    font-family: "Segoe UI", Arial, sans-serif;
    font-weight: 700;
    font-size: 14px;
    min-width: 150px;
    padding: 12px 24px;
    margin-right: 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    color: white;
}

/* Different color for each tab - darker flat colors (PR#5) */
QTabBar::tab:nth-child(1) {
    background: #1565C0;  /* Darker Blue - Cài đặt */
}

QTabBar::tab:nth-child(2) {
    background: #2E7D32;  /* Darker Green - Image2Video */
}

QTabBar::tab:nth-child(3) {
    background: #E65100;  /* Darker Orange - Text2Video */
}

QTabBar::tab:nth-child(4) {
    background: #6A1B9A;  /* Darker Purple - Video bán hàng */
}

QTabBar::tab:selected {
    border-bottom: 4px solid white;
    font-size: 15px;
    padding-bottom: 8px;
}

QTabBar::tab:hover:!selected {
    filter: brightness(1.1);
}

/* Group Box - 14px bold title with icon support (PR#5) */
QGroupBox {
    border: 1px solid #E0E0E0;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 8px;
    background: white;
    font-family: "Segoe UI", Arial, sans-serif;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 8px 12px;
    color: #424242;
    font-weight: bold;
    font-size: 14px;
    font-family: "Segoe UI", Arial, sans-serif;
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
