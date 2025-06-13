import customtkinter as ctk

# Холодная цветовая схема с повышенной контрастностью
BG_COLOR = "#f1eee8"         # Основной фон
ACCENT_COLOR = "#edc20a"     # Яркий акцент (золото)
HOVER_COLOR = "#ebe3e0"      # Цвет при наведении
TEXT_COLOR = "#363636"       # Светлый текст
BORDER_COLOR = "#c6aa82"     # Цвет рамок и делений
SHADOW_COLOR   = "#000000"   # Тень – абсолютно чёрный


# Более читаемый современный шрифт. При отсутствии автоматически
# подберётся ближайшая замена.
FONT_FAMILY = "Segoe UI"

# Размеры и радиусы по умолчанию
BASE_FONT_SIZE = 13
TITLE_FONT_SIZE = 18
CORNER_RADIUS = 14
ENTRY_HEIGHT = 38
BUTTON_HEIGHT = 38

def style_button(button: ctk.CTkButton):
    """Apply unified style for action buttons."""
    button.configure(
        corner_radius=CORNER_RADIUS,
        fg_color=ACCENT_COLOR,
        hover_color=HOVER_COLOR,
        height=BUTTON_HEIGHT,
        border_width=2,
        border_color=SHADOW_COLOR,
        text_color="black",
        font=ctk.CTkFont(family=FONT_FAMILY, size=BASE_FONT_SIZE, weight="bold"),
    )

def style_frame(frame: ctk.CTkFrame):
    """Standard frame styling with rounded corners."""
    frame.configure(fg_color=BG_COLOR, corner_radius=CORNER_RADIUS)

def style_label(label: ctk.CTkLabel, size=BASE_FONT_SIZE, weight="bold"):
    """Style for labels used across the interface."""
    label.configure(
        font=ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight),
        text_color=TEXT_COLOR,
    )

def style_title(label: ctk.CTkLabel):
    """Style for section titles."""
    label.configure(
        font=ctk.CTkFont(family=FONT_FAMILY, size=TITLE_FONT_SIZE, weight="bold"),
        text_color=TEXT_COLOR,
    )

def style_entry(entry: ctk.CTkEntry, size=BASE_FONT_SIZE, weight="bold"):
    """Unified entry field styling."""
    entry.configure(
        height=ENTRY_HEIGHT,
        corner_radius=CORNER_RADIUS,
        font=ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight),
        fg_color=BG_COLOR,
        text_color=TEXT_COLOR,
    )

def style_textbox(textbox: ctk.CTkTextbox, size=BASE_FONT_SIZE):
    textbox.configure(
        font=ctk.CTkFont(family=FONT_FAMILY, size=size),
        fg_color=BG_COLOR,
        text_color=TEXT_COLOR,
        state="disabled"
    )

def style_box_frame(frame: ctk.CTkFrame):
    frame.configure(
        fg_color="transparent",
        border_color=BORDER_COLOR,
        border_width=2,
        corner_radius=CORNER_RADIUS
    )

