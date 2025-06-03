import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import pandas as pd
import numpy as np
import re
import datetime
import stavki_ux as ux  # ваш модуль интерфейса
import requests
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import bid


# --- Получение цен и диапазонов ---
try:
    sber_price = bid.fetch_moex_last_price("SBER")
    gazp_price = bid.fetch_moex_last_price("GAZP")

    CENTER1, MIN1, MAX1 = sber_price, sber_price - 10, sber_price + 10
    CENTER2, MIN2, MAX2 = gazp_price, gazp_price - 10, gazp_price + 10

except Exception as e:
    print(f"Ошибка при получении цен: {e}")
    CENTER1, MIN1, MAX1 = 270, 260, 280
    CENTER2, MIN2, MAX2 = 160, 150, 170

def fetch_intraday_prices(ticker):
    """Получает минутные цены за последний торговый день (вчерашний день)"""
    try:
        yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        url = f"https://iss.moex.com/iss/engines/stock/markets/shares/securities/{ticker}/candles.json?from={yesterday}&interval=1"
        r = requests.get(url, timeout=10)
        data = r.json()

        candles = data.get('candles', {}).get('data', [])
        if not candles:
            raise ValueError("Нет данных по свечам.")

        columns = data['candles']['columns']
        idx_time = columns.index('begin')
        idx_price = columns.index('close')
        times = [c[idx_time][11:16] for c in candles]
        prices = [c[idx_price] for c in candles]
        return times, prices
    except Exception as e:
        print(f"Ошибка при получении графика {ticker}: {e}")
        return [], []


def plot_price_chart(ticker, parent_frame):
    global chart_canvas_widget

    times, prices = fetch_intraday_prices(ticker)
    if not times or not prices:
        return

    fig, ax = plt.subplots(figsize=(4.8, 3), dpi=100)
    fig.patch.set_facecolor("#1A1A1A")  # фон графика
    ax.set_facecolor("#1A1A1A")         # фон области графика
    ax.plot(times, prices, linewidth=1.8, color=ux.ACCENT_COLOR)  # основной цвет линии
    ax.set_ylim(min(prices), max(prices))  # ограничим по минимальной и максимальной цене
    ax.set_yticks(np.linspace(min(prices), max(prices), 5))  # 5 делений, равномерно
    ax.set_yticklabels([f"{y:.2f}" for y in np.linspace(min(prices), max(prices), 5)], color=ux.TEXT_COLOR, fontsize=7)

    ax.set_title("График цены за день", fontsize=9, color=ux.TEXT_COLOR)
    ax.set_xticks([])  # убрать все метки X
    ax.set_xlabel("время", fontsize=8, color=ux.TEXT_COLOR, labelpad=10)
    ax.tick_params(axis='y', labelsize=7, colors=ux.TEXT_COLOR)
    ax.spines['bottom'].set_color(ux.TEXT_COLOR)
    ax.spines['left'].set_color(ux.TEXT_COLOR)
    ax.spines['top'].set_color("#1A1A1A")
    ax.spines['right'].set_color("#1A1A1A")
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.3)

    fig.tight_layout()
    chart_canvas = FigureCanvasTkAgg(fig, master=parent_frame)

    if hasattr(plot_price_chart, "canvas_widget"):
        plot_price_chart.canvas_widget.get_tk_widget().destroy()

    plot_price_chart.canvas_widget = chart_canvas
    chart_canvas.draw()
    chart_canvas.get_tk_widget().pack()


# --- Константы ---
INITIAL_BANK = 10_000_000


current_type = None
history = []
embedded_bid_frame = None

def add_to_history(bet_range, amount, coefficient, bet_type: str):
    company = "Сбербанк" if current_type == 1 else "Газпром"
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

# --- Data Initialization ---
def initialize_data(center, min_val, max_val):
    prices = np.arange(min_val, max_val + 1)
    weights = 1 / (((prices - center) / 4) ** 4 + 1) * 100
    base_probs = weights / weights.sum()
    return pd.DataFrame({
        'Цена': prices,
        'Ставки_доп': np.zeros_like(prices, dtype=int),
        'Вероятность': base_probs
    })


def calculate_coefficient(df, start, end):
    sub = df[(df['Цена'] >= start) & (df['Цена'] <= end)]
    p = sub['Вероятность'].sum()
    if p == 0:
        return 1.00  # или можно выбросить исключение
    coef = round(0.95 / p, 3)
    return max(coef, 1.00)


