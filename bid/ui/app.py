import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import re
import pandas as pd
import datetime

from bid.data.moex import (
    fetch_moex_last_price,
    plot_price_chart,
)
from bid.data.crypto import (
    fetch_crypto_last_price,
    plot_crypto_price_chart,
)
from bid.logic.probability import (
    initialize_table,
    recalculate_all_probabilities,
    update_bet,
    get_prob,
    process_express,
    initialize_data,
    calculate_coefficient,
    apply_bet,
)
from bid.ui import styles as ux
from bid.ui.bid_window import open_bid_window

try:
    DEFAULT_CENTER_PRICE = fetch_moex_last_price("SBER")
except Exception as e:
    print(f"Ошибка при получении цены: {e}")
    DEFAULT_CENTER_PRICE = 110

# --- market price ranges ----------------------------------------------------
try:
    sber_price = fetch_moex_last_price("SBER")
    gazp_price = fetch_moex_last_price("GAZP")
    btc_price = fetch_crypto_last_price("BTC")
    eth_price = fetch_crypto_last_price("ETH")
    if btc_price == 0 or eth_price == 0:
        raise ValueError("crypto price unavailable")
    CENTER1, MIN1, MAX1 = sber_price, sber_price - 10, sber_price + 10
    CENTER2, MIN2, MAX2 = gazp_price, gazp_price - 10, gazp_price + 10
    CENTER3, MIN3, MAX3 = btc_price, btc_price - 1000, btc_price + 1000
    CENTER4, MIN4, MAX4 = eth_price, eth_price - 1000, eth_price + 1000
except Exception as e:
    print(f"Ошибка при получении цен: {e}")
    CENTER1, MIN1, MAX1 = 270, 260, 280
    CENTER2, MIN2, MAX2 = 160, 150, 170
    CENTER3, MIN3, MAX3 = 0, -1000, 1000
    CENTER4, MIN4, MAX4 = 0, -1000, 1000

# --- global state -----------------------------------------------------------
current_type = None
history = []
embedded_bid_frame = None
embedded_bid_table_frame = None
currency_symbol = "₽"
current_center = CENTER1


df_type1 = initialize_data(CENTER1, MIN1, MAX1)
df_type2 = initialize_data(CENTER2, MIN2, MAX2)
df_type3 = initialize_data(CENTER3, MIN3, MAX3)
df_type4 = initialize_data(CENTER4, MIN4, MAX4)
price_table1 = initialize_table(CENTER1)
price_table2 = initialize_table(CENTER2)
price_table3 = initialize_table(CENTER3)
price_table4 = initialize_table(CENTER4)
last_range = [None, None]


# --- higher-level UI -------------------------------------------------------

def add_to_history(bet_range, amount, coefficient, bet_type: str):
    company_map = {1: "Сбербанк", 2: "Газпром", 3: "BTC", 4: "ETH"}
    company = company_map.get(current_type, "-")
    entry = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "range": f"{bet_range[0]}–{bet_range[1]}",
        "amount": amount,
        "coefficient": coefficient,
        "company": company,
        "bet_type": bet_type,
    }
    history.append(entry)


def get_history():
    return history.copy()


min_val, max_val, padding, pixel_range = MIN1, MAX1, 10, 400
canvas_width, marker_width = pixel_range + 2 * padding, 6
unit = pixel_range / (max_val - min_val)
val_to_x = lambda v: int((v - min_val) * unit) + padding
x_to_val = lambda x: int(round((x - padding) / unit + min_val))

def update_dimensions(window_width: int):
    """Recalculate global geometry values based on window width."""
    global pixel_range, canvas_width, unit, val_to_x, x_to_val
    pixel_range = int(window_width * 0.4)
    canvas_width = pixel_range + 2 * padding
    unit = pixel_range / (max_val - min_val)
    val_to_x = lambda v: int((v - min_val) * unit) + padding
    x_to_val = lambda x: int(round((x - padding) / unit + min_val))

format_amount = lambda a: "{:,.2f}".format(a).replace(",", " ").replace(".", ",")


