import random

def simulate_week_verbose(max_per_day=20):
    second_try = [0] * 10
    third_try = [0] * 10

    passed = 0
    total_new = 0

    for day in range(1, 7):
        places = max_per_day

        # 2-я попытка
        n2 = min(second_try[day], places)
        places -= n2

        passed2 = 0
        fail2 = 0
        for _ in range(n2):
            if random.random() < 0.25:
                passed += 1
                passed2 += 1
            else:
                fail2 += 1
                if day + 2 <= 6:
                    third_try[day + 2] += 1

        # 3-я попытка
        n3 = min(third_try[day], places)
        places -= n3

        passed3 = 0
        fail3 = 0
        for _ in range(n3):
            if random.random() < 0.10:
                passed += 1
                passed3 += 1
            else:
                fail3 += 1

        # Новые студенты
        n1 = places
        total_new += n1

        passed1 = 0
        fail1 = 0
        for _ in range(n1):
            if random.random() < 0.60:
                passed += 1
                passed1 += 1
            else:
                fail1 += 1
                if day + 2 <= 6:
                    second_try[day + 2] += 1

        print(f"День {day}:")
        print(f"  2-я попытка: {n2}, сдали: {passed2}, не сдали: {fail2}")
        print(f"  3-я попытка: {n3}, сдали: {passed3}, не сдали: {fail3}")
        print(f"  Новые студенты: {n1}, сдали: {passed1}, не сдали: {fail1}")
        print()

    print(f"Итого новых студентов: {total_new}")
    print(f"Итого успешно сдали: {passed}")


simulate_week_verbose()