def apply_bet(df, center, min_val, max_val, last_range, amount):
    start, end = last_range
    count = end - start + 1
    add = amount / count
    df['Ставки_доп'] = df['Ставки_доп'].astype(float)
    df.loc[(df['Цена'] >= start) & (df['Цена'] <= end), 'Ставки_доп'] += float(add)
    prices = df['Цена'].values
    base_weights = 1 / (((prices - center) / 4) ** 4 + 1) * 100
    base_probs = base_weights / base_weights.sum()
    base_stakes = base_probs * INITIAL_BANK
    total_stakes = base_stakes + df['Ставки_доп']
    stake_probs = total_stakes / total_stakes.sum()
    df['Вероятность'] = 0.4 * base_probs + 0.6 * stake_probs
    return df

# --- UI Logic ---
df_type1 = initialize_data(CENTER1, MIN1, MAX1)
df_type2 = initialize_data(CENTER2, MIN2, MAX2)
last_range = [None, None]

min_val, max_val, padding, pixel_range = MIN1, MAX1, 10, 400
canvas_width, marker_width = pixel_range + 2 * padding, 6
unit = pixel_range / (max_val - min_val)
val_to_x = lambda v: int((v - min_val) * unit) + padding
x_to_val = lambda x: int(round((x - padding) / unit + min_val))

format_amount = lambda a: '{:,.2f}'.format(a).replace(',', ' ').replace('.', ',')

def format_bet_input():
    digits = re.sub(r'\D', '', entry_bet.get())
    if digits:
        entry_bet.delete(0, 'end')
        entry_bet.insert(0, f"{int(digits):,}".replace(',', '.'))

def update_coef_label():
    x1, x2 = canvas.coords(marker_from)[0], canvas.coords(marker_to)[0]
    v1, v2 = x_to_val(x1), x_to_val(x2)
    if v1 > v2:
        coef_value.configure(text='-'); range_value.configure(text='—'); return
    try:
        df = df_type1 if current_type == 1 else df_type2
        coef = calculate_coefficient(df, v1, v2)
        coef_value.configure(text=f"{coef}")
        range_value.configure(text=f"{v1 - 0.51:.2f}–{v2 + 0.5:.2f}")
        last_range[:] = v1, v2
    except:
        coef_value.configure(text='Ошибка'); range_value.configure(text='—')

def move_marker(event):
    x = min(max(event.x, padding), canvas_width - marker_width - padding)
    item = canvas.find_withtag("current")
    if not item: return
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
        messagebox.showwarning("Внимание", "Сначала выберите диапазон."); return
    try:
        amt = float(entry_bet.get().replace('.', '').replace(',', '.'))
        if amt <= 0: raise ValueError("Ставка должна быть положительной.")
        global df_type1, df_type2
        df = df_type1 if current_type == 1 else df_type2
        center = CENTER1 if current_type == 1 else CENTER2
        df_new = apply_bet(df, center, min_val, max_val, last_range, amt)
        if current_type == 1:
            df_type1 = df_new
        else:
            df_type2 = df_new
        coef = float(coef_value.cget("text"))
        add_to_history(
            (round(last_range[0] - .51, 2), round(last_range[1] + .50, 2)),
            amt,
            coef,
            "Диапазон закрытия",
        )
        update_history_view(); update_coef_label(); update_bet_table(); show_result(amt, coef)
    except Exception as e:
        messagebox.showerror("Ошибка", str(e))

def show_result(amt, coef):
    win = tk.Toplevel(root)
    win.title("Результат ставки"); win.geometry("300x200"); win.configure(bg="#1A1A1A")
    for txt, fnt, col, pady in [
        (f"Коэффициент: {coef:.2f}", (ux.FONT_FAMILY, 14), ux.TEXT_COLOR, 10),
        (f"Возможный выигрыш:\n{format_amount(amt * coef)}", (ux.FONT_FAMILY, 16, 'bold'), ux.ACCENT_COLOR, 10)
    ]:
        tk.Label(win, text=txt, font=fnt, fg=col, bg="#1A1A1A", justify="center").pack(pady=pady)
    tk.Button(win, text="OK", command=win.destroy, font=(ux.FONT_FAMILY, 10), bg="#333", fg=ux.TEXT_COLOR, activebackground=ux.HOVER_COLOR).pack(pady=5)

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
    df = df_type1 if current_type == 1 else df_type2
    tdf = df.copy()
    tdf.columns = ['Цена', 'Капитализация', 'Вероятность']
    tdf['Капитализация'] = tdf['Капитализация'].round(0).astype(int)
    tdf['Вероятность'] = (tdf['Вероятность'] * 100).round(2)
    lines = [f"{'Цена':>10}  {'Капитализация':>15}  {'Вероятность':>12}"] + [
        f"{r['Цена']:>10.2f}  {r['Капитализация']:>15}  {r['Вероятность']:>20.2f}%" for _, r in tdf.iterrows()
    ]
    table_textbox.configure(state="normal")
    table_textbox.delete("1.0", "end")
    table_textbox.insert("1.0", '\n'.join(lines))
    table_textbox.configure(state="disabled")