entry_bet = None
canvas = None
marker_from = None
marker_to = None
coef_value = None
range_value = None
root = None
history_textbox = None
info_textbox = None
table_textbox = None


def format_bet_input():
    digits = re.sub(r"\D", "", entry_bet.get())
    if digits:
        entry_bet.delete(0, "end")
        entry_bet.insert(0, f"{int(digits):,}".replace(",", "."))


def update_coef_label():
    x1, x2 = canvas.coords(marker_from)[0], canvas.coords(marker_to)[0]
    v1, v2 = x_to_val(x1), x_to_val(x2)
    if v1 > v2:
        coef_value.configure(text="-")
        range_value.configure(text="—")
        return
    try:
        df_map = {1: df_type1, 2: df_type2, 3: df_type3, 4: df_type4}
        df = df_map.get(current_type)
        coef = calculate_coefficient(df, v1, v2)
        coef_value.configure(text=f"{coef}")
        range_value.configure(text=f"{v1 - 0.51:.2f}–{v2 + 0.5:.2f}")
        last_range[:] = v1, v2
    except Exception:
        coef_value.configure(text="Ошибка")
        range_value.configure(text="—")


def move_marker(event):
    x = min(max(event.x, padding), canvas_width - marker_width - padding)
    item = canvas.find_withtag("current")
    if not item:
        return
    if item[0] == marker_from:
        xt = canvas.coords(marker_to)[0]
        if x + marker_width > xt:
            nx = min(xt + (x + marker_width - xt), canvas_width - marker_width - padding)
            canvas.coords(marker_to, nx, 15, nx + marker_width, 35)
            x = nx - marker_width
        canvas.coords(marker_from, x, 15, x + marker_width, 35)
    else:
        xf = canvas.coords(marker_from)[0]
        if x < xf + marker_width:
            nx = max(padding, xf + (x - (xf + marker_width)))
            canvas.coords(marker_from, nx, 15, nx + marker_width, 35)
            x = nx + marker_width
        canvas.coords(marker_to, x, 15, x + marker_width, 35)
    update_coef_label()


def on_bet_click():
    if last_range[0] is None:
        messagebox.showwarning("Внимание", "Сначала выберите диапазон.")
        return
    try:
        amt = float(entry_bet.get().replace('.', '').replace(',', '.'))
        if amt <= 0:
            raise ValueError("Ставка должна быть положительной.")
        global df_type1, df_type2, df_type3, df_type4
        df_map = {1: df_type1, 2: df_type2, 3: df_type3, 4: df_type4}
        center_map = {1: CENTER1, 2: CENTER2, 3: CENTER3, 4: CENTER4}
        df = df_map.get(current_type)
        center = center_map.get(current_type)
        df_new = apply_bet(df, center, min_val, max_val, last_range, amt)
        if current_type == 1:
            df_type1 = df_new
        elif current_type == 2:
            df_type2 = df_new
        elif current_type == 3:
            df_type3 = df_new
        elif current_type == 4:
            df_type4 = df_new
        coef = float(coef_value.cget("text"))
        add_to_history(
            (round(last_range[0] - 0.51, 2), round(last_range[1] + 0.50, 2)),
            amt,
            coef,
            "Диапазон закрытия",
        )
        update_history_view()
        update_coef_label()
        update_bet_table()
        show_result(amt, coef)
    except Exception as e:
        messagebox.showerror("Ошибка", str(e))


def show_result(amt, coef):
    win = tk.Toplevel(root)
    win.title("Результат ставки")
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    w = int(sw * 0.3)
    h = int(sh * 0.3)
    win.geometry(f"{w}x{h}+{(sw - w)//2}+{(sh - h)//2}")
    win.configure(bg="#1A1A1A")
    for txt, fnt, col, pady in [
        (f"Коэффициент: {coef:.2f}", ctk.CTkFont(family=ux.FONT_FAMILY, size=14), ux.TEXT_COLOR, 10),
        (f"Возможный выигрыш:\n{format_amount(amt * coef)}", ctk.CTkFont(family=ux.FONT_FAMILY, size=16, weight="bold"), ux.ACCENT_COLOR, 10),
    ]:
        tk.Label(win, text=txt, font=fnt, fg=col, bg="#1A1A1A", justify="center").pack(pady=pady)
    tk.Button(win, text="OK", command=win.destroy, font=ctk.CTkFont(family=ux.FONT_FAMILY, size=10), bg="#333", fg=ux.TEXT_COLOR, activebackground=ux.HOVER_COLOR).pack(pady=5)


