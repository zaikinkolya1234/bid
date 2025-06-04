import customtkinter as ctk

# Цвета и шрифт — тёмный стиль в духе интерфейса на скриншоте
BG_COLOR = "#0D0D0D"         # Основной фон
ACCENT_COLOR = "#F5C000"     # Яркий акцент (золото)
HOVER_COLOR = "#FFDD55"      # Цвет при наведении
TEXT_COLOR = "#E0E0E0"       # Светлый текст
BORDER_COLOR = "#333333"     # Цвет рамок и делений
FONT_FAMILY = "Segoe UI"

def style_button(button: ctk.CTkButton):
    button.configure(
        corner_radius=10,
        fg_color=ACCENT_COLOR,
        hover_color=HOVER_COLOR,
        text_color="black",  # ← здесь устанавливается чёрный цвет текста
        font=(FONT_FAMILY, 10)
    )

def style_frame(frame: ctk.CTkFrame):
    frame.configure(fg_color=BG_COLOR)

def style_label(label: ctk.CTkLabel, size=10):
    label.configure(
        font=(FONT_FAMILY, size),
        text_color=TEXT_COLOR
    )

def style_entry(entry: ctk.CTkEntry):
    entry.configure(
        height=30,
        corner_radius=10,
        font=(FONT_FAMILY, 10),
        fg_color="#1A1A1A",
        text_color=TEXT_COLOR
    )

def style_textbox(textbox: ctk.CTkTextbox):
    textbox.configure(
        font=(FONT_FAMILY, 10),
        fg_color="#1A1A1A",
        text_color=TEXT_COLOR,
        state="disabled"
    )

def style_box_frame(frame: ctk.CTkFrame):
    frame.configure(
        fg_color="transparent",
        border_color=BORDER_COLOR,
        border_width=2,
        corner_radius=8
    )

