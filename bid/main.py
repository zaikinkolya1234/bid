import customtkinter as ctk
ctk.deactivate_automatic_dpi_awareness()
import tkinter as tk
from tkinter import messagebox
import re
import pandas as pd
import datetime

from .data.moex import (
    fetch_moex_last_price,
    plot_price_chart,
)
from .logic.probability import (
    initialize_table,
    recalculate_all_probabilities,
    update_bet,
    get_prob,
    process_express,
    initialize_data,
    calculate_coefficient,
    apply_bet,
)
from .ui import styles as ux

try:
    DEFAULT_CENTER_PRICE = fetch_moex_last_price("SBER")
except Exception as e:
    print(f"Ошибка при получении цены: {e}")
    DEFAULT_CENTER_PRICE = 110


# --- market price ranges ----------------------------------------------------

try:
    sber_price = fetch_moex_last_price("SBER")
    gazp_price = fetch_moex_last_price("GAZP")
    CENTER1, MIN1, MAX1 = sber_price, sber_price - 10, sber_price + 10
    CENTER2, MIN2, MAX2 = gazp_price, gazp_price - 10, gazp_price + 10
except Exception as e:
    print(f"Ошибка при получении цен: {e}")
    CENTER1, MIN1, MAX1 = 270, 260, 280
    CENTER2, MIN2, MAX2 = 160, 150, 170

# --- global state -----------------------------------------------------------

current_type = None
history = []
embedded_bid_frame = None
embedded_bid_table_frame = None

df_type1 = initialize_data(CENTER1, MIN1, MAX1)
df_type2 = initialize_data(CENTER2, MIN2, MAX2)
price_table1 = initialize_table(CENTER1)
price_table2 = initialize_table(CENTER2)
last_range = [None, None]