def update_history_view():
    history_textbox.configure(state="normal")
    history_textbox.delete("1.0", "end")
    hist = get_history()
    for h in hist:
        history_textbox.insert("end", f"{h['timestamp']} — {h['company']} | {h['bet_type']}\n")
        history_textbox.insert("end", f"Ставка: {h['amount']} на {h['range']} (Коэффициент: {h['coefficient']})\n")
        win = format_amount(h['amount'] * h['coefficient'])
        history_textbox.insert("end", f"Возможный выигрыш: {win}\n", "win")
        history_textbox.insert("end", "\u2014" * 40 + "\n", "sep")
    if not hist:
        history_textbox.insert("1.0", "История пуста.")
    history_textbox.configure(state="disabled")


def update_bet_table():
    df_map = {1: df_type1, 2: df_type2, 3: df_type3, 4: df_type4}
    df = df_map.get(current_type)
    if df is None:
        table_textbox.configure(state="normal")
        table_textbox.delete("1.0", "end")
        table_textbox.insert("1.0", "Выберите актив")
        table_textbox.configure(state="disabled")
        return
    tdf = df.copy()
    tdf.columns = ["Цена", "Капитализация", "Вероятность"]
    tdf["Капитализация"] = tdf["Капитализация"].round(0).astype(int)
    tdf["Вероятность"] = (tdf["Вероятность"] * 100).round(2)
    lines = [f"{'Цена':>10}  {'Капитализация':>15}  {'Вероятность':>12}"] + [
        f"{r['Цена']:>10.2f}  {r['Капитализация']:>15}  {r['Вероятность']:>20.2f}%" for _, r in tdf.iterrows()
    ]
    table_textbox.configure(state="normal")
    table_textbox.delete("1.0", "end")
    table_textbox.insert("1.0", "\n".join(lines))
    table_textbox.configure(state="disabled")