def draw_axis_labels():
    canvas.delete("tick")
    for i in range(min_val, max_val + 1, 2):
        x = val_to_x(i)
        canvas.create_line(x, 20, x, 30, fill=ux.TEXT_COLOR, tags="tick")
        canvas.create_text(x, 40, text=str(i), font=(ux.FONT_FAMILY, 8), fill=ux.TEXT_COLOR, tags="tick")

# --- UI Init ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
root = ctk.CTk();
screen_width = root.winfo_screenwidth(); screen_height = root.winfo_screenheight()
root.geometry(f"{screen_width}x{screen_height}")
root.title("Ставки на закрытие акций")
root.configure(fg_color=ux.BG_COLOR)

main_container = ctk.CTkScrollableFrame(root, fg_color=ux.BG_COLOR)
main_container.pack(fill="both", expand=True)

menu = ctk.CTkFrame(main_container); ux.style_frame(menu); menu.pack(fill="x", pady=5)
for txt, cmd in [("Ставки", lambda: switch_view("bet")), ("История", lambda: switch_view("history")), ("Информация", lambda: switch_view("info"))]:
    b = ctk.CTkButton(menu, text=txt, command=cmd); ux.style_button(b); b.pack(side="left", padx=10)

def switch_view(view):
    global current_type, min_val, max_val, unit, embedded_bid_frame
    for f in [type_select_frame, bet_frame, history_frame, info_frame]:
        f.pack_forget()
    if view == "bet":
        type_select_frame.pack(fill="both", expand=True)
    elif view == "type1":
        current_type = 1
        min_val, max_val = MIN1, MAX1
        unit = pixel_range / (max_val - min_val)
        type_label.configure(text="Выбран: Сбербанк")
        range_question_label.configure(text="Закрытия акции Сбербанк")
        plot_price_chart("SBER", chart_frame)
        # сначала обновить масштаб
        draw_axis_labels()
        # сбросить координаты маркеров
        x1, x2 = val_to_x(CENTER1 - 2), val_to_x(CENTER1 + 2)
        canvas.coords(marker_from, x1, 15, x1 + marker_width, 35)
        canvas.coords(marker_to, x2, 15, x2 + marker_width, 35)

        # очистка поля ввода
        entry_bet.delete(0, 'end')
        update_coef_label()
        update_bet_table()
        if embedded_bid_frame:
            embedded_bid_frame.destroy()
        embedded_bid_frame = bid.open_bid_window(
            parent=left_side,
            table_parent=right_side,
            log_bet=lambda r,a,c,kind: add_to_history(r, a, c, kind),
            center_price=CENTER1,
        )
        embedded_bid_frame.pack(pady=10, fill="x")
        bet_frame.pack(fill="both", expand=True)

    elif view == "type2":
        current_type = 2
        min_val, max_val = MIN2, MAX2
        unit = pixel_range / (max_val - min_val)
        type_label.configure(text="Выбран: Газпром")
        range_question_label.configure(text="Закрытия акции Газпром")
        plot_price_chart("GAZP", chart_frame)
        draw_axis_labels()
        x1, x2 = val_to_x(CENTER2 - 2), val_to_x(CENTER2 + 2)
        canvas.coords(marker_from, x1, 15, x1 + marker_width, 35)
        canvas.coords(marker_to, x2, 15, x2 + marker_width, 35)

        entry_bet.delete(0, 'end')
        update_coef_label()
        update_bet_table()
        if embedded_bid_frame:
            embedded_bid_frame.destroy()
        embedded_bid_frame = bid.open_bid_window(
            parent=left_side,
            table_parent=right_side,
            log_bet=lambda r,a,c,kind: add_to_history(r, a, c, kind),
            center_price=CENTER2,
        )
        embedded_bid_frame.pack(pady=10, fill="x")
        bet_frame.pack(fill="both", expand=True)
    elif view == "history":
        update_history_view(); history_frame.pack(fill="both", expand=True)
    elif view == "info":
        info_textbox.configure(state="normal"); info_textbox.delete("1.0", "end")
        info_textbox.insert("1.0", "Компания создана в 2025 году холдингом Beorn.")
        info_textbox.configure(state="disabled"); info_frame.pack(fill="both", expand=True)


# --- Frames ---
type_select_frame = ctk.CTkFrame(main_container); ux.style_frame(type_select_frame)
for txt, val in [("Сбербанк", "type1"), ("Газпром", "type2")]:
    b = ctk.CTkButton(type_select_frame, text=txt, command=lambda v=val: switch_view(v))
    ux.style_button(b); b.pack(pady=20)

