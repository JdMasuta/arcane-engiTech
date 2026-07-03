"""Qt stylesheet built from the shared arcane palette."""
from arcane import theme

STYLESHEET = f"""
* {{
    font-family: "Segoe UI", "Helvetica Neue", sans-serif;
    font-size: 13px;
    color: #{theme.TEXT};
}}
QWidget {{
    background-color: #{theme.BACKGROUND};
}}
QMainWindow::separator {{
    background: #{theme.BORDER};
    width: 1px;
    height: 1px;
}}
QFrame#Panel, QGroupBox {{
    background-color: #{theme.SURFACE};
    border: 1px solid #{theme.BORDER};
    border-radius: 10px;
}}
QGroupBox {{
    margin-top: 14px;
    padding: 10px 12px 12px 12px;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
    color: #{theme.ACCENT};
}}
QLabel#Title {{
    font-size: 18px;
    font-weight: 700;
    color: #{theme.TEXT};
}}
QLabel#Subtitle {{
    color: #{theme.TEXT_MUTED};
}}
QLabel#StatusValue {{
    color: #{theme.GOLD};
    font-weight: 600;
}}
QPushButton {{
    background-color: #{theme.SURFACE_LIGHT};
    border: 1px solid #{theme.BORDER};
    border-radius: 8px;
    padding: 7px 14px;
}}
QPushButton:hover {{
    border-color: #{theme.ACCENT};
}}
QPushButton:pressed {{
    background-color: #{theme.ACCENT_DIM};
}}
QPushButton:disabled {{
    color: #{theme.TEXT_MUTED};
    border-color: #{theme.SURFACE_LIGHT};
}}
QPushButton#Primary {{
    background-color: #{theme.ACCENT_DIM};
    border: 1px solid #{theme.ACCENT};
    font-weight: 600;
}}
QPushButton#Primary:hover {{
    background-color: #{theme.ACCENT};
    color: #{theme.BACKGROUND};
}}
QSpinBox, QDoubleSpinBox, QComboBox, QLineEdit {{
    background-color: #{theme.BACKGROUND};
    border: 1px solid #{theme.BORDER};
    border-radius: 6px;
    padding: 4px 6px;
    selection-background-color: #{theme.ACCENT_DIM};
}}
QComboBox::drop-down {{
    border: none;
    width: 18px;
}}
QComboBox QAbstractItemView {{
    background-color: #{theme.SURFACE};
    border: 1px solid #{theme.BORDER};
    selection-background-color: #{theme.ACCENT_DIM};
}}
QSlider::groove:horizontal {{
    height: 6px;
    background: #{theme.SURFACE_LIGHT};
    border-radius: 3px;
}}
QSlider::sub-page:horizontal {{
    background: #{theme.ACCENT};
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: #{theme.GOLD};
    width: 14px;
    margin: -5px 0;
    border-radius: 7px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid #{theme.BORDER};
    border-radius: 4px;
    background: #{theme.BACKGROUND};
}}
QCheckBox::indicator:checked {{
    background: #{theme.ACCENT};
}}
QProgressBar {{
    border: 1px solid #{theme.BORDER};
    border-radius: 6px;
    text-align: center;
    background: #{theme.BACKGROUND};
}}
QProgressBar::chunk {{
    background-color: #{theme.ACCENT};
    border-radius: 5px;
}}
QScrollArea {{
    border: none;
}}
QStatusBar {{
    color: #{theme.TEXT_MUTED};
}}
"""
