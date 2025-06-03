def main() -> None:
    """Calculate and print the coefficient after greeting."""
    print("привет мир")
    print("привет земля")

    try:
        number = float(input("Введите число: "))
        result = 100 / number
    except ZeroDivisionError:
        print("На ноль делить нельзя.")
        return
    except ValueError:
        print("Нужно ввести число.")
        return

    print("коэффициент:", result)


if __name__ == "__main__":
    main()
