import math
import requests
import customtkinter as ctk
import tkinter as tk
import stavki_ux as ux

def fetch_moex_last_price(ticker: str) -> int:
    """Return last traded price for the given ticker from MOEX."""
    url = f"https://iss.moex.com/iss/engines/stock/markets/shares/securities/{ticker}.json"
    r = requests.get(url, timeout=10)
    data = r.json()
    market_data = data['marketdata']['data'][0]
    idx = data['marketdata']['columns'].index('LAST')
    return round(float(market_data[idx]))

try:
    DEFAULT_CENTER_PRICE = fetch_moex_last_price("SBER")
except Exception as e:
    print(f"Ошибка при получении цены: {e}")
    DEFAULT_CENTER_PRICE = 110

def probability(x: float, center_price: float) -> float:
    """Return base probability for the given price."""
    numerator = 100
    denominator = ((x - center_price) / 4) ** 4 + 1
    return numerator / denominator

def initialize_table(center_price: float):
    price_range = range(center_price - 10, center_price + 11)
    table = []
    for price in price_range:
        prob = round(probability(price, center_price), 4)
        table.append({
            'Цена': price,
            'Вероятность': prob,
            'Ставка_да': 0.0,
            'Ставка_нет': 0.0
        })
    return table

def recalculate_all_probabilities(table, center_price: float):
    for row in table:
        price = row['Цена']
        y1 = row['Ставка_да']
        y2 = row['Ставка_нет']
        P0 = probability(price, center_price)
        h1 = P0 * 100_000
        h2 = (100 - P0) * 100_000
        denominator = y1 + y2 + h1 + h2
        new_prob = round(0.5 * P0 + 0.5 * ((y1 + h1) / denominator * 100), 4)
        row['Вероятность'] = new_prob

def update_bet(table, price, amount, bet_type):
    for row in table:
        if row['Цена'] == price:
            if bet_type == 'да':
                row['Ставка_да'] = round(row['Ставка_да'] + amount, 2)
            else:
                row['Ставка_нет'] = round(row['Ставка_нет'] + amount, 2)
            break

def get_prob(table, price):
    for row in table:
        if row['Цена'] == price:
            return row['Вероятность'] / 100
    return None

def process_express(table, price1, price2, amount):
    p1 = get_prob(table, price1)
    p2 = get_prob(table, price2)
    if not p1 or not p2:
        print("Ошибка: цены вне диапазона.")
        return

    w1 = math.log(1 / p1) / (math.log(1 / p1) + math.log(1 / p2))
    w2 = 1 - w1

    update_bet(table, price1, amount * w1, bet_type='нет')
    update_bet(table, price2, amount * w2, bet_type='нет')

