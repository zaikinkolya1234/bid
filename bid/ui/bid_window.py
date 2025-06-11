import customtkinter as ctk
import tkinter as tk
import re

from bid.data.moex import fetch_moex_last_price
from bid.logic.probability import (
    initialize_table,
    recalculate_all_probabilities,
    update_bet,
    get_prob,
    process_express,
)
from bid.ui import styles as ux

try:
    DEFAULT_CENTER_PRICE = fetch_moex_last_price("SBER")
except Exception as e:
    print(f"Ошибка при получении цены: {e}")
    DEFAULT_CENTER_PRICE = 110


def open_bid_window(parent=None, log_bet=None, center_price=None, table_parent=None, table=None, axis_width=None):
    """Open graphical interface for placing bets on price range or target."""

    if center_price is None:
        center_price = DEFAULT_CENTER_PRICE

    price_range = range(center_price - 10, center_price + 11)
    if table is None:
        table = initialize_table(center_price)

    format_amount = lambda a: '{:,.2f}'.format(a).replace(',', ' ').replace('.', ',')

    ctk.set_appearance_mode("dark")
    if parent is None:
        root = ctk.CTk()
        scaling = root.winfo_fpixels("1i") / 96
        ctk.set_widget_scaling(scaling)
        ctk.set_window_scaling(scaling)
        root.tk.call("tk", "scaling", scaling)
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        width = int(sw * 0.5)
        height = int(sh * 0.5)
        root.geometry(f"{width}x{height}+{(sw - width)//2}+{(sh - height)//2}")
        root.title("Ставки")
        container = root
    else:
        container = ctk.CTkFrame(parent, fg_color=ux.BG_COLOR)
        root = None

    if table_parent is None:
        table_parent = container

    # --- layout helpers ---
    def add_row(widget, center=False, **pack_opts):
        if center:
            widget.pack(pady=5, padx=10)
        else:
            widget.pack(pady=5, padx=10, fill="both", expand=True, **pack_opts)

    def create_res(parent, label_text):
        frame = ctk.CTkFrame(parent)
        ux.style_frame(frame)
        frame.pack(side="left", padx=10)
        lbl = ctk.CTkLabel(frame, text=label_text)
        ux.style_label(lbl, 12)
        lbl.pack(side="left")
        box = ctk.CTkFrame(frame, width=80)
        ux.style_box_frame(box)
        box.pack(side="left", padx=5)
        val = ctk.CTkLabel(box, text="—" if "Диапазон" in label_text else "-")
        ux.style_label(val, 12)
        val.pack(padx=6, pady=2)
        return val

    def show_result_popup(amount, coef):
        win = ctk.CTkToplevel(container)
        win.title("Результат ставки")
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        w = int(sw * 0.3)
        h = int(sh * 0.3)
        win.geometry(f"{w}x{h}+{(sw - w)//2}+{(sh - h)//2}")

        frame = ctk.CTkFrame(win)
        ux.style_frame(frame)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        lbl_coef = ctk.CTkLabel(frame, text=f"Коэффициент: {coef:.2f}")
        ux.style_label(lbl_coef)
        lbl_coef.pack(pady=10)

        lbl_win = ctk.CTkLabel(
            frame,
            text=f"Возможный выигрыш:\n{format_amount(amount * coef)}",
            justify="center",
        )
        ux.style_title(lbl_win)
        lbl_win.pack(pady=10)

        btn_ok = ctk.CTkButton(frame, text="OK", command=win.destroy)
        ux.style_button(btn_ok)
        btn_ok.pack(pady=10)

    min_val = price_range.start
    max_val = price_range.stop - 1
    padding = 10
    screen_w = (root.winfo_screenwidth() if root is not None else parent.winfo_screenwidth())
    if axis_width is not None:
        width = int(axis_width)
    else:
        width = int(screen_w * 0.4)
    marker_w = 6
    unit = width / (max_val - min_val)
    val_to_x = lambda v: int((v - min_val) * unit) + padding
    x_to_val = lambda x: int(round((x - padding) / unit + min_val))

    def draw_axis(canv):
        canv.create_line(padding, 25, width + padding, 25, width=2, fill=ux.TEXT_COLOR)
        for i in range(min_val, max_val + 1, 2):
            x = val_to_x(i)
            canv.create_line(x, 20, x, 30, fill=ux.TEXT_COLOR)
            canv.create_text(
                x,
                40,
                text=str(i),
                fill=ux.TEXT_COLOR,
                font=ctk.CTkFont(family=ux.FONT_FAMILY, size=8),
            )

    # --- Range selection ---
    lbl_range = ctk.CTkLabel(container, text="Выбор диапазона", anchor="center")
    ux.style_title(lbl_range)
    add_row(lbl_range)

    canvas_range = tk.Canvas(
        container,
        width=width + 2 * padding,
        height=60,
        bg=ux.BG_COLOR,
        highlightthickness=0,
    )
    add_row(canvas_range, center=True)
    draw_axis(canvas_range)

    left_marker = canvas_range.create_rectangle(val_to_x(center_price - 2), 15,
                                                val_to_x(center_price - 2) + marker_w, 35,
                                                fill=ux.ACCENT_COLOR, tags="left")
    right_marker = canvas_range.create_rectangle(val_to_x(center_price + 2), 15,
                                                 val_to_x(center_price + 2) + marker_w, 35,
                                                 fill=ux.ACCENT_COLOR, tags="right")

    frame_range_info = ctk.CTkFrame(container)
    ux.style_frame(frame_range_info)
    add_row(frame_range_info, center=True)
    range_value = create_res(frame_range_info, "Диапазон:")
    coef_label_range = create_res(frame_range_info, "Коэффициент:")

    frame_range_bet = ctk.CTkFrame(container)
    ux.style_frame(frame_range_bet)
    add_row(frame_range_bet, center=True)
    lbl_range_bet = ctk.CTkLabel(frame_range_bet, text="Ставка:")
    ux.style_label(lbl_range_bet)
    lbl_range_bet.pack(side="left")
    entry_range = ctk.CTkEntry(frame_range_bet, width=100)
    ux.style_entry(entry_range)
    entry_range.configure(font=ctk.CTkFont(family=ux.FONT_FAMILY, size=12, weight="bold"))
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
    btn_range.pack(side="left", padx=5)

    # --- Price selection ---
    lbl_price = ctk.CTkLabel(container, text="Достижение цены", anchor="center")
    ux.style_title(lbl_price)
    add_row(lbl_price)

    canvas_price = tk.Canvas(
        container,
        width=width + 2 * padding,
        height=60,
        bg=ux.BG_COLOR,
        highlightthickness=0,
    )
    add_row(canvas_price, center=True)
    draw_axis(canvas_price)

    marker = canvas_price.create_rectangle(val_to_x(center_price), 15,
                                           val_to_x(center_price) + marker_w, 35,
                                           fill=ux.ACCENT_COLOR, tags="marker")

    frame_price_info = ctk.CTkFrame(container)
    ux.style_frame(frame_price_info)
    add_row(frame_price_info, center=True)
    price_value = create_res(frame_price_info, "Цена:")
    coef_label_price = create_res(frame_price_info, "Коэффициент:")

    frame_price_bet = ctk.CTkFrame(container)
    ux.style_frame(frame_price_bet)
    add_row(frame_price_bet, center=True)
    lbl_price_bet = ctk.CTkLabel(frame_price_bet, text="Ставка:")
    ux.style_label(lbl_price_bet)
    lbl_price_bet.pack(side="left")
    entry_price = ctk.CTkEntry(frame_price_bet, width=100)
    ux.style_entry(entry_price)
    entry_price.configure(font=ctk.CTkFont(family=ux.FONT_FAMILY, size=12, weight="bold"))
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
    table_frame.pack(pady=10, fill="both", expand=True)
    mono = ctk.CTkFont(family=ux.FONT_FAMILY, size=12)
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
    btn_price.pack(side="left", padx=5)

    if root is not None:
        root.mainloop()
    else:
        return container, table_frame, table
