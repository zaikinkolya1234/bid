import customtkinter as ctk

# Цвета и шрифт — тёмный стиль в духе интерфейса на скриншоте
BG_COLOR = "#0D0D0D"         # Основной фон
ACCENT_COLOR = "#F5C000"     # Яркий акцент (золото)
HOVER_COLOR = "#FFDD55"      # Цвет при наведении
TEXT_COLOR = "#E0E0E0"       # Светлый текст
BORDER_COLOR = "#333333"     # Цвет рамок и делений

# Предпочтительный современный шрифт. Используем Inter, но при отсутствии
# такого шрифта в системе tkinter автоматически подберёт замену.
FONT_FAMILY = "Inter"

# Общий размер шрифта для большинства элементов. Значение немного больше
# прежнего для улучшения читаемости на дисплеях с высоким DPI.
BASE_FONT_SIZE = 12

def style_button(button: ctk.CTkButton):
    """Apply unified style for action buttons."""
    button.configure(
        corner_radius=12,
        fg_color=ACCENT_COLOR,
        hover_color=HOVER_COLOR,
        text_color="black",
        font=ctk.CTkFont(family=FONT_FAMILY, size=BASE_FONT_SIZE)
    )

def style_frame(frame: ctk.CTkFrame):
    """Standard frame styling with rounded corners and slight padding."""
    frame.configure(fg_color=BG_COLOR, corner_radius=12)

def style_label(label: ctk.CTkLabel, size=BASE_FONT_SIZE, weight="normal"):
    label.configure(
        font=ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight),
        text_color=TEXT_COLOR
    )

def style_entry(entry: ctk.CTkEntry, size=BASE_FONT_SIZE, weight="normal"):
    entry.configure(
        height=32,
        corner_radius=12,
        font=ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight),
        fg_color="#1A1A1A",
        text_color=TEXT_COLOR
    )

def style_textbox(textbox: ctk.CTkTextbox, size=BASE_FONT_SIZE):
    textbox.configure(
        font=ctk.CTkFont(family=FONT_FAMILY, size=size),
        fg_color="#1A1A1A",
        text_color=TEXT_COLOR,
        state="disabled"
    )

def style_box_frame(frame: ctk.CTkFrame):
    frame.configure(
        fg_color="transparent",
        border_color=BORDER_COLOR,
        border_width=2,
        corner_radius=10
    )