def open_bid_window(parent=None, log_bet=None, center_price=None, table_parent=None, table=None):
    """Open graphical interface for placing bets on price range or target.

    If *parent* is provided, returns a frame with the interface embedded along
    with the table frame used for displaying data. Otherwise creates a
    standalone window and starts the mainloop.
    """
    if center_price is None:
        center_price = DEFAULT_CENTER_PRICE

    price_range = range(center_price - 10, center_price + 11)
    if table is None:
        table = initialize_table(center_price)

    format_amount = lambda a: '{:,.2f}'.format(a).replace(',', ' ').replace('.', ',')

    ctk.set_appearance_mode("dark")
    if parent is None:
        root = ctk.CTk()
        root.title("Ставки")
        root.geometry("500x500")
        container = root
    else:
        container = ctk.CTkFrame(parent, fg_color=ux.BG_COLOR)
        root = None

    if table_parent is None:
        table_parent = container

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

    def show_result_popup(amount, coef):
        win = tk.Toplevel(container)
        win.title("Результат ставки")
        win.geometry("300x200")
        win.configure(bg=ux.BG_COLOR)
        for txt, fnt, col, pady in [
            (f"Коэффициент: {coef:.2f}", (ux.FONT_FAMILY, 14), ux.TEXT_COLOR, 10),
            (f"Возможный выигрыш:\n{format_amount(amount * coef)}", (ux.FONT_FAMILY, 18, 'bold'), ux.ACCENT_COLOR, 10),
        ]:
            tk.Label(win, text=txt, font=fnt, fg=col, bg=ux.BG_COLOR, justify="center").pack(pady=pady)
        tk.Button(win, text="OK", command=win.destroy, font=(ux.FONT_FAMILY, 10), bg="#333", fg=ux.TEXT_COLOR, activebackground=ux.HOVER_COLOR).pack(pady=5)

    min_val = price_range.start
    max_val = price_range.stop - 1
    padding = 10
    width = 400
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
    lbl_range = ctk.CTkLabel(container, text="Выбор диапазона", anchor="center")
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
    entry_range = ctk.CTkEntry(frame_range_bet, width=100)
    ux.style_entry(entry_range)
    entry_range.configure(font=(ux.FONT_FAMILY, 12, "bold"))
    entry_range.pack(side="left", padx=5)
    entry_range.bind("<KeyRelease>", lambda e: format_entry(entry_range))

    def format_entry(entry):
        digits = re.sub(r"\D", "", entry.get())
        if digits:
            entry.delete(0, "end")
            entry.insert(0, f"{int(digits):,}".replace(",", "."))

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
            amt = float(entry_range.get().replace('.', '').replace(',', '.'))
            v1 = x_to_val(canvas_range.coords(left_marker)[0])
            v2 = x_to_val(canvas_range.coords(right_marker)[0])
            process_express(table, v1, v2, amt)
            recalculate_all_probabilities(table, center_price)
            update_range_coef()
            update_table()
            try:
                coef = float(coef_label_range.cget("text"))
            except ValueError:
                coef = 0.0
            if log_bet:
                log_bet((v1, v2), amt, coef, "Выбор диапазона")
            show_result_popup(amt, coef)
        except Exception:
            pass

    btn_range = ctk.CTkButton(frame_range_bet, text="Сделать ставку", command=place_range_bet)
    ux.style_button(btn_range)
    btn_range.pack(side="right", padx=5)

    # --- Price selection ---
    lbl_price = ctk.CTkLabel(container, text="Достижение цены", anchor="center")
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
    entry_price = ctk.CTkEntry(frame_price_bet, width=100)
    ux.style_entry(entry_price)
    entry_price.configure(font=(ux.FONT_FAMILY, 12, "bold"))
    entry_price.pack(side="left", padx=5)
    entry_price.bind("<KeyRelease>", lambda e: format_entry(entry_price))

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

    table_frame = ctk.CTkFrame(table_parent)
    ux.style_frame(table_frame)
    table_frame.pack(pady=10)
    mono = ctk.CTkFont(family="Courier New", size=12)
    table_textbox = ctk.CTkTextbox(table_frame, width=460, height=340)
    ux.style_textbox(table_textbox)
    table_textbox.configure(font=mono)
    table_textbox.pack()

    def update_table():
        lines = [f"{'Цена':>7}  {'Ставка_да':>10}  {'Ставка_нет':>10}  {'Вероятность':>12}"]
        for row in table:
            lines.append(f"{row['Цена']:>7}  {row['Ставка_да']:>10.2f}  {row['Ставка_нет']:>10.2f}  {row['Вероятность']:>11.2f}%")
        table_textbox.configure(state='normal')
        table_textbox.delete('1.0', 'end')
        table_textbox.insert('1.0', '\n'.join(lines))
        table_textbox.configure(state='disabled')
    update_table()

    def place_price_bet():
        try:
            amt = float(entry_price.get().replace('.', '').replace(',', '.'))
            v = x_to_val(canvas_price.coords(marker)[0])
            update_bet(table, v, amt, bet_type='да')
            recalculate_all_probabilities(table, center_price)
            update_price_coef()
            update_table()
            try:
                coef = float(coef_label_price.cget("text"))
            except ValueError:
                coef = 0.0
            if log_bet:
                log_bet((v, v), amt, coef, "Достижение цели")
            show_result_popup(amt, coef)
        except Exception:
            pass

    btn_price = ctk.CTkButton(frame_price_bet, text="Сделать ставку", command=place_price_bet)
    ux.style_button(btn_price)
    btn_price.pack(side="right", padx=5)

    if root is not None:
        root.mainloop()
    else:
        return container, table_frame, table

# --- higher-level UI -------------------------------------------------------

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


min_val, max_val, padding, pixel_range = MIN1, MAX1, 10, 400
canvas_width, marker_width = pixel_range + 2 * padding, 6
unit = pixel_range / (max_val - min_val)
val_to_x = lambda v: int((v - min_val) * unit) + padding
x_to_val = lambda x: int(round((x - padding) / unit + min_val))

