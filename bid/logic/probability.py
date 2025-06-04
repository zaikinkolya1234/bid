import math
import numpy as np
import pandas as pd


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
            "Цена": price,
            "Вероятность": prob,
            "Ставка_да": 0.0,
            "Ставка_нет": 0.0,
        })
    return table


def recalculate_all_probabilities(table, center_price: float):
    for row in table:
        price = row["Цена"]
        y1 = row["Ставка_да"]
        y2 = row["Ставка_нет"]
        P0 = probability(price, center_price)
        h1 = P0 * 100_000
        h2 = (100 - P0) * 100_000
        denominator = y1 + y2 + h1 + h2
        new_prob = round(0.5 * P0 + 0.5 * ((y1 + h1) / denominator * 100), 4)
        row["Вероятность"] = new_prob


def update_bet(table, price, amount, bet_type):
    for row in table:
        if row["Цена"] == price:
            if bet_type == "да":
                row["Ставка_да"] = round(row["Ставка_да"] + amount, 2)
            else:
                row["Ставка_нет"] = round(row["Ставка_нет"] + amount, 2)
            break


def get_prob(table, price):
    for row in table:
        if row["Цена"] == price:
            return row["Вероятность"] / 100
    return None


def process_express(table, price1, price2, amount):
    p1 = get_prob(table, price1)
    p2 = get_prob(table, price2)
    if not p1 or not p2:
        print("Ошибка: цены вне диапазона.")
        return

    w1 = math.log(1 / p1) / (math.log(1 / p1) + math.log(1 / p2))
    w2 = 1 - w1

    update_bet(table, price1, amount * w1, bet_type="нет")
    update_bet(table, price2, amount * w2, bet_type="нет")


INITIAL_BANK = 10_000_000


def initialize_data(center, min_val, max_val):
    prices = np.arange(min_val, max_val + 1)
    weights = 1 / (((prices - center) / 4) ** 4 + 1) * 100
    base_probs = weights / weights.sum()
    return pd.DataFrame({
        "Цена": prices,
        "Ставки_доп": np.zeros_like(prices, dtype=int),
        "Вероятность": base_probs,
    })


def calculate_coefficient(df, start, end):
    sub = df[(df["Цена"] >= start) & (df["Цена"] <= end)]
    p = sub["Вероятность"].sum()
    if p == 0:
        return 1.00
    coef = round(0.95 / p, 3)
    return max(coef, 1.00)


def apply_bet(df, center, min_val, max_val, last_range, amount):
    start, end = last_range
    count = end - start + 1
    add = amount / count
    df["Ставки_доп"] = df["Ставки_доп"].astype(float)
    mask = (df["Цена"] >= start) & (df["Цена"] <= end)
    df.loc[mask, "Ставки_доп"] += float(add)
    prices = df["Цена"].values
    base_weights = 1 / (((prices - center) / 4) ** 4 + 1) * 100
    base_probs = base_weights / base_weights.sum()
    base_stakes = base_probs * INITIAL_BANK
    total_stakes = base_stakes + df["Ставки_доп"]
    stake_probs = total_stakes / total_stakes.sum()
    df["Вероятность"] = 0.4 * base_probs + 0.6 * stake_probs
    return df