def open_bid_window(parent=None, log_bet=None, center_price=None):
    """Open graphical interface for placing bets on price range or target.

    If *parent* is provided, returns a frame with the interface embedded.
    Otherwise creates a standalone window and starts the mainloop.
    """
    if center_price is None:
        center_price = DEFAULT_CENTER_PRICE

    price_range = range(center_price - 10, center_price + 11)
    table = initialize_table(center_price)

    ctk.set_appearance_mode("dark")
    if parent is None:
        root = ctk.CTk()
        root.title("Ставки")
        root.geometry("500x500")
        container = root
    else:
        container = ctk.CTkFrame(parent, fg_color=ux.BG_COLOR)
        root = None

    # --- layout helpers ---
    def add_row(widget, **pack_opts):
        widget.pack(fill="x", pady=5, padx=10, **pack_opts)

    def create_res(parent, label_text):
        frame = ctk.CTkFrame(parent)
        ux.style_frame(frame)
        frame.pack(side="left", padx=10)
        lbl = ctk.CTkLabel(frame, text=label_text)
        ux.style_label(lbl, 12)
        lbl.pack(side="left")
        box = ctk.CTkFrame(frame)
        ux.style_box_frame(box)
        box.pack(side="left", padx=5)
        val = ctk.CTkLabel(box, text="—" if "Диапазон" in label_text else "-")
        ux.style_label(val, 12)
        val.pack(padx=6, pady=2)
        return val

    min_val = price_range.start
    max_val = price_range.stop - 1
    padding = 10
    width = 320
    marker_w = 6
    unit = width / (max_val - min_val)
    val_to_x = lambda v: int((v - min_val) * unit) + padding
    x_to_val = lambda x: int(round((x - padding) / unit + min_val))

    def draw_axis(canv):
        canv.create_line(padding, 25, width + padding, 25, width=2, fill=ux.TEXT_COLOR)
        for i in range(min_val, max_val + 1, 2):
            x = val_to_x(i)
            canv.create_line(x, 20, x, 30, fill=ux.TEXT_COLOR)
            canv.create_text(x, 40, text=str(i), fill=ux.TEXT_COLOR, font=(ux.FONT_FAMILY, 8))

    # --- Range selection ---
    lbl_range = ctk.CTkLabel(container, text="Выбор диапазона")
    ux.style_label(lbl_range, 12)
    add_row(lbl_range)

    canvas_range = tk.Canvas(container, width=width + 2 * padding, height=60,
                             bg=ux.BG_COLOR, highlightthickness=0)
    add_row(canvas_range)
    draw_axis(canvas_range)

    left_marker = canvas_range.create_rectangle(val_to_x(center_price - 2), 15,
                                                val_to_x(center_price - 2) + marker_w, 35,
                                                fill=ux.ACCENT_COLOR, tags="left")
    right_marker = canvas_range.create_rectangle(val_to_x(center_price + 2), 15,
                                                 val_to_x(center_price + 2) + marker_w, 35,
                                                 fill=ux.ACCENT_COLOR, tags="right")

    frame_range_info = ctk.CTkFrame(container)
    ux.style_frame(frame_range_info)
    add_row(frame_range_info)
    range_value = create_res(frame_range_info, "Диапазон:")
    coef_label_range = create_res(frame_range_info, "Коэффициент:")

    frame_range_bet = ctk.CTkFrame(container)
    ux.style_frame(frame_range_bet)
    add_row(frame_range_bet)
    entry_range = ctk.CTkEntry(frame_range_bet, width=120)
    ux.style_entry(entry_range)
    entry_range.pack(side="left")

    def update_range_coef():
        v1 = x_to_val(canvas_range.coords(left_marker)[0])
        v2 = x_to_val(canvas_range.coords(right_marker)[0])

        if v1 > v2:
            coef_label_range.configure(text="-")
            range_value.configure(text="—")
            return

        # Prevent probabilities from reaching 1 which would lead to
        # division by zero when calculating the coefficient
        if v1 >= center_price:
            v1 = center_price - 1
        if v2 <= center_price:
            v2 = center_price + 1

        p1 = get_prob(table, v1)
        p2 = get_prob(table, v2)

        if p1 is None or p2 is None:
            coef_label_range.configure(text="-")
            return

        prob_inside = (1 - p1) * (1 - p2)
        if prob_inside <= 0:
            coef_label_range.configure(text="-")
            range_value.configure(text=f"{v1}-{v2}")
            return

        coef = round(max(1, 95 / (prob_inside * 100)), 2)
        coef_label_range.configure(text=str(coef))
        range_value.configure(text=f"{v1}-{v2}")

    def move_marker(event):
        x = min(max(event.x, padding), width + padding - marker_w)
        tag = canvas_range.gettags("current")[0]
        center_x = val_to_x(center_price)

        if tag == "left":
            right_x = canvas_range.coords(right_marker)[0]
            max_left = min(right_x - marker_w, val_to_x(center_price - 1))

            if x > max_left:
                x = max_left

            canvas_range.coords(left_marker, x, 15, x + marker_w, 35)
        else:
            left_x = canvas_range.coords(left_marker)[0]
            min_right = max(left_x + marker_w, val_to_x(center_price + 1))

            if x < min_right:
                x = min_right

            canvas_range.coords(right_marker, x, 15, x + marker_w, 35)
        update_range_coef()

    canvas_range.tag_bind("left", "<B1-Motion>", move_marker)
    canvas_range.tag_bind("right", "<B1-Motion>", move_marker)
    update_range_coef()

    def place_range_bet():
        try:
            amt = float(entry_range.get().replace(',', '.'))
            v1 = x_to_val(canvas_range.coords(left_marker)[0])
            v2 = x_to_val(canvas_range.coords(right_marker)[0])
            process_express(table, v1, v2, amt)
            recalculate_all_probabilities(table, center_price)
            update_range_coef()
            if log_bet:
                try:
                    coef = float(coef_label_range.cget("text"))
                except ValueError:
                    coef = 0.0
                log_bet((v1, v2), amt, coef, "Выбор диапазона")
        except Exception:
            pass

    btn_range = ctk.CTkButton(frame_range_bet, text="Сделать ставку", command=place_range_bet)
    ux.style_button(btn_range)
    btn_range.pack(side="right", padx=5)

    # --- Price selection ---
    lbl_price = ctk.CTkLabel(container, text="Достижение цены")
    ux.style_label(lbl_price, 12)
    add_row(lbl_price)

    canvas_price = tk.Canvas(container, width=width + 2 * padding, height=60,
                             bg=ux.BG_COLOR, highlightthickness=0)
    add_row(canvas_price)
    draw_axis(canvas_price)

    marker = canvas_price.create_rectangle(val_to_x(center_price), 15,
                                           val_to_x(center_price) + marker_w, 35,
                                           fill=ux.ACCENT_COLOR, tags="marker")

    frame_price_info = ctk.CTkFrame(container)
    ux.style_frame(frame_price_info)
    add_row(frame_price_info)
    price_value = create_res(frame_price_info, "Цена:")
    coef_label_price = create_res(frame_price_info, "Коэффициент:")

    frame_price_bet = ctk.CTkFrame(container)
    ux.style_frame(frame_price_bet)
    add_row(frame_price_bet)
    entry_price = ctk.CTkEntry(frame_price_bet, width=120)
    ux.style_entry(entry_price)
    entry_price.pack(side="left")

    def update_price_coef():
        v = x_to_val(canvas_price.coords(marker)[0])
        p = get_prob(table, v)
        if p is None:
            coef_label_price.configure(text="-")
            price_value.configure(text="-")
            return
        coef = round(max(1, 95 / (p * 100)), 2)
        coef_label_price.configure(text=str(coef))
        price_value.configure(text=str(v))

    def move_price_marker(event):
        x = min(max(event.x, padding), width + padding - marker_w)
        canvas_price.coords(marker, x, 15, x + marker_w, 35)
        update_price_coef()

    canvas_price.tag_bind("marker", "<B1-Motion>", move_price_marker)
    update_price_coef()

    def place_price_bet():
        try:
            amt = float(entry_price.get().replace(',', '.'))
            v = x_to_val(canvas_price.coords(marker)[0])
            update_bet(table, v, amt, bet_type='да')
            recalculate_all_probabilities(table, center_price)
            update_price_coef()
            if log_bet:
                try:
                    coef = float(coef_label_price.cget("text"))
                except ValueError:
                    coef = 0.0
                log_bet((v, v), amt, coef, "Достижение цели")
        except Exception:
            pass

    btn_price = ctk.CTkButton(frame_price_bet, text="Сделать ставку", command=place_price_bet)
    ux.style_button(btn_price)
    btn_price.pack(side="right", padx=5)

    if root is not None:
        root.mainloop()
    else:
        return container

