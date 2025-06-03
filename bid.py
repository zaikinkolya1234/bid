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
    CENTER_PRICE = fetch_moex_last_price("SBER")
except Exception as e:
    print(f"Ошибка при получении цены: {e}")
    CENTER_PRICE = 110

PRICE_RANGE = range(CENTER_PRICE - 10, CENTER_PRICE + 11)

def probability(x: float) -> float:
    """Return base probability for the given price."""
    numerator = 100
    denominator = ((x - CENTER_PRICE) / 4) ** 4 + 1
    return numerator / denominator

def initialize_table():
    table = []
    for price in PRICE_RANGE:
        prob = round(probability(price), 4)
        table.append({
            'Цена': price,
            'Вероятность': prob,
            'Ставка_да': 0.0,
            'Ставка_нет': 0.0
        })
    return table

def recalculate_all_probabilities(table):
    for row in table:
        price = row['Цена']
        y1 = row['Ставка_да']
        y2 = row['Ставка_нет']
        P0 = probability(price)
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

def open_bid_window():
    """Open graphical interface for placing bets on price range or target."""
    table = initialize_table()

    ctk.set_appearance_mode("dark")
    root = ctk.CTk()
    root.title("Ставки")
    root.geometry("500x400")

    tabview = ctk.CTkTabview(root)
    tabview.pack(fill="both", expand=True, padx=10, pady=10)

    range_tab = tabview.add("Диапазон")
    price_tab = tabview.add("Достижение цены")

    min_val = PRICE_RANGE.start
    max_val = PRICE_RANGE.stop - 1
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

    # --- Range tab ---
    canvas_range = tk.Canvas(range_tab, width=width + 2 * padding, height=60, bg=ux.BG_COLOR, highlightthickness=0)
    canvas_range.pack(pady=5)
    draw_axis(canvas_range)

    left_marker = canvas_range.create_rectangle(val_to_x(CENTER_PRICE - 2), 15,
                                                val_to_x(CENTER_PRICE - 2) + marker_w, 35,
                                                fill=ux.ACCENT_COLOR, tags="left")
    right_marker = canvas_range.create_rectangle(val_to_x(CENTER_PRICE + 2), 15,
                                                 val_to_x(CENTER_PRICE + 2) + marker_w, 35,
                                                 fill=ux.ACCENT_COLOR, tags="right")

    range_value = ctk.CTkLabel(range_tab, text="—")
    ux.style_label(range_value)
    range_value.pack(pady=2)

    coef_label_range = ctk.CTkLabel(range_tab, text="-")
    ux.style_label(coef_label_range)
    coef_label_range.pack(pady=2)

    entry_range = ctk.CTkEntry(range_tab, width=100)
    ux.style_entry(entry_range)
    entry_range.pack(pady=5)

    def update_range_coef():
        v1 = x_to_val(canvas_range.coords(left_marker)[0])
        v2 = x_to_val(canvas_range.coords(right_marker)[0])
        if v1 > v2:
            coef_label_range.configure(text="-")
            range_value.configure(text="—")
            return
        p1 = get_prob(table, v1)
        p2 = get_prob(table, v2)
        if p1 is None or p2 is None:
            coef_label_range.configure(text="-")
            return
        prob_inside = (1 - p1) * (1 - p2)
        coef = round(max(1, 95 / (prob_inside * 100)), 2)
        coef_label_range.configure(text=str(coef))
        range_value.configure(text=f"{v1}-{v2}")

    def move_marker(event):
        x = min(max(event.x, padding), width + padding - marker_w)
        tag = canvas_range.gettags("current")[0]
        center_x = val_to_x(CENTER_PRICE)
        if tag == "left":
            right_x = canvas_range.coords(right_marker)[0]
            if x + marker_w > right_x:
                x = right_x - marker_w
            if x + marker_w > center_x:
                x = center_x - marker_w
            canvas_range.coords(left_marker, x, 15, x + marker_w, 35)
        else:
            left_x = canvas_range.coords(left_marker)[0]
            if x < left_x + marker_w:
                x = left_x + marker_w
            if x < center_x:
                x = center_x
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
            recalculate_all_probabilities(table)
            update_range_coef()
        except Exception:
            pass

    btn_range = ctk.CTkButton(range_tab, text="Сделать ставку", command=place_range_bet)
    ux.style_button(btn_range)
    btn_range.pack(pady=5)

    # --- Price tab ---
    canvas_price = tk.Canvas(price_tab, width=width + 2 * padding, height=60, bg=ux.BG_COLOR, highlightthickness=0)
    canvas_price.pack(pady=5)
    draw_axis(canvas_price)

    marker = canvas_price.create_rectangle(val_to_x(CENTER_PRICE), 15,
                                           val_to_x(CENTER_PRICE) + marker_w, 35,
                                           fill=ux.ACCENT_COLOR, tags="marker")

    price_value = ctk.CTkLabel(price_tab, text="-")
    ux.style_label(price_value)
    price_value.pack(pady=2)

    coef_label_price = ctk.CTkLabel(price_tab, text="-")
    ux.style_label(coef_label_price)
    coef_label_price.pack(pady=2)

    entry_price = ctk.CTkEntry(price_tab, width=100)
    ux.style_entry(entry_price)
    entry_price.pack(pady=5)

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
            recalculate_all_probabilities(table)
            update_price_coef()
        except Exception:
            pass

    btn_price = ctk.CTkButton(price_tab, text="Сделать ставку", command=place_price_bet)
    ux.style_button(btn_price)
    btn_price.pack(pady=5)

    root.mainloop()

def main():
    table = initialize_table()
    last_input = None

    while True:
        user_input = input("Введите цену или ставку (exit - выход): ").strip().lower()
        if user_input in ("exit", "выход"):
            break

        try:
            parts = list(map(float, user_input.split()))
            if len(parts) == 1 and parts[0] % 1000 == 0:
                if last_input:
                    if len(last_input) == 1:
                        update_bet(table, int(last_input[0]), parts[0], bet_type='да')
                    elif len(last_input) == 2:
                        process_express(table, int(last_input[0]), int(last_input[1]), parts[0])
                    else:
                        print("Ошибка: неверный контекст ставки.")
                    recalculate_all_probabilities(table)
                else:
                    print("Ошибка: ставка задана без цены.")
            elif len(parts) in (1, 2):
                last_input = parts
                if len(parts) == 1:
                    price = int(parts[0])
                    for row in table:
                        if row['Цена'] == price:
                            prob = row['Вероятность']
                            coef = round(max(1, 95 / prob), 2)
                            print(f"Цена {price} | Коэффициент: {coef}")
                            break
                else:
                    left, right = sorted((int(parts[0]), int(parts[1])))
                    if left >= CENTER_PRICE or right <= CENTER_PRICE:
                        print(f"Неправильный диапазон: левая граница должна быть < {CENTER_PRICE}, правая > {CENTER_PRICE}.")
                        continue
                    p1 = get_prob(table, left)
                    p2 = get_prob(table, right)
                    if p1 is None or p2 is None:
                        print("Ошибка: одна из цен вне диапазона.")
                        continue
                    prob_inside = (1 - p1) * (1 - p2)
                    coef = round(max(1, 95 / (prob_inside * 100)), 2)
                    print(f"Диапазон {left}–{right} | Коэффициент: {coef}")
            else:
                print("Ошибка: введите одно или два числа.")
        except ValueError as e:
            print(f"Ошибка ввода: {e}")

if __name__ == "__main__":
    open_bid_window()
