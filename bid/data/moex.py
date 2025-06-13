import datetime
import requests
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import FuncFormatter
from bid.ui import styles as ux


def _prepare_frame(frame):
    """Remove previous chart widget from *frame* if present."""
    if hasattr(frame, "chart_canvas"):
        try:
            frame.chart_canvas.get_tk_widget().destroy()
        except Exception:
            pass
        delattr(frame, "chart_canvas")





def fetch_moex_last_price(ticker: str) -> int:
    """Return last traded price for the given ticker using the MOEX ISS API."""
    symbol = ticker.upper()
    url = (
        "https://iss.moex.com/iss/engines/stock/markets/shares/"
        f"securities/{symbol}.json"
    )
    try:
        data = requests.get(url, timeout=10).json()
        columns = data["marketdata"]["columns"]
        board_idx = columns.index("BOARDID")
        last_idx = columns.index("LAST")
        for row in data["marketdata"]["data"]:
            if row[board_idx] == "TQBR" and row[last_idx] is not None:
                return round(float(row[last_idx]))
        for row in data["marketdata"]["data"]:
            if row[last_idx] is not None:
                return round(float(row[last_idx]))
    except Exception as e:
        print(f"Ошибка при получении цены {ticker}: {e}")
        return 0


def fetch_intraday_prices(ticker: str):
    """Return time and price arrays for the most recent trading day."""
    symbol = ticker.upper()

    # Determine the last available trading date
    try:
        date_url = (
            "https://iss.moex.com/iss/history/engines/stock/markets/shares/"
            f"securities/{symbol}.json?iss.meta=off&history.columns=TRADEDATE&sort_order=desc&limit=1"
        )
        resp = requests.get(date_url, timeout=10).json()
        last_date = resp.get("history", {}).get("data", [[None]])[0][0]
        if last_date is None:
            raise ValueError("no trade date")
    except Exception as e:
        print(f"Ошибка при получении даты {ticker}: {e}")
        return [], []

    url = (
        "https://iss.moex.com/iss/engines/stock/markets/shares/"
        f"securities/{symbol}/candles.json?interval=10&from={last_date}&till={last_date}&boardid=TQBR"
    )
    try:
        data = requests.get(url, timeout=10).json()
        candles = data.get("candles", {}).get("data", [])
        if not candles:
            raise ValueError("no candle data")
        cols = data["candles"]["columns"]
        idx_t = cols.index("begin")
        idx_c = cols.index("close")
        candles.sort(key=lambda x: x[idx_t])
        times = [c[idx_t][11:16] for c in candles]
        prices = [c[idx_c] for c in candles]
        return times, prices
    except Exception as e:
        print(f"Ошибка при получении графика {ticker}: {e}")
        return [], []


def plot_price_chart(ticker: str, parent_frame):
    """Draw intraday price chart for *ticker* inside *parent_frame*."""
    times, prices = fetch_intraday_prices(ticker)
    if not times or not prices:
        return
    _prepare_frame(parent_frame)

    parent_frame.update_idletasks()
    width_px = max(parent_frame.winfo_width(), 600)
    fig_width = width_px / 100
    fig, ax = plt.subplots(figsize=(fig_width, 5), dpi=100)
    fig.patch.set_facecolor(ux.BG_COLOR)
    ax.set_facecolor(ux.BG_COLOR)
    ax.plot(range(len(times)), prices, linewidth=1.8, color=ux.ACCENT_COLOR)
    ax.set_xlim(0, len(times) - 1)
    ax.set_ylim(min(prices), max(prices))
    ax.set_yticks(np.linspace(min(prices), max(prices), 5))
    formatter = FuncFormatter(lambda y, _: f"{y:.0f} ₽")
    ax.yaxis.set_major_formatter(formatter)
    ax.set_title("График цены за день", fontsize=11, color=ux.TEXT_COLOR)
    num_ticks = 6
    idx = np.linspace(0, len(times) - 1, num_ticks, dtype=int)
    ax.set_xticks(idx)
    ax.set_xticklabels([times[i] for i in idx], color=ux.TEXT_COLOR, fontsize=10, rotation=45, ha="right")
    ax.set_xlabel("время", fontsize=10, color=ux.TEXT_COLOR, labelpad=10)
    ax.tick_params(axis="y", labelsize=9, colors=ux.TEXT_COLOR)
    ax.spines["bottom"].set_color(ux.TEXT_COLOR)
    ax.spines["left"].set_color(ux.TEXT_COLOR)
    ax.spines["top"].set_color(ux.BG_COLOR)
    ax.spines["right"].set_color(ux.BG_COLOR)
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.3)
    fig.tight_layout()

    chart_canvas = FigureCanvasTkAgg(fig, master=parent_frame)
    parent_frame.chart_canvas = chart_canvas
    chart_canvas.draw()
    chart_canvas.get_tk_widget().pack(fill="both", expand=True)
