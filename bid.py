import math
import requests

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
    main()
