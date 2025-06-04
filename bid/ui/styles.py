import customtkinter as ctk

# Современная цветовая схема и шрифт
BG_COLOR = "#181A1B"         # Глубокий тёмный фон
ACCENT_COLOR = "#1E88E5"     # Яркий синий акцент
HOVER_COLOR = "#42A5F5"      # Цвет при наведении
TEXT_COLOR = "#FAFAFA"       # Светлый текст
BORDER_COLOR = "#333333"     # Цвет рамок и делений
FONT_FAMILY = "Inter"  # современный сглаженный шрифт

def style_button(button: ctk.CTkButton):
    """Apply uniform styling for buttons."""
    button.configure(
        corner_radius=12,
        fg_color=ACCENT_COLOR,
        hover_color=HOVER_COLOR,
        text_color=BG_COLOR,
        font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
        pady=6,
        padx=12,
    )

def style_frame(frame: ctk.CTkFrame):
    """Standard background for frames."""
    frame.configure(fg_color=BG_COLOR)

def style_label(label: ctk.CTkLabel, size=12, weight="normal"):
    label.configure(
        font=ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight),
        text_color=TEXT_COLOR,
    )

def style_entry(entry: ctk.CTkEntry, size=12, weight="normal"):
    entry.configure(
        height=36,
        corner_radius=10,
        font=ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight),
        fg_color="#1F1F1F",
        text_color=TEXT_COLOR,
        border_width=1,
        border_color=BORDER_COLOR,
    )

def style_textbox(textbox: ctk.CTkTextbox, size=12):
    textbox.configure(
        font=ctk.CTkFont(family=FONT_FAMILY, size=size),
        fg_color="#1F1F1F",
        text_color=TEXT_COLOR,
        state="disabled",
        corner_radius=8,
    )

def style_box_frame(frame: ctk.CTkFrame):
    frame.configure(
        fg_color="transparent",
        border_color=BORDER_COLOR,
        border_width=1,
        corner_radius=8,
    )