bet_frame = ctk.CTkFrame(main_container); ux.style_frame(bet_frame)

left_side = ctk.CTkFrame(bet_frame); ux.style_frame(left_side)
left_side.pack(side="left", fill="both", expand=True)
right_side = ctk.CTkFrame(bet_frame); ux.style_frame(right_side)
right_side.pack(side="right", fill="both", expand=True)

type_label = ctk.CTkLabel(left_side, text="", font=(ux.FONT_FAMILY, 16, "bold"), text_color=ux.ACCENT_COLOR)
type_label.pack(pady=5)
chart_frame = ctk.CTkFrame(left_side); ux.style_frame(chart_frame); chart_frame.pack(pady=5)

range_question_label = ctk.CTkLabel(left_side, text="", font=(ux.FONT_FAMILY, 12))
ux.style_label(range_question_label)
range_question_label.pack(pady=5)


scale = ctk.CTkFrame(left_side); ux.style_frame(scale); scale.pack(pady=10)
canvas = tk.Canvas(scale, width=canvas_width, height=60, bg=ux.BG_COLOR, highlightthickness=0)
canvas.pack(); canvas.create_line(padding, 25, canvas_width - padding, 25, width=2, fill=ux.TEXT_COLOR)
draw_axis_labels()

x1, x2 = val_to_x(108), val_to_x(112)
marker_from = canvas.create_rectangle(x1, 15, x1 + marker_width, 35, fill=ux.ACCENT_COLOR, tags="marker")
marker_to = canvas.create_rectangle(x2, 15, x2 + marker_width, 35, fill=ux.ACCENT_COLOR, tags="marker")
canvas.tag_bind("marker", "<B1-Motion>", move_marker)

result = ctk.CTkFrame(left_side); ux.style_frame(result); result.pack(pady=10)
def create_res(label_text):
    frame = ctk.CTkFrame(result); ux.style_frame(frame); frame.pack(side="left", padx=10)
    label = ctk.CTkLabel(frame, text=label_text); ux.style_label(label, 12); label.pack(side="left")
    box = ctk.CTkFrame(frame); ux.style_box_frame(box); box.pack(side="left", padx=5)
    value = ctk.CTkLabel(box, text="—" if "Диапазон" in label_text else "-"); ux.style_label(value, 12); value.pack(padx=6, pady=2)
    return value

range_value = create_res("Диапазон:"); coef_value = create_res("Коэффициент:")

frame_bet = ctk.CTkFrame(left_side); ux.style_frame(frame_bet); frame_bet.pack(pady=10)
label_bet = ctk.CTkLabel(frame_bet, text="Ставка:"); ux.style_label(label_bet); label_bet.pack(side="left")
entry_bet = ctk.CTkEntry(frame_bet, width=100); ux.style_entry(entry_bet); entry_bet.configure(font=(ux.FONT_FAMILY, 12, "bold"))
entry_bet.pack(side="left", padx=5); entry_bet.bind("<KeyRelease>", lambda e: format_bet_input())
ctk.CTkButton(frame_bet, text="Сделать ставку", command=on_bet_click, fg_color=ux.ACCENT_COLOR, hover_color=ux.HOVER_COLOR, text_color=ux.BG_COLOR).pack(side="left", padx=10)

# встроенный интерфейс из bid.py будет инициализирован при выборе компании

mono = ctk.CTkFont(family="Courier New", size=12)
table_frame = ctk.CTkFrame(right_side); ux.style_frame(table_frame); table_frame.pack(pady=10)
table_textbox = ctk.CTkTextbox(table_frame, width=460, height=340); ux.style_textbox(table_textbox)
table_textbox.configure(font=mono); table_textbox.pack()

history_frame = ctk.CTkFrame(main_container); ux.style_frame(history_frame)
history_textbox = ctk.CTkTextbox(history_frame, width=460, height=400)
ux.style_textbox(history_textbox)
history_textbox.pack(padx=10, pady=10)
history_textbox.tag_config("win", font=(ux.FONT_FAMILY, 12, "bold"), foreground=ux.ACCENT_COLOR)
history_textbox.tag_config("sep", foreground=ux.BORDER_COLOR)

info_frame = ctk.CTkFrame(main_container); ux.style_frame(info_frame)
info_textbox = ctk.CTkTextbox(info_frame, width=460, height=400); ux.style_textbox(info_textbox); info_textbox.pack(padx=10, pady=10)

update_coef_label(); update_bet_table()
root.bind("<Return>", lambda e: on_bet_click())
switch_view("bet")
root.mainloop()
