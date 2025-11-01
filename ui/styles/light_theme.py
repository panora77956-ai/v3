# -*- coding: utf-8 -*-
"""
Light Theme System - Video Super Ultra v1.0.0.0
Complete light theme with flat design and consistent typography
Material Design Light principles implementation
"""

# Light Flat Color Palette
COLORS = {
    "primary": "#1E88E5",  # Blue - Primary/Info actions
    "primary_dark": "#1565C0",
    "primary_hover": "#2196F3",
    "success": "#4CAF50",  # Green - Success/Generate
    "success_hover": "#66BB6A",
    "warning": "#FF6B2C",  # Orange - Warning/Auto actions
    "warning_hover": "#FF8A50",
    "danger": "#F44336",  # Red - Delete/Danger
    "danger_hover": "#E57373",
    "info": "#008080",  # Teal - Info/Check
    "info_hover": "#009999",
    "gray": "#666666",  # Gray - Stop/Cancel
    "gray_hover": "#808080",
    "background": "#F5F5F5",  # Light background
    "surface": "#FFFFFF",  # Light surface
    "border": "#E0E0E0",  # Light border
    "divider": "#E0E0E0",
    "hover": "#EEEEEE",
    "text_primary": "#212121",
    "text_secondary": "#424242",
}

# Unified Light Theme Stylesheet with Segoe UI
LIGHT_STYLESHEET = """
/* Global - Light theme with Segoe UI, 14px base (was 13px, +1px for readability) */
QWidget {
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 14px;
    color: #212121;
    background-color: #F5F5F5;
}

/* Labels - 14px normal weight (was 13px) */
QLabel {
    color: #212121;
    font-size: 14px;
    font-weight: normal;
    background: transparent;
}

/* Buttons - Flat light design with consistent colors */
QPushButton {
    background: #1E88E5;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    min-height: 32px;
    font-weight: 600;
    font-size: 14px;
    font-family: "Segoe UI", Arial, sans-serif;
}

QPushButton:hover {
    background: #2196F3;
}

QPushButton:pressed {
    background: #1565C0;
}

QPushButton:disabled {
    background: #E0E0E0;
    color: #9E9E9E;
}

/* Settings panel buttons - 24px height */
QPushButton[objectName*="btn_check"],
QPushButton[objectName*="btn_delete"],
QPushButton[objectName*="btn_primary"] {
    min-height: 24px;
    padding: 4px 12px;
    font-size: 12px;
}

/* Success Buttons (Green) - Save/Generate actions */
QPushButton[objectName*="save"],
QPushButton[objectName*="success"],
QPushButton[objectName*="luu"],
QPushButton[objectName*="auto"] {
    background: #4CAF50;
}

QPushButton[objectName*="save"]:hover,
QPushButton[objectName*="success"]:hover,
QPushButton[objectName*="luu"]:hover,
QPushButton[objectName*="auto"]:hover {
    background: #66BB6A;
}

QPushButton[objectName*="save"]:pressed,
QPushButton[objectName*="success"]:pressed,
QPushButton[objectName*="luu"]:pressed,
QPushButton[objectName*="auto"]:pressed {
    background: #388E3C;
}

/* Warning Buttons (Orange) - Auto/Import actions */
QPushButton[objectName*="import"],
QPushButton[objectName*="warning"],
QPushButton[objectName*="nhap"] {
    background: #FF6B2C;
}

QPushButton[objectName*="import"]:hover,
QPushButton[objectName*="warning"]:hover,
QPushButton[objectName*="nhap"]:hover {
    background: #FF8A50;
}

QPushButton[objectName*="import"]:pressed,
QPushButton[objectName*="warning"]:pressed,
QPushButton[objectName*="nhap"]:pressed {
    background: #E65100;
}

/* Danger Buttons (Red) - Delete/Stop actions */
QPushButton[objectName*="delete"],
QPushButton[objectName*="danger"],
QPushButton[objectName*="xoa"],
QPushButton[objectName*="del"],
QPushButton[objectName*="stop"],
QPushButton[objectName*="dung"] {
    background: #F44336;
}

QPushButton[objectName*="delete"]:hover,
QPushButton[objectName*="danger"]:hover,
QPushButton[objectName*="xoa"]:hover,
QPushButton[objectName*="del"]:hover,
QPushButton[objectName*="stop"]:hover,
QPushButton[objectName*="dung"]:hover {
    background: #E57373;
}

QPushButton[objectName*="delete"]:pressed,
QPushButton[objectName*="danger"]:pressed,
QPushButton[objectName*="xoa"]:pressed,
QPushButton[objectName*="del"]:pressed,
QPushButton[objectName*="stop"]:pressed,
QPushButton[objectName*="dung"]:pressed {
    background: #D32F2F;
}

/* Info Buttons (Teal) - Check/Info actions */
QPushButton[objectName*="check"],
QPushButton[objectName*="info"],
QPushButton[objectName*="kiem"],
QPushButton[objectName*="test"] {
    background: #008080;
}

QPushButton[objectName*="check"]:hover,
QPushButton[objectName*="info"]:hover,
QPushButton[objectName*="kiem"]:hover,
QPushButton[objectName*="test"]:hover {
    background: #009999;
}

QPushButton[objectName*="check"]:pressed,
QPushButton[objectName*="info"]:pressed,
QPushButton[objectName*="kiem"]:pressed,
QPushButton[objectName*="test"]:pressed {
    background: #006666;
}

/* Gray Buttons - Stop/Cancel actions */
QPushButton[objectName*="gray"] {
    background: #666666;
}

QPushButton[objectName*="gray"]:hover {
    background: #808080;
}

QPushButton[objectName*="gray"]:pressed {
    background: #4D4D4D;
}

/* Text Inputs - Light theme */
QLineEdit, QTextEdit, QPlainTextEdit {
    background: #FFFFFF;
    border: 1px solid #E0E0E0;
    border-radius: 4px;
    padding: 12px;
    color: #212121;
    font-size: 14px;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 2px solid #1E88E5;
    padding: 11px;
}

QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {
    background: #F5F5F5;
    color: #9E9E9E;
}

/* Combo Box - Light theme */
QComboBox {
    background: #FFFFFF;
    border: 1px solid #E0E0E0;
    border-radius: 4px;
    padding: 10px;
    min-width: 100px;
    font-size: 14px;
    color: #212121;
}

QComboBox:hover {
    border: 1px solid #1E88E5;
}

QComboBox::drop-down {
    border: none;
    padding-right: 10px;
}

QComboBox QAbstractItemView {
    background: #FFFFFF;
    border: 1px solid #E0E0E0;
    selection-background-color: #1E88E5;
    selection-color: #FFFFFF;
    color: #212121;
    font-size: 14px;
}

/* Spin Box - Light theme */
QSpinBox {
    background: #FFFFFF;
    border: 1px solid #E0E0E0;
    border-radius: 4px;
    padding: 10px;
    font-size: 14px;
    color: #212121;
}

QSpinBox:focus {
    border: 2px solid #1E88E5;
    padding: 9px;
}

/* List Widget - Light theme with 120px height and 12px monospace */
QListWidget {
    background: #FFFFFF;
    border: 1px solid #E0E0E0;
    border-radius: 4px;
    min-height: 120px;
    font-size: 12px;
    font-family: "Courier New", monospace;
    color: #212121;
}

QListWidget::item {
    padding: 8px;
    border-bottom: 1px solid #EEEEEE;
}

QListWidget::item:selected {
    background: #1E88E5;
    color: #FFFFFF;
}

QListWidget::item:hover {
    background: #EEEEEE;
}

/* Table Widget - Light theme */
QTableWidget {
    background: #FFFFFF;
    border: 1px solid #E0E0E0;
    border-radius: 8px;
    gridline-color: #EEEEEE;
    font-size: 14px;
    color: #212121;
}

QTableWidget::item {
    padding: 8px;
}

QTableWidget::item:selected {
    background: #1E88E5;
    color: #FFFFFF;
}

QTableWidget::item:hover {
    background: #EEEEEE;
}

QHeaderView::section {
    background: #F5F5F5;
    padding: 10px;
    border: none;
    border-bottom: 2px solid #1E88E5;
    font-weight: bold;
    font-size: 14px;
    color: #212121;
}

/* Tab Widget - Light theme */
QTabWidget::pane {
    border: 1px solid #E0E0E0;
    border-radius: 4px;
    background: #FFFFFF;
}

/* Tab Bar - Bold font with light theme colors */
QTabBar::tab {
    font-family: "Segoe UI", Arial, sans-serif;
    font-weight: 700;
    font-size: 15px;
    min-width: 150px;
    padding: 12px 24px;
    margin-right: 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    color: #FFFFFF;
    background: #BDBDBD;
}

/* Main navigation tabs - Different colors */
QTabBar::tab:nth-child(1) {
    background: #1E88E5;  /* Blue - Cài đặt */
}

QTabBar::tab:nth-child(2) {
    background: #4CAF50;  /* Green - Image2Video */
}

QTabBar::tab:nth-child(3) {
    background: #FF6B2C;  /* Orange - Text2Video */
}

QTabBar::tab:nth-child(4) {
    background: #9C27B0;  /* Purple - Video bán hàng */
}

QTabBar::tab:selected {
    border-bottom: 4px solid #212121;
    font-size: 15px;
    padding-bottom: 8px;
}

QTabBar::tab:hover:!selected {
    background-color: rgba(0, 0, 0, 0.15);
}

/* Group Box - Light theme with 6px spacing */
QGroupBox {
    border: 1px solid #E0E0E0;
    border-radius: 8px;
    margin-top: 6px;
    padding-top: 6px;
    background: #FFFFFF;
    font-family: "Segoe UI", Arial, sans-serif;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 6px 12px;
    color: #212121;
    font-weight: bold;
    font-size: 14px;
    font-family: "Segoe UI", Arial, sans-serif;
}

/* Scroll Bar - Light theme with horizontal support */
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

/* Progress Bar - Light theme */
QProgressBar {
    border: 1px solid #E0E0E0;
    border-radius: 4px;
    text-align: center;
    background: #F5F5F5;
    font-size: 14px;
    color: #212121;
}

QProgressBar::chunk {
    background: #1E88E5;
    border-radius: 3px;
}

/* Checkbox - Light theme */
QCheckBox {
    spacing: 8px;
    font-size: 14px;
    color: #212121;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #9E9E9E;
    border-radius: 3px;
    background: #FFFFFF;
}

QCheckBox::indicator:checked {
    background: #1E88E5;
    border: 2px solid #1E88E5;
}

QCheckBox::indicator:hover {
    border: 2px solid #1E88E5;
}

/* Radio Button - Light theme */
QRadioButton {
    spacing: 8px;
    font-size: 14px;
    color: #212121;
}

QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #9E9E9E;
    border-radius: 9px;
    background: #FFFFFF;
}

QRadioButton::indicator:checked {
    background: #1E88E5;
    border: 2px solid #1E88E5;
}

QRadioButton::indicator:hover {
    border: 2px solid #1E88E5;
}

/* Tool Button - Light theme */
QToolButton {
    background: transparent;
    border: none;
    padding: 8px;
    border-radius: 4px;
    font-size: 14px;
    color: #212121;
}

QToolButton:hover {
    background: #EEEEEE;
}

QToolButton:pressed {
    background: #E0E0E0;
}
"""


def apply_light_theme(app):
    """
    Apply unified Material Design light theme to the application

    Args:
        app: QApplication instance
    """
    app.setStyleSheet(LIGHT_STYLESHEET)
