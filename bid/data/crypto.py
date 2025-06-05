import requests
import datetime
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from ..ui import styles as ux

CRYPTO_IDS = {
    "BTK": "bitcoin",
    "DKK": "dogecoin",
}


def fetch_crypto_last_price(ticker: str) -> int:
    coin_id = CRYPTO_IDS.get(ticker.upper(), ticker.lower())
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=rub"
    r = requests.get(url, timeout=10)
    data = r.json()
    price = data.get(coin_id, {}).get("rub")
    if price is None:
        raise ValueError(f"Price for {ticker} not found")
    return round(float(price))


def fetch_intraday_prices(ticker: str):
    coin_id = CRYPTO_IDS.get(ticker.upper(), ticker.lower())
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=rub&days=1"
    r = requests.get(url, timeout=10)
    data = r.json()
    prices = data.get("prices", [])
    times = [datetime.datetime.fromtimestamp(p[0] / 1000).strftime("%H:%M") for p in prices]
    vals = [p[1] for p in prices]
    return times, vals


def plot_crypto_price_chart(ticker: str, parent_frame):
    times, prices = fetch_intraday_prices(ticker)
    if not times or not prices:
        return
    fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
    fig.patch.set_facecolor(ux.BG_COLOR)
    ax.set_facecolor(ux.BG_COLOR)
    ax.plot(times, prices, linewidth=1.8, color=ux.ACCENT_COLOR)
    ax.set_ylim(min(prices), max(prices))
    ax.set_yticks(np.linspace(min(prices), max(prices), 5))
    ax.set_yticklabels([
        f"{y:.2f}" for y in np.linspace(min(prices), max(prices), 5)
    ], color=ux.TEXT_COLOR, fontsize=7)
    ax.set_title("График цены за день", fontsize=9, color=ux.TEXT_COLOR)
    ax.set_xticks([])
    ax.set_xlabel("время", fontsize=8, color=ux.TEXT_COLOR, labelpad=10)
    ax.tick_params(axis="y", labelsize=7, colors=ux.TEXT_COLOR)
    ax.spines["bottom"].set_color(ux.TEXT_COLOR)
    ax.spines["left"].set_color(ux.TEXT_COLOR)
    ax.spines["top"].set_color(ux.BG_COLOR)
    ax.spines["right"].set_color(ux.BG_COLOR)
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.3)
    fig.tight_layout()

    chart_canvas = FigureCanvasTkAgg(fig, master=parent_frame)
    if hasattr(plot_crypto_price_chart, "canvas_widget"):
        plot_crypto_price_chart.canvas_widget.get_tk_widget().destroy()
    plot_crypto_price_chart.canvas_widget = chart_canvas
    chart_canvas.draw()
    chart_canvas.get_tk_widget().pack()
