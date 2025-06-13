import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import re
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
    lkoh_price = fetch_moex_last_price("LKOH")
    rosn_price = fetch_moex_last_price("ROSN")
    gmkn_price = fetch_moex_last_price("GMKN")
    nvtk_price = fetch_moex_last_price("NVTK")
    plzl_price = fetch_moex_last_price("PLZL")
    sngs_price = fetch_moex_last_price("SNGS")
    mtss_price = fetch_moex_last_price("MTSS")
    chmf_price = fetch_moex_last_price("CHMF")
    btc_price = fetch_crypto_last_price("BTC")
    eth_price = fetch_crypto_last_price("ETH")
    bnb_price = fetch_crypto_last_price("BNB")
    sol_price = fetch_crypto_last_price("SOL")
    usdc_price = fetch_crypto_last_price("USDC")
    xrp_price = fetch_crypto_last_price("XRP")
    ton_price = fetch_crypto_last_price("TON")
    ada_price = fetch_crypto_last_price("ADA")
    doge_price = fetch_crypto_last_price("DOGE")
    if btc_price == 0 or eth_price == 0:
        raise ValueError("crypto price unavailable")
    CENTER1, MIN1, MAX1 = sber_price, sber_price - 10, sber_price + 10
    CENTER2, MIN2, MAX2 = gazp_price, gazp_price - 10, gazp_price + 10
    CENTER3, MIN3, MAX3 = btc_price, btc_price - 1000, btc_price + 1000
    CENTER4, MIN4, MAX4 = eth_price, eth_price - 1000, eth_price + 1000
    CENTER5, MIN5, MAX5 = lkoh_price, lkoh_price - 10, lkoh_price + 10
    CENTER6, MIN6, MAX6 = rosn_price, rosn_price - 10, rosn_price + 10
    CENTER7, MIN7, MAX7 = gmkn_price, gmkn_price - 10, gmkn_price + 10
    CENTER8, MIN8, MAX8 = nvtk_price, nvtk_price - 10, nvtk_price + 10
    CENTER9, MIN9, MAX9 = plzl_price, plzl_price - 10, plzl_price + 10
    CENTER10, MIN10, MAX10 = sngs_price, sngs_price - 10, sngs_price + 10
    CENTER11, MIN11, MAX11 = mtss_price, mtss_price - 10, mtss_price + 10
    CENTER12, MIN12, MAX12 = chmf_price, chmf_price - 10, chmf_price + 10
    delta_bnb = max(1, int(bnb_price * 0.02))
    delta_sol = max(1, int(sol_price * 0.02))
    delta_usdc = max(1, int(usdc_price * 0.02))
    delta_xrp = max(1, int(xrp_price * 0.02))
    delta_ton = max(1, int(ton_price * 0.02))
    delta_ada = max(1, int(ada_price * 0.02))
    delta_doge = max(1, int(doge_price * 0.02))
    CENTER14, MIN14, MAX14 = bnb_price, bnb_price - delta_bnb, bnb_price + delta_bnb
    CENTER15, MIN15, MAX15 = sol_price, sol_price - delta_sol, sol_price + delta_sol
    CENTER16, MIN16, MAX16 = usdc_price, usdc_price - delta_usdc, usdc_price + delta_usdc
    CENTER17, MIN17, MAX17 = xrp_price, xrp_price - delta_xrp, xrp_price + delta_xrp
    CENTER18, MIN18, MAX18 = ton_price, ton_price - delta_ton, ton_price + delta_ton
    CENTER19, MIN19, MAX19 = ada_price, ada_price - delta_ada, ada_price + delta_ada
    CENTER20, MIN20, MAX20 = doge_price, doge_price - delta_doge, doge_price + delta_doge
