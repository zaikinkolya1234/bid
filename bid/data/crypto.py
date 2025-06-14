import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import FuncFormatter
from bid.ui import styles as ux

_session = requests.Session()
_retry = Retry(
    total=2,
    connect=2,
    read=2,
    backoff_factor=0.5,
    status_forcelist=[429, 500, 502, 503, 504],
)
_adapter = HTTPAdapter(max_retries=_retry)
_session.mount("https://", _adapter)
_session.mount("http://", _adapter)
_session.headers.update({"User-Agent": "Mozilla/5.0"})


def _get_json(url):
    """Retrieve JSON data from *url* with safe timeouts."""
    try:
        response = _session.get(url, timeout=(5, 5))
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        raise RuntimeError(f"HTTP request failed: {exc}") from exc

# Mapping of internal tickers to Coingecko IDs
CRYPTO_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "BNB": "binancecoin",
    "SOL": "solana",
    "USDC": "usd-coin",
    "XRP": "ripple",
    "TON": "the-open-network",
    "ADA": "cardano",
    "DOGE": "dogecoin",
}


def _prepare_frame(frame):
    """Remove previous chart widget from *frame* if present."""
    if hasattr(frame, "chart_canvas"):
        try:
            frame.chart_canvas.get_tk_widget().destroy()
        except Exception:
            pass
        delattr(frame, "chart_canvas")


def fetch_crypto_last_price(ticker: str) -> int:
    """Return the last known USD price for the given crypto ticker."""
    coin_id = CRYPTO_IDS.get(ticker.upper(), ticker.lower())
    url = (
        "https://api.coingecko.com/api/v3/simple/price"
        f"?ids={coin_id}&vs_currencies=usd"
    )
    try:
        data = _get_json(url)
        price = data.get(coin_id, {}).get("usd")
        if price is None:
            raise ValueError("price not found")
        return round(float(price))
    except Exception as e:
        print(f"Ошибка при получении цены {ticker}: {e}")
        return 0


def fetch_intraday_prices(ticker: str):
    """Return time and price arrays for the last day in USD from Coingecko."""
    coin_id = CRYPTO_IDS.get(ticker.upper(), ticker.lower())
    url = (
        f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        "?vs_currency=usd&days=1"
    )
    try:
        data = _get_json(url)
        prices = sorted(data.get("prices", []), key=lambda x: x[0])
        times = [datetime.datetime.fromtimestamp(p[0] / 1000).strftime("%H:%M") for p in prices]
        vals = [p[1] for p in prices]
        return times, vals
    except Exception as e:
        print(f"Ошибка при получении графика {ticker}: {e}")
        return [], []


def plot_crypto_price_chart(ticker: str, parent_frame):
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
    formatter = FuncFormatter(lambda y, _: f"{y:.0f} $")
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