format_amount = lambda a: "{:,.2f}".format(a).replace(",", " ").replace(".", ",")


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
        df = df_type1 if current_type == 1 else df_type2
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
    win.geometry("300x200")
    win.configure(bg="#1A1A1A")
    for txt, fnt, col, pady in [
        (f"Коэффициент: {coef:.2f}", (ux.FONT_FAMILY, 14), ux.TEXT_COLOR, 10),
        (f"Возможный выигрыш:\n{format_amount(amt * coef)}", (ux.FONT_FAMILY, 16, "bold"), ux.ACCENT_COLOR, 10),
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
    for i in range(min_val, max_val + 1, 2):
        x = val_to_x(i)
        canvas.create_line(x, 20, x, 30, fill=ux.TEXT_COLOR, tags="tick")
        canvas.create_text(x, 40, text=str(i), font=(ux.FONT_FAMILY, 8), fill=ux.TEXT_COLOR, tags="tick")


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
root = ctk.CTk()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root.geometry(f"{screen_width}x{screen_height}")
root.title("Ставки на закрытие акций")
root.configure(fg_color=ux.BG_COLOR)

main_container = ctk.CTkScrollableFrame(root, fg_color=ux.BG_COLOR)
main_container.pack(fill="both", expand=True)

menu = ctk.CTkFrame(main_container)
ux.style_frame(menu)
menu.pack(fill="x", pady=5)
for txt, cmd in [
    ("Ставки", lambda: switch_view("bet")),
    ("История", lambda: switch_view("history")),
    ("Информация", lambda: switch_view("info")),
]:
    b = ctk.CTkButton(menu, text=txt, command=cmd)
    ux.style_button(b)
    b.pack(side="left", padx=10)


def switch_view(view):
    global current_type, min_val, max_val, unit, embedded_bid_frame, embedded_bid_table_frame
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


type_select_frame = ctk.CTkFrame(main_container)
ux.style_frame(type_select_frame)
for txt, val in [("Сбербанк", "type1"), ("Газпром", "type2")]:
    b = ctk.CTkButton(type_select_frame, text=txt, command=lambda v=val: switch_view(v))
    ux.style_button(b)
    b.pack(pady=20)

bet_frame = ctk.CTkFrame(main_container)
ux.style_frame(bet_frame)

left_side = ctk.CTkFrame(bet_frame)
ux.style_frame(left_side)
left_side.pack(side="left", fill="both", expand=True)
right_side = ctk.CTkFrame(bet_frame)
ux.style_frame(right_side)
right_side.pack(side="right", fill="both", expand=True)

type_label = ctk.CTkLabel(left_side, text="", font=(ux.FONT_FAMILY, 16, "bold"), text_color=ux.ACCENT_COLOR)
type_label.pack(pady=5)
chart_frame = ctk.CTkFrame(left_side)
ux.style_frame(chart_frame)
chart_frame.pack(pady=5)

range_question_label = ctk.CTkLabel(left_side, text="", font=(ux.FONT_FAMILY, 12))
ux.style_label(range_question_label, 12)
range_question_label.pack(pady=5)

scale = ctk.CTkFrame(left_side)
ux.style_frame(scale)
scale.pack(pady=10)
canvas = tk.Canvas(scale, width=canvas_width, height=60, bg=ux.BG_COLOR, highlightthickness=0)
canvas.pack()
canvas.create_line(padding, 25, canvas_width - padding, 25, width=2, fill=ux.TEXT_COLOR)
draw_axis_labels()

x1, x2 = val_to_x(108), val_to_x(112)
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
    box = ctk.CTkFrame(frame)
    ux.style_box_frame(box)
    box.pack(side="left", padx=5)
    value = ctk.CTkLabel(box, text="—" if "Диапазон" in label_text else "-")
    ux.style_label(value, 12)
    value.pack(padx=6, pady=2)
    return value


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
entry_bet.configure(font=(ux.FONT_FAMILY, 12, "bold"))
entry_bet.pack(side="left", padx=5)
entry_bet.bind("<KeyRelease>", lambda e: format_bet_input())
ctk.CTkButton(
    frame_bet,
    text="Сделать ставку",
    command=on_bet_click,
    fg_color=ux.ACCENT_COLOR,
    hover_color=ux.HOVER_COLOR,
    text_color=ux.BG_COLOR,
).pack(side="left", padx=5)


mono = ctk.CTkFont(family="Courier New", size=12)
table_frame = ctk.CTkFrame(right_side)
ux.style_frame(table_frame)
table_frame.pack(pady=10)
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