except Exception as e:
    print(f"Ошибка при получении цен: {e}")
    CENTER1, MIN1, MAX1 = 270, 260, 280
    CENTER2, MIN2, MAX2 = 160, 150, 170
    CENTER3, MIN3, MAX3 = 0, -1000, 1000
    CENTER4, MIN4, MAX4 = 0, -1000, 1000
    CENTER5, MIN5, MAX5 = 0, -10, 10
    CENTER6, MIN6, MAX6 = 0, -10, 10
    CENTER7, MIN7, MAX7 = 0, -10, 10
    CENTER8, MIN8, MAX8 = 0, -10, 10
    CENTER9, MIN9, MAX9 = 0, -10, 10
    CENTER10, MIN10, MAX10 = 0, -10, 10
    CENTER11, MIN11, MAX11 = 0, -10, 10
    CENTER12, MIN12, MAX12 = 0, -10, 10

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
df_type5 = initialize_data(CENTER5, MIN5, MAX5)
df_type6 = initialize_data(CENTER6, MIN6, MAX6)
df_type7 = initialize_data(CENTER7, MIN7, MAX7)
df_type8 = initialize_data(CENTER8, MIN8, MAX8)
df_type9 = initialize_data(CENTER9, MIN9, MAX9)
df_type10 = initialize_data(CENTER10, MIN10, MAX10)
df_type11 = initialize_data(CENTER11, MIN11, MAX11)
df_type12 = initialize_data(CENTER12, MIN12, MAX12)
df_type14 = initialize_data(CENTER14, MIN14, MAX14)
df_type15 = initialize_data(CENTER15, MIN15, MAX15)
df_type16 = initialize_data(CENTER16, MIN16, MAX16)
df_type17 = initialize_data(CENTER17, MIN17, MAX17)
df_type18 = initialize_data(CENTER18, MIN18, MAX18)
df_type19 = initialize_data(CENTER19, MIN19, MAX19)
df_type20 = initialize_data(CENTER20, MIN20, MAX20)
price_table1 = initialize_table(CENTER1)
price_table2 = initialize_table(CENTER2)
price_table3 = initialize_table(CENTER3)
price_table4 = initialize_table(CENTER4)
price_table5 = initialize_table(CENTER5)
price_table6 = initialize_table(CENTER6)
price_table7 = initialize_table(CENTER7)
price_table8 = initialize_table(CENTER8)
price_table9 = initialize_table(CENTER9)
price_table10 = initialize_table(CENTER10)
price_table11 = initialize_table(CENTER11)
price_table12 = initialize_table(CENTER12)
price_table14 = initialize_table(CENTER14)
price_table15 = initialize_table(CENTER15)
price_table16 = initialize_table(CENTER16)
price_table17 = initialize_table(CENTER17)
price_table18 = initialize_table(CENTER18)
price_table19 = initialize_table(CENTER19)
price_table20 = initialize_table(CENTER20)
last_range = [None, None]


# --- higher-level UI -------------------------------------------------------

def add_to_history(bet_range, amount, coefficient, bet_type: str):
    company_map = {
        1: "Сбербанк",
        2: "Газпром",
        3: "BTC",
        4: "ETH",
        5: "ЛУКОЙЛ",
        6: "Роснефть",
        7: "Норникель",
        8: "Новатэк",
        9: "Полюс",
        10: "Сургутнефтегаз",
        11: "МТС",
        12: "Северсталь",
        14: "Binance Coin",
        15: "Solana",
        16: "USD Coin",
        17: "XRP",
        18: "Toncoin",
        19: "Cardano",
        20: "Dogecoin",
    }
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


def _adjust_box_width(label: ctk.CTkLabel, extra: int = 12):
    """Resize the surrounding frame based on the label's required width."""
    label.update_idletasks()
    box = label.master
    box.configure(width=label.winfo_reqwidth() + extra)