def draw_axis_labels():
    canvas.delete("tick")
    step = max(2, (max_val - min_val) // 10)
    for i in range(min_val, max_val + 1, step):
        x = val_to_x(i)
        canvas.create_line(x, 20, x, 30, fill=ux.TEXT_COLOR, tags="tick")
        color = ux.ACCENT_COLOR if i == current_center else ux.TEXT_COLOR
        canvas.create_text(
            x,
            40,
            text=f"{i} {currency_symbol}",
            font=ctk.CTkFont(family=ux.FONT_FAMILY, size=8),
            fill=color,
            tags="tick",
        )


def switch_view(view):
    global current_type, min_val, max_val, unit, embedded_bid_frame, embedded_bid_table_frame
    global currency_symbol, current_center
    for f in [type_select_frame, crypto_select_frame, bet_frame, history_frame, info_frame]:
        f.pack_forget()
    if view == "bet":
        type_select_frame.pack(fill="both", expand=True)
    elif view == "crypto":
        crypto_select_frame.pack(fill="both", expand=True)
    elif view == "type1":
        current_type = 1
        currency_symbol = "₽"
        current_center = CENTER1
        min_val, max_val = MIN1, MAX1
        unit = pixel_range / (max_val - min_val)
        type_label.configure(text="Выбран: Сбербанк")
        range_question_label.configure(text="Закрытия акции Сбербанк")
        plot_price_chart("SBER", chart_frame)
        draw_axis_labels()
        x1, x2 = val_to_x(CENTER1 - 2), val_to_x(CENTER1 + 2)
        canvas.coords(marker_from, x1, 15, x1 + marker_width, 35)
        canvas.coords(marker_to, x2, 15, x2 + marker_width, 35)
        entry_bet.delete(0, "end")
        update_coef_label()
        update_bet_table()
        if embedded_bid_frame:
            embedded_bid_frame.destroy()
        if embedded_bid_table_frame:
            embedded_bid_table_frame.destroy()
        embedded_bid_frame, embedded_bid_table_frame, _ = open_bid_window(
            parent=left_side,
            table_parent=right_side,
            log_bet=lambda r, a, c, kind: add_to_history(r, a, c, kind),
            center_price=CENTER1,
            table=price_table1,
            axis_width=pixel_range,
        )
        embedded_bid_frame.pack(pady=10, fill="x")
        bet_frame.pack(fill="both", expand=True)
    elif view == "type2":
        current_type = 2
        currency_symbol = "₽"
        current_center = CENTER2
        min_val, max_val = MIN2, MAX2
        unit = pixel_range / (max_val - min_val)
        type_label.configure(text="Выбран: Газпром")
        range_question_label.configure(text="Закрытия акции Газпром")
        plot_price_chart("GAZP", chart_frame)
        draw_axis_labels()
        x1, x2 = val_to_x(CENTER2 - 2), val_to_x(CENTER2 + 2)
        canvas.coords(marker_from, x1, 15, x1 + marker_width, 35)
        canvas.coords(marker_to, x2, 15, x2 + marker_width, 35)
        entry_bet.delete(0, "end")
        update_coef_label()
        update_bet_table()
        if embedded_bid_frame:
            embedded_bid_frame.destroy()
        if embedded_bid_table_frame:
            embedded_bid_table_frame.destroy()
        embedded_bid_frame, embedded_bid_table_frame, _ = open_bid_window(
            parent=left_side,
            table_parent=right_side,
            log_bet=lambda r, a, c, kind: add_to_history(r, a, c, kind),
            center_price=CENTER2,
            table=price_table2,
            axis_width=pixel_range,
        )
        embedded_bid_frame.pack(pady=10, fill="x")
        bet_frame.pack(fill="both", expand=True)
    elif view == "btc":
        current_type = 3
        currency_symbol = "$"
        current_center = CENTER3
        min_val, max_val = MIN3, MAX3
        unit = pixel_range / (max_val - min_val)
        type_label.configure(text="Выбран: BTC")
        range_question_label.configure(text="Курс BTC")
        plot_crypto_price_chart("BTC", chart_frame)
        draw_axis_labels()
        x1, x2 = val_to_x(CENTER3 - 200), val_to_x(CENTER3 + 200)
        canvas.coords(marker_from, x1, 15, x1 + marker_width, 35)
        canvas.coords(marker_to, x2, 15, x2 + marker_width, 35)
        entry_bet.delete(0, "end")
        update_coef_label()
        update_bet_table()
        if embedded_bid_frame:
            embedded_bid_frame.destroy()
        if embedded_bid_table_frame:
            embedded_bid_table_frame.destroy()
        embedded_bid_frame, embedded_bid_table_frame, _ = open_bid_window(
            parent=left_side,
            table_parent=right_side,
            log_bet=lambda r, a, c, kind: add_to_history(r, a, c, kind),
            center_price=CENTER3,
            table=price_table3,
            axis_width=pixel_range,
        )
        embedded_bid_frame.pack(pady=10, fill="x")
        bet_frame.pack(fill="both", expand=True)
    elif view == "eth":
        current_type = 4
        currency_symbol = "$"
        current_center = CENTER4
        min_val, max_val = MIN4, MAX4
        unit = pixel_range / (max_val - min_val)
        type_label.configure(text="Выбран: ETH")
        range_question_label.configure(text="Курс ETH")
        plot_crypto_price_chart("ETH", chart_frame)
        draw_axis_labels()
        x1, x2 = val_to_x(CENTER4 - 200), val_to_x(CENTER4 + 200)
        canvas.coords(marker_from, x1, 15, x1 + marker_width, 35)
        canvas.coords(marker_to, x2, 15, x2 + marker_width, 35)
        entry_bet.delete(0, "end")
        update_coef_label()
        update_bet_table()
        if embedded_bid_frame:
            embedded_bid_frame.destroy()
        if embedded_bid_table_frame:
            embedded_bid_table_frame.destroy()
        embedded_bid_frame, embedded_bid_table_frame, _ = open_bid_window(
            parent=left_side,
            table_parent=right_side,
            log_bet=lambda r, a, c, kind: add_to_history(r, a, c, kind),
            center_price=CENTER4,
            table=price_table4,
            axis_width=pixel_range,
        )
        embedded_bid_frame.pack(pady=10, fill="x")
        bet_frame.pack(fill="both", expand=True)
    elif view == "history":
        update_history_view()
        history_frame.pack(fill="both", expand=True)
    elif view == "info":
        info_textbox.configure(state="normal")
        info_textbox.delete("1.0", "end")
        info_textbox.insert("1.0", "Компания создана в 2025 году холдингом Beorn.")
        info_textbox.configure(state="disabled")
        info_frame.pack(fill="both", expand=True)


def run_app():
    global root, entry_bet, canvas, marker_from, marker_to, coef_value, range_value
    global history_textbox, info_textbox, table_textbox
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    root = ctk.CTk()
    scaling = root.winfo_fpixels("1i") / 96
    ctk.set_widget_scaling(scaling)
    ctk.set_window_scaling(scaling)
    root.tk.call("tk", "scaling", scaling)

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    width = int(screen_width * 0.8)
    height = int(screen_height * 0.8)
    root.geometry(f"{width}x{height}+{(screen_width - width)//2}+{(screen_height - height)//2}")
    update_dimensions(width)
    root.title("Ставки на закрытие акций")
    root.configure(fg_color=ux.BG_COLOR)

    main_container = ctk.CTkScrollableFrame(root, fg_color=ux.BG_COLOR)
    main_container.pack(fill="both", expand=True)

    menu = ctk.CTkFrame(main_container)
    ux.style_frame(menu)
    menu.pack(fill="both", expand=True, pady=5)
    for txt, cmd in [
        ("Акции", lambda: switch_view("bet")),
        ("Криптовалюта", lambda: switch_view("crypto")),
        ("История", lambda: switch_view("history")),
        ("Информация", lambda: switch_view("info")),
    ]:
        b = ctk.CTkButton(menu, text=txt, command=cmd)
        ux.style_button(b)
        b.pack(side="left", padx=10)

    global type_select_frame, crypto_select_frame, bet_frame, history_frame, info_frame
    global left_side, right_side, type_label, chart_frame, range_question_label

    type_select_frame = ctk.CTkFrame(main_container)
    ux.style_frame(type_select_frame)
    for txt, val in [("Сбербанк", "type1"), ("Газпром", "type2")]:
        b = ctk.CTkButton(type_select_frame, text=txt, command=lambda v=val: switch_view(v))
        ux.style_button(b)
        b.pack(pady=20)

    crypto_select_frame = ctk.CTkFrame(main_container)
    ux.style_frame(crypto_select_frame)
    for txt, val in [("BTC", "btc"), ("ETH", "eth")]:
        cb = ctk.CTkButton(crypto_select_frame, text=txt, command=lambda v=val: switch_view(v))
        ux.style_button(cb)
        cb.pack(pady=20)

    bet_frame = ctk.CTkFrame(main_container)
    ux.style_frame(bet_frame)

    left_side = ctk.CTkFrame(bet_frame)
    ux.style_frame(left_side)
    left_side.pack(side="left", fill="both", expand=True)
    right_side = ctk.CTkFrame(bet_frame)
    ux.style_frame(right_side)
    right_side.pack(side="right", fill="both", expand=True)

    type_label = ctk.CTkLabel(
        left_side,
        text="",
        font=ctk.CTkFont(family=ux.FONT_FAMILY, size=16, weight="bold"),
        text_color=ux.ACCENT_COLOR,
    )
    type_label.pack(pady=5)
    chart_frame = ctk.CTkFrame(left_side)
    ux.style_frame(chart_frame)
    chart_frame.pack(pady=5, fill="both", expand=True)

    range_question_label = ctk.CTkLabel(
        left_side,
        text="",
        font=ctk.CTkFont(family=ux.FONT_FAMILY, size=12),
    )
    ux.style_label(range_question_label, 12)
    range_question_label.pack(pady=5)

    global scale
    scale = ctk.CTkFrame(left_side)
    ux.style_frame(scale)
    scale.pack(pady=10, fill="both", expand=True)
    canvas = tk.Canvas(scale, width=canvas_width, height=60, bg=ux.BG_COLOR, highlightthickness=0)
    canvas.pack()
    canvas.create_line(padding, 25, canvas_width - padding, 25, width=2, fill=ux.TEXT_COLOR)
    draw_axis_labels()

    x1, x2 = val_to_x(CENTER1 - 2), val_to_x(CENTER1 + 2)
    marker_from = canvas.create_rectangle(x1, 15, x1 + marker_width, 35, fill=ux.ACCENT_COLOR, tags="marker")
    marker_to = canvas.create_rectangle(x2, 15, x2 + marker_width, 35, fill=ux.ACCENT_COLOR, tags="marker")
    canvas.tag_bind("marker", "<B1-Motion>", move_marker)

    result = ctk.CTkFrame(left_side)
    ux.style_frame(result)
    result.pack(pady=10)

    def create_res(label_text):
        frame = ctk.CTkFrame(result)
        ux.style_frame(frame)
        frame.pack(side="left", padx=10)
        label = ctk.CTkLabel(frame, text=label_text)
        ux.style_label(label, 12)
        label.pack(side="left")
        box = ctk.CTkFrame(frame, width=80)
        ux.style_box_frame(box)
        box.pack(side="left", padx=5)
        value = ctk.CTkLabel(box, text="—" if "Диапазон" in label_text else "-")
        ux.style_label(value, 12)
        value.pack(padx=6, pady=2)
        return value

    global range_value, coef_value
    range_value = create_res("Диапазон:")
    coef_value = create_res("Коэффициент:")

    frame_bet = ctk.CTkFrame(left_side)
    ux.style_frame(frame_bet)
    frame_bet.pack(pady=10)
    label_bet = ctk.CTkLabel(frame_bet, text="Ставка:")
    ux.style_label(label_bet)
    label_bet.pack(side="left")
    entry_bet = ctk.CTkEntry(frame_bet, width=100)
    ux.style_entry(entry_bet)
    entry_bet.configure(font=ctk.CTkFont(family=ux.FONT_FAMILY, size=12, weight="bold"))
    entry_bet.pack(side="left", padx=5)
    entry_bet.bind("<KeyRelease>", lambda e: format_bet_input())
    btn_main_bet = ctk.CTkButton(frame_bet, text="Сделать ставку", command=on_bet_click)
    ux.style_button(btn_main_bet)
    btn_main_bet.pack(side="left", padx=5)

    mono = ctk.CTkFont(family="Courier New", size=12)
    table_frame = ctk.CTkFrame(right_side)
    ux.style_frame(table_frame)
    table_frame.pack(pady=10, fill="both", expand=True)
    table_textbox = ctk.CTkTextbox(table_frame, width=460, height=340)
    ux.style_textbox(table_textbox)
    table_textbox.configure(font=mono)
    table_textbox.pack()

    history_frame = ctk.CTkFrame(main_container)
    ux.style_frame(history_frame)
    history_textbox = ctk.CTkTextbox(history_frame, width=460, height=400)
    ux.style_textbox(history_textbox)
    history_textbox.pack(padx=10, pady=10)

    bold_font = ctk.CTkFont(family=ux.FONT_FAMILY, size=12, weight="bold")
    history_textbox.tag_config("win", foreground=ux.ACCENT_COLOR)
    history_textbox._textbox.tag_config("win", font=bold_font)
    history_textbox.tag_config("sep", foreground=ux.BORDER_COLOR)

    info_frame = ctk.CTkFrame(main_container)
    ux.style_frame(info_frame)
    info_textbox = ctk.CTkTextbox(info_frame, width=460, height=400)
    ux.style_textbox(info_textbox)
    info_textbox.pack(padx=10, pady=10)

    update_coef_label()
    update_bet_table()
    root.bind("<Return>", lambda e: on_bet_click())
    switch_view("bet")
    root.mainloop()