def update_coef_label():
    x1, x2 = canvas.coords(marker_from)[0], canvas.coords(marker_to)[0]
    v1, v2 = x_to_val(x1), x_to_val(x2)
    if v1 > v2:
        coef_value.configure(text="-")
        range_value.configure(text="—")
        _adjust_box_width(coef_value)
        _adjust_box_width(range_value)
        return
    try:
        df_map = {
            1: df_type1,
            2: df_type2,
            3: df_type3,
            4: df_type4,
            5: df_type5,
            6: df_type6,
            7: df_type7,
            8: df_type8,
            9: df_type9,
            10: df_type10,
            11: df_type11,
            12: df_type12,
            14: df_type14,
            15: df_type15,
            16: df_type16,
            17: df_type17,
            18: df_type18,
            19: df_type19,
            20: df_type20,
        }
        df = df_map.get(current_type)
        coef = calculate_coefficient(df, v1, v2)
        coef_value.configure(text=f"{coef}")
        range_value.configure(text=f"{v1 - 0.51:.2f}–{v2 + 0.5:.2f}")
        _adjust_box_width(coef_value)
        _adjust_box_width(range_value)
        last_range[:] = v1, v2
    except Exception:
        coef_value.configure(text="Ошибка")
        range_value.configure(text="—")
        _adjust_box_width(coef_value)
        _adjust_box_width(range_value)


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
        global df_type5, df_type6, df_type7, df_type8
        global df_type9, df_type10, df_type11, df_type12
        global df_type14, df_type15, df_type16
        global df_type17, df_type18, df_type19, df_type20
        df_map = {
            1: df_type1,
            2: df_type2,
            3: df_type3,
            4: df_type4,
            5: df_type5,
            6: df_type6,
            7: df_type7,
            8: df_type8,
            9: df_type9,
            10: df_type10,
            11: df_type11,
            12: df_type12,
            14: df_type14,
            15: df_type15,
            16: df_type16,
            17: df_type17,
            18: df_type18,
            19: df_type19,
            20: df_type20,
        }
        center_map = {
            1: CENTER1,
            2: CENTER2,
            3: CENTER3,
            4: CENTER4,
            5: CENTER5,
            6: CENTER6,
            7: CENTER7,
            8: CENTER8,
            9: CENTER9,
            10: CENTER10,
            11: CENTER11,
            12: CENTER12,
            14: CENTER14,
            15: CENTER15,
            16: CENTER16,
            17: CENTER17,
            18: CENTER18,
            19: CENTER19,
            20: CENTER20,
        }
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
        elif current_type == 5:
            df_type5 = df_new
        elif current_type == 6:
            df_type6 = df_new
        elif current_type == 7:
            df_type7 = df_new
        elif current_type == 8:
            df_type8 = df_new
        elif current_type == 9:
            df_type9 = df_new
        elif current_type == 10:
            df_type10 = df_new
        elif current_type == 11:
            df_type11 = df_new
        elif current_type == 12:
            df_type12 = df_new
        elif current_type == 14:
            df_type14 = df_new
        elif current_type == 15:
            df_type15 = df_new
        elif current_type == 16:
            df_type16 = df_new
        elif current_type == 17:
            df_type17 = df_new
        elif current_type == 18:
            df_type18 = df_new
        elif current_type == 19:
            df_type19 = df_new
        elif current_type == 20:
            df_type20 = df_new
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
    """Display bet result inside the main application window."""
    overlay = ctk.CTkFrame(root)
    ux.style_frame(overlay)
    overlay.place(relx=0.5, rely=0.5, anchor="center")

    lbl_coef = ctk.CTkLabel(overlay, text=f"Коэффициент: {coef:.2f}")
    ux.style_label(lbl_coef, 12)
    lbl_coef.pack(padx=20, pady=10)

    lbl_win = ctk.CTkLabel(
        overlay,
        text=f"Возможный выигрыш:\n{format_amount(amt * coef)}",
        justify="center",
    )
    ux.style_title(lbl_win)
    lbl_win.pack(padx=20, pady=10)

    btn_ok = ctk.CTkButton(overlay, text="OK", command=overlay.destroy)
    ux.style_button(btn_ok)
    btn_ok.pack(pady=10)


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
    df_map = {
        1: df_type1,
        2: df_type2,
        3: df_type3,
        4: df_type4,
        5: df_type5,
        6: df_type6,
        7: df_type7,
        8: df_type8,
        9: df_type9,
        10: df_type10,
        11: df_type11,
        12: df_type12,
        14: df_type14,
        15: df_type15,
        16: df_type16,
        17: df_type17,
        18: df_type18,
        19: df_type19,
        20: df_type20,
    }
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
            font=ctk.CTkFont(family=ux.FONT_FAMILY, size=12),
            fill=color,
            tags="tick",
        )


def switch_view(view):
    global current_type, min_val, max_val, unit, embedded_bid_frame, embedded_bid_table_frame
    global currency_symbol, current_center
    for f in [type_select_frame, crypto_select_frame, bet_frame, history_frame, info_frame]:
        f.pack_forget()
    if view == "bet":
        type_select_frame.pack(fill="both", expand=True, pady=(15, 0))
    elif view == "crypto":
        crypto_select_frame.pack(fill="both", expand=True, pady=(15, 0))
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
    elif view == "type5":
        current_type = 5
        currency_symbol = "₽"
        current_center = CENTER5
        min_val, max_val = MIN5, MAX5
        unit = pixel_range / (max_val - min_val)
        type_label.configure(text="Выбран: ЛУКОЙЛ")
        range_question_label.configure(text="Закрытия акции ЛУКОЙЛ")
        plot_price_chart("LKOH", chart_frame)
        draw_axis_labels()
        x1, x2 = val_to_x(CENTER5 - 2), val_to_x(CENTER5 + 2)
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
            center_price=CENTER5,
            table=price_table5,
            axis_width=pixel_range,
        )
        embedded_bid_frame.pack(pady=10, fill="x")
        bet_frame.pack(fill="both", expand=True)
    elif view == "type6":
        current_type = 6
        currency_symbol = "₽"
        current_center = CENTER6
        min_val, max_val = MIN6, MAX6
        unit = pixel_range / (max_val - min_val)
        type_label.configure(text="Выбран: Роснефть")
        range_question_label.configure(text="Закрытия акции Роснефть")
        plot_price_chart("ROSN", chart_frame)
        draw_axis_labels()
        x1, x2 = val_to_x(CENTER6 - 2), val_to_x(CENTER6 + 2)
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
            center_price=CENTER6,
            table=price_table6,
            axis_width=pixel_range,
        )
        embedded_bid_frame.pack(pady=10, fill="x")
        bet_frame.pack(fill="both", expand=True)
    elif view == "type7":
        current_type = 7
        currency_symbol = "₽"
        current_center = CENTER7
        min_val, max_val = MIN7, MAX7
        unit = pixel_range / (max_val - min_val)
        type_label.configure(text="Выбран: Норникель")
        range_question_label.configure(text="Закрытия акции Норникель")
        plot_price_chart("GMKN", chart_frame)
        draw_axis_labels()
        x1, x2 = val_to_x(CENTER7 - 2), val_to_x(CENTER7 + 2)
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
            center_price=CENTER7,
            table=price_table7,
            axis_width=pixel_range,
        )
        embedded_bid_frame.pack(pady=10, fill="x")
        bet_frame.pack(fill="both", expand=True)
    elif view == "type8":
        current_type = 8
        currency_symbol = "₽"
        current_center = CENTER8
        min_val, max_val = MIN8, MAX8
        unit = pixel_range / (max_val - min_val)
        type_label.configure(text="Выбран: Новатэк")
        range_question_label.configure(text="Закрытия акции Новатэк")
        plot_price_chart("NVTK", chart_frame)
        draw_axis_labels()
        x1, x2 = val_to_x(CENTER8 - 2), val_to_x(CENTER8 + 2)
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
            center_price=CENTER8,
            table=price_table8,
            axis_width=pixel_range,
        )
        embedded_bid_frame.pack(pady=10, fill="x")
        bet_frame.pack(fill="both", expand=True)
    elif view == "type9":
        current_type = 9
        currency_symbol = "₽"
        current_center = CENTER9
        min_val, max_val = MIN9, MAX9
        unit = pixel_range / (max_val - min_val)
        type_label.configure(text="Выбран: Полюс")
        range_question_label.configure(text="Закрытия акции Полюс")
        plot_price_chart("PLZL", chart_frame)
        draw_axis_labels()
        x1, x2 = val_to_x(CENTER9 - 2), val_to_x(CENTER9 + 2)
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
            center_price=CENTER9,
            table=price_table9,
            axis_width=pixel_range,
        )
        embedded_bid_frame.pack(pady=10, fill="x")
        bet_frame.pack(fill="both", expand=True)
    elif view == "type10":
        current_type = 10
        currency_symbol = "₽"
        current_center = CENTER10
        min_val, max_val = MIN10, MAX10
        unit = pixel_range / (max_val - min_val)
        type_label.configure(text="Выбран: Сургутнефтегаз")
        range_question_label.configure(text="Закрытия акции Сургутнефтегаз")
        plot_price_chart("SNGS", chart_frame)
        draw_axis_labels()
        x1, x2 = val_to_x(CENTER10 - 2), val_to_x(CENTER10 + 2)
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
            center_price=CENTER10,
            table=price_table10,
            axis_width=pixel_range,
        )
        embedded_bid_frame.pack(pady=10, fill="x")
        bet_frame.pack(fill="both", expand=True)
    elif view == "type11":
        current_type = 11
        currency_symbol = "₽"
        current_center = CENTER11
        min_val, max_val = MIN11, MAX11
        unit = pixel_range / (max_val - min_val)
        type_label.configure(text="Выбран: МТС")
        range_question_label.configure(text="Закрытия акции МТС")
        plot_price_chart("MTSS", chart_frame)
        draw_axis_labels()
        x1, x2 = val_to_x(CENTER11 - 2), val_to_x(CENTER11 + 2)
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
            center_price=CENTER11,
            table=price_table11,
            axis_width=pixel_range,
        )
        embedded_bid_frame.pack(pady=10, fill="x")
        bet_frame.pack(fill="both", expand=True)
    elif view == "type12":
        current_type = 12
        currency_symbol = "₽"
        current_center = CENTER12
        min_val, max_val = MIN12, MAX12
        unit = pixel_range / (max_val - min_val)
        type_label.configure(text="Выбран: Северсталь")
        range_question_label.configure(text="Закрытия акции Северсталь")
        plot_price_chart("CHMF", chart_frame)
        draw_axis_labels()
        x1, x2 = val_to_x(CENTER12 - 2), val_to_x(CENTER12 + 2)
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
            center_price=CENTER12,
            table=price_table12,
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
    elif view == "bnb":
        current_type = 14
        currency_symbol = "$"
        current_center = CENTER14
        min_val, max_val = MIN14, MAX14
        unit = pixel_range / (max_val - min_val)
        type_label.configure(text="Выбран: BNB")
        range_question_label.configure(text="Курс BNB")
        plot_crypto_price_chart("BNB", chart_frame)
        draw_axis_labels()
        x1, x2 = val_to_x(CENTER14 - 2), val_to_x(CENTER14 + 2)
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
            center_price=CENTER14,
            table=price_table14,
            axis_width=pixel_range,
        )
        embedded_bid_frame.pack(pady=10, fill="x")
        bet_frame.pack(fill="both", expand=True)
    elif view == "sol":
        current_type = 15
        currency_symbol = "$"
        current_center = CENTER15
        min_val, max_val = MIN15, MAX15
        unit = pixel_range / (max_val - min_val)
        type_label.configure(text="Выбран: SOL")
        range_question_label.configure(text="Курс SOL")
        plot_crypto_price_chart("SOL", chart_frame)
        draw_axis_labels()
        x1, x2 = val_to_x(CENTER15 - 2), val_to_x(CENTER15 + 2)
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
            center_price=CENTER15,
            table=price_table15,
            axis_width=pixel_range,
        )
        embedded_bid_frame.pack(pady=10, fill="x")
        bet_frame.pack(fill="both", expand=True)
    elif view == "usdc":
        current_type = 16
        currency_symbol = "$"
        current_center = CENTER16
        min_val, max_val = MIN16, MAX16
        unit = pixel_range / (max_val - min_val)
        type_label.configure(text="Выбран: USDC")
        range_question_label.configure(text="Курс USDC")
        plot_crypto_price_chart("USDC", chart_frame)
        draw_axis_labels()
        x1, x2 = val_to_x(CENTER16 - 2), val_to_x(CENTER16 + 2)
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
            center_price=CENTER16,
            table=price_table16,
            axis_width=pixel_range,
        )
        embedded_bid_frame.pack(pady=10, fill="x")
        bet_frame.pack(fill="both", expand=True)
    elif view == "xrp":
        current_type = 17
        currency_symbol = "$"
        current_center = CENTER17
        min_val, max_val = MIN17, MAX17
        unit = pixel_range / (max_val - min_val)
        type_label.configure(text="Выбран: XRP")
        range_question_label.configure(text="Курс XRP")
        plot_crypto_price_chart("XRP", chart_frame)
        draw_axis_labels()
        x1, x2 = val_to_x(CENTER17 - 2), val_to_x(CENTER17 + 2)
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
            center_price=CENTER17,
            table=price_table17,
            axis_width=pixel_range,
        )
        embedded_bid_frame.pack(pady=10, fill="x")
        bet_frame.pack(fill="both", expand=True)
    elif view == "ton":
        current_type = 18
        currency_symbol = "$"
        current_center = CENTER18
        min_val, max_val = MIN18, MAX18
        unit = pixel_range / (max_val - min_val)
        type_label.configure(text="Выбран: TON")
        range_question_label.configure(text="Курс TON")
        plot_crypto_price_chart("TON", chart_frame)
        draw_axis_labels()
        x1, x2 = val_to_x(CENTER18 - 2), val_to_x(CENTER18 + 2)
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
            center_price=CENTER18,
            table=price_table18,
            axis_width=pixel_range,
        )
        embedded_bid_frame.pack(pady=10, fill="x")
        bet_frame.pack(fill="both", expand=True)
    elif view == "ada":
        current_type = 19
        currency_symbol = "$"
        current_center = CENTER19
        min_val, max_val = MIN19, MAX19
        unit = pixel_range / (max_val - min_val)
        type_label.configure(text="Выбран: ADA")
        range_question_label.configure(text="Курс ADA")
        plot_crypto_price_chart("ADA", chart_frame)
        draw_axis_labels()
        x1, x2 = val_to_x(CENTER19 - 2), val_to_x(CENTER19 + 2)
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
            center_price=CENTER19,
            table=price_table19,
            axis_width=pixel_range,
        )
        embedded_bid_frame.pack(pady=10, fill="x")
        bet_frame.pack(fill="both", expand=True)
    elif view == "doge":
        current_type = 20
        currency_symbol = "$"
        current_center = CENTER20
        min_val, max_val = MIN20, MAX20
        unit = pixel_range / (max_val - min_val)
        type_label.configure(text="Выбран: DOGE")
        range_question_label.configure(text="Курс DOGE")
        plot_crypto_price_chart("DOGE", chart_frame)
        draw_axis_labels()
        x1, x2 = val_to_x(CENTER20 - 2), val_to_x(CENTER20 + 2)
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
            center_price=CENTER20,
            table=price_table20,
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
    for txt, val in [
        ("Сбербанк", "type1"),
        ("Газпром", "type2"),
        ("ЛУКОЙЛ", "type5"),
        ("Роснефть", "type6"),
        ("Норникель", "type7"),
        ("Новатэк", "type8"),
        ("Полюс", "type9"),
        ("Сургутнефтегаз", "type10"),
        ("МТС", "type11"),
        ("Северсталь", "type12"),
    ]:
        b = ctk.CTkButton(type_select_frame, text=txt, command=lambda v=val: switch_view(v))
        ux.style_button(b)
        b.pack(pady=5, padx=20, anchor="w")

    crypto_select_frame = ctk.CTkFrame(main_container)
    ux.style_frame(crypto_select_frame)
    for txt, val in [
        ("BTC", "btc"),
        ("ETH", "eth"),
        ("BNB", "bnb"),
        ("SOL", "sol"),
        ("USDC", "usdc"),
        ("XRP", "xrp"),
        ("TON", "ton"),
        ("ADA", "ada"),
        ("DOGE", "doge"),
    ]:
        cb = ctk.CTkButton(crypto_select_frame, text=txt, command=lambda v=val: switch_view(v))
        ux.style_button(cb)
        cb.pack(pady=5, padx=20, anchor="w")

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
        box = ctk.CTkFrame(frame, width=ux.INFO_BOX_WIDTH, height=ux.INFO_BOX_HEIGHT)
        ux.style_box_frame(box)
        box.pack(side="left", padx=5)
        box.pack_propagate(False)
        value = ctk.CTkLabel(box, text="—" if "Диапазон" in label_text else "-")
        ux.style_label(value, 12)
        value.configure(bg_color="transparent")
        value.pack(padx=6, pady=2, fill="both", expand=True)
        box.lift()
        _adjust_box_width(value)
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

    mono = ctk.CTkFont(family=ux.FONT_FAMILY, size=12)
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
