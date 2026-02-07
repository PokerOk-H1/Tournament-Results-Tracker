#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
tournament.py — анализатор турнирных результатов

Функции:
- summary  — сводный отчёт (ROI, профит, ITM и т.д.)
- add      — добавление одной записи турнира в CSV
- graph    — график профита/банкролла
- details  — подробный список турниров с фильтрами
"""

import argparse
import csv
import os
from dataclasses import dataclass
from datetime import datetime, date
from typing import List, Optional, Dict, Any, Iterable, Tuple
from collections import defaultdict

# ==========================
# Модель данных
# ==========================

CSV_HEADERS = [
    "date",
    "room",
    "name",
    "buy_in",
    "rake",
    "currency",
    "result",
    "place",
    "players",
    "format",
    "notes",
]


def parse_date(date_str: str) -> date:
    """Парсинг даты формата YYYY-MM-DD."""
    return datetime.strptime(date_str, "%Y-%m-%d").date()


@dataclass
class Tournament:
    date: date
    room: str
    name: str
    buy_in: float
    rake: float
    currency: str
    result: float
    place: int
    players: int
    format: str
    notes: str

    @property
    def total_cost(self) -> float:
        """Общая стоимость участия (бай-ин + рейк)."""
        return self.buy_in + self.rake

    @property
    def profit(self) -> float:
        """Профит турнира."""
        return self.result - self.total_cost

    @property
    def is_itm(self) -> bool:
        """ITM — есть ли приз."""
        return self.result > 0

    @classmethod
    def from_csv_row(cls, row: Dict[str, str]) -> Optional["Tournament"]:
        """Создать Tournament из строки CSV. При ошибке — вернуть None."""
        try:
            d = parse_date(row["date"])
        except Exception:
            print(f"Предупреждение: не удалось распарсить дату: {row.get('date')!r}")
            return None

        def to_float(value: str) -> float:
            value = value.strip()
            if not value:
                return 0.0
            try:
                return float(value)
            except ValueError:
                return 0.0

        def to_int(value: str) -> int:
            value = value.strip()
            if not value:
                return 0
            try:
                return int(value)
            except ValueError:
                return 0

        try:
            return cls(
                date=d,
                room=row.get("room", "").strip(),
                name=row.get("name", "").strip(),
                buy_in=to_float(row.get("buy_in", "0")),
                rake=to_float(row.get("rake", "0")),
                currency=row.get("currency", "").strip() or "USD",
                result=to_float(row.get("result", "0")),
                place=to_int(row.get("place", "0")),
                players=to_int(row.get("players", "0")),
                format=row.get("format", "").strip(),
                notes=row.get("notes", "").strip(),
            )
        except Exception as e:
            print(f"Предупреждение: не удалось распарсить строку: {e}")
            return None


# ==========================
# Работа с CSV
# ==========================

def load_tournaments(file_path: str) -> List[Tournament]:
    """Загрузить турниры из CSV-файла."""
    tournaments: List[Tournament] = []

    if not os.path.isfile(file_path):
        raise FileNotFoundError(
            f"Файл {file_path} не найден. Укажите путь через --file или создайте CSV."
        )

    with open(file_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        missing = [h for h in CSV_HEADERS if h not in reader.fieldnames]
        if missing:
            print(
                "Предупреждение: в файле не хватает колонок: "
                + ", ".join(missing)
            )
        for row in reader:
            t = Tournament.from_csv_row(row)
            if t is not None:
                tournaments.append(t)

    return tournaments


def append_tournament(file_path: str, tournament: Tournament) -> None:
    """Добавить турнир в CSV. При отсутствии файла — создать с заголовком."""
    file_exists = os.path.isfile(file_path)

    with open(file_path, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        if not file_exists:
            writer.writeheader()

        writer.writerow(
            {
                "date": tournament.date.strftime("%Y-%m-%d"),
                "room": tournament.room,
                "name": tournament.name,
                "buy_in": f"{tournament.buy_in:.2f}",
                "rake": f"{tournament.rake:.2f}",
                "currency": tournament.currency,
                "result": f"{tournament.result:.2f}",
                "place": tournament.place,
                "players": tournament.players,
                "format": tournament.format,
                "notes": tournament.notes,
            }
        )


# ==========================
# Фильтрация
# ==========================

def filter_tournaments(
    tournaments: Iterable[Tournament],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    room: Optional[str] = None,
    format_: Optional[str] = None,
    currency: Optional[str] = None,
) -> List[Tournament]:
    """Отфильтровать турниры по заданным параметрам."""
    result: List[Tournament] = []

    for t in tournaments:
        if from_date is not None and t.date < from_date:
            continue
        if to_date is not None and t.date > to_date:
            continue
        if room and t.room.lower() != room.lower():
            continue
        if format_ and t.format.lower() != format_.lower():
            continue
        if currency and t.currency.upper() != currency.upper():
            continue
        result.append(t)

    return result


# ==========================
# Помощники для агрегаций
# ==========================

def calc_summary_stats(tournaments: List[Tournament]) -> Dict[str, Any]:
    """Посчитать сводные показатели по выборке турниров."""
    total = len(tournaments)
    total_itm = sum(1 for t in tournaments if t.is_itm)
    total_buy_in = sum(t.buy_in for t in tournaments)
    total_rake = sum(t.rake for t in tournaments)
    total_cost = total_buy_in + total_rake
    total_result = sum(t.result for t in tournaments)
    profit = total_result - total_cost

    itm_pct = (total_itm / total * 100) if total else 0.0
    roi_pct = (profit / total_cost * 100) if total_cost > 0 else 0.0

    return {
        "total": total,
        "total_itm": total_itm,
        "total_buy_in": total_buy_in,
        "total_rake": total_rake,
        "total_cost": total_cost,
        "total_result": total_result,
        "profit": profit,
        "itm_pct": itm_pct,
        "roi_pct": roi_pct,
    }


def group_by_format(tournaments: List[Tournament]) -> Dict[str, List[Tournament]]:
    groups: Dict[str, List[Tournament]] = defaultdict(list)
    for t in tournaments:
        key = t.format or "UNKNOWN"
        groups[key].append(t)
    return groups


def group_by_buyin_range(tournaments: List[Tournament]) -> Dict[str, List[Tournament]]:
    """
    Группировка по диапазонам бай-инов:
    0–5, 5–11, 11–33, 33+
    """
    ranges = {
        "0–5": [],
        "5–11": [],
        "11–33": [],
        "33+": [],
    }

    for t in tournaments:
        bi = t.buy_in
        if bi < 5:
            ranges["0–5"].append(t)
        elif 5 <= bi < 11:
            ranges["5–11"].append(t)
        elif 11 <= bi < 33:
            ranges["11–33"].append(t)
        else:
            ranges["33+"].append(t)

    return ranges


def group_by_time(
    tournaments: List[Tournament],
    show_by: str,
) -> List[Tuple[str, List[Tournament]]]:
    """
    Группировка турниров по времени:
    - none  — без группировки
    - day   — по дням
    - week  — по неделям (ISO year-week)
    - month — по месяцам (YYYY-MM)
    Возвращает список (ключ, список турниров).
    """
    if show_by == "none":
        return [("ALL", tournaments)]

    buckets: Dict[str, List[Tournament]] = defaultdict(list)

    for t in tournaments:
        if show_by == "day":
            key = t.date.strftime("%Y-%m-%d")
        elif show_by == "week":
            iso_year, iso_week, _ = t.date.isocalendar()
            key = f"{iso_year}-W{iso_week:02d}"
        elif show_by == "month":
            key = t.date.strftime("%Y-%m")
        else:
            key = "ALL"
        buckets[key].append(t)

    return sorted(buckets.items(), key=lambda kv: kv[0])


# ==========================
# Подкоманда summary
# ==========================

def handle_summary(args: argparse.Namespace) -> None:
    try:
        tournaments = load_tournaments(args.file)
    except FileNotFoundError as e:
        print(e)
        return

    from_d = parse_date(args.from_date) if args.from_date else None
    to_d = parse_date(args.to_date) if args.to_date else None

    tournaments = filter_tournaments(
        tournaments,
        from_date=from_d,
        to_date=to_d,
        room=args.room,
        format_=args.format,
        currency=args.currency,
    )

    if not tournaments:
        print("По заданным фильтрам турниров не найдено.")
        return

    print("=== ОБЩИЙ ОТЧЁТ ===")
    overall = calc_summary_stats(tournaments)
    print(f"Турниров всего: {overall['total']}")
    print(
        f"ITM: {overall['total_itm']} "
        f"({overall['itm_pct']:.2f}%)"
    )
    print(
        f"Суммарный бай-ин (без рейка): {overall['total_buy_in']:.2f}, "
        f"рейк: {overall['total_rake']:.2f}"
    )
    print(f"Суммарная стоимость (бай-ин + рейк): {overall['total_cost']:.2f}")
    print(f"Суммарный приз: {overall['total_result']:.2f}")
    print(f"Профит: {overall['profit']:.2f}")
    print(f"ROI: {overall['roi_pct']:.2f}%")
    print()

    # Разбивка по форматам
    print("=== РАЗБИВКА ПО ФОРМАТАМ ===")
    fmt_groups = group_by_format(tournaments)
    for fmt, ts in fmt_groups.items():
        stats = calc_summary_stats(ts)
        print(
            f"- {fmt}: "
            f"турниров={stats['total']}, "
            f"ITM={stats['itm_pct']:.2f}%, "
            f"ROI={stats['roi_pct']:.2f}%, "
            f"профит={stats['profit']:.2f}"
        )
    print()

    # Разбивка по диапазонам бай-ина
    print("=== РАЗБИВКА ПО ДИАПАЗОНАМ БАЙ-ИНОВ ===")
    bi_groups = group_by_buyin_range(tournaments)
    for rng, ts in bi_groups.items():
        if not ts:
            continue
        stats = calc_summary_stats(ts)
        print(
            f"- {rng}: "
            f"турниров={stats['total']}, "
            f"ITM={stats['itm_pct']:.2f}%, "
            f"ROI={stats['roi_pct']:.2f}%, "
            f"профит={stats['profit']:.2f}"
        )
    print()

    # Группировка по времени (по желанию)
    if args.show_by != "none":
        print(f"=== РАЗБИВКА ПО ВРЕМЕНИ ({args.show_by}) ===")
        time_groups = group_by_time(tournaments, args.show_by)
        for key, ts in time_groups:
            stats = calc_summary_stats(ts)
            print(
                f"{key}: турниров={stats['total']}, "
                f"профит={stats['profit']:.2f}, "
                f"ROI={stats['roi_pct']:.2f}%, "
                f"ITM={stats['itm_pct']:.2f}%"
            )
        print()

        # Экспорт, если нужен
        if args.export:
            with open(args.export, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["period", "count", "itm_pct", "roi_pct", "profit"])
                for key, ts in time_groups:
                    stats = calc_summary_stats(ts)
                    writer.writerow(
                        [
                            key,
                            stats["total"],
                            f"{stats['itm_pct']:.2f}",
                            f"{stats['roi_pct']:.2f}",
                            f"{stats['profit']:.2f}",
                        ]
                    )
            print(f"Агрегированные данные по периодам сохранены в {args.export}")


# ==========================
# Подкоманда add
# ==========================

def handle_add(args: argparse.Namespace) -> None:
    if args.date:
        try:
            d = parse_date(args.date)
        except Exception:
            print("Ошибка: неправильный формат даты, ожидается YYYY-MM-DD")
            return
    else:
        d = date.today()

    def f_or_default(v: Optional[str], default: float) -> float:
        if v is None:
            return default
        try:
            return float(v)
        except ValueError:
            return default

    def i_or_default(v: Optional[str], default: int) -> int:
        if v is None:
            return default
        try:
            return int(v)
        except ValueError:
            return default

    t = Tournament(
        date=d,
        room=args.room or "PokerOK",
        name=args.name,
        buy_in=f_or_default(args.buy_in, 0.0),
        rake=f_or_default(args.rake, 0.0),
        currency=(args.currency or "USD").upper(),
        result=f_or_default(args.result, 0.0),
        place=i_or_default(args.place, 0),
        players=i_or_default(args.players, 0),
        format=args.format or "MTT",
        notes=args.notes or "",
    )

    append_tournament(args.file, t)

    print("Турнир добавлен.")
    print(f"Дата: {t.date}")
    print(f"Название: {t.name}")
    print(f"Рум: {t.room}")
    print(f"Бай-ин: {t.buy_in:.2f} + {t.rake:.2f} рейк")
    print(f"Результат: {t.result:.2f}")
    print(f"Профит: {t.profit:.2f}")


# ==========================
# Подкоманда graph
# ==========================

def handle_graph(args: argparse.Namespace) -> None:
    try:
        import matplotlib.pyplot as plt  # локальный импорт
    except ImportError:
        print(
            "Ошибка: для подкоманды 'graph' требуется установленный matplotlib.\n"
            "Установите его командой: pip install matplotlib"
        )
        return

    try:
        tournaments = load_tournaments(args.file)
    except FileNotFoundError as e:
        print(e)
        return

    from_d = parse_date(args.from_date) if args.from_date else None
    to_d = parse_date(args.to_date) if args.to_date else None

    tournaments = filter_tournaments(
        tournaments,
        from_date=from_d,
        to_date=to_d,
        room=args.room,
        format_=args.format,
        currency=args.currency,
    )

    if not tournaments:
        print("По заданным фильтрам турниров не найдено.")
        return

    tournaments.sort(key=lambda t: t.date)

    x_dates: List[date] = []
    y_values: List[float] = []

    metric = args.metric
    if metric not in ("profit", "bankroll"):
        print("Ошибка: --metric должен быть 'profit' или 'bankroll'")
        return

    cumulative = 0.0
    if metric == "bankroll":
        if args.start_bankroll is None:
            print(
                "Ошибка: для метрики 'bankroll' необходимо указать "
                "--start-bankroll"
            )
            return
        cumulative = float(args.start_bankroll)

    for t in tournaments:
        tournament_profit = t.profit
        if metric == "profit":
            cumulative += tournament_profit
        else:  # bankroll
            cumulative += tournament_profit
        x_dates.append(t.date)
        y_values.append(cumulative)

    plt.figure()
    plt.plot(x_dates, y_values, marker="o")
    plt.xlabel("Дата")
    plt.ylabel("Профит" if metric == "profit" else "Банкролл")
    plt.title(
        "График профита" if metric == "profit" else "График динамики банкролла"
    )
    plt.grid(True)

    if args.output:
        plt.savefig(args.output)
        print(f"График сохранён в файл: {args.output}")

    plt.show()


# ==========================
# Подкоманда details
# ==========================

def handle_details(args: argparse.Namespace) -> None:
    try:
        tournaments = load_tournaments(args.file)
    except FileNotFoundError as e:
        print(e)
        return

    from_d = parse_date(args.from_date) if args.from_date else None
    to_d = parse_date(args.to_date) if args.to_date else None

    tournaments = filter_tournaments(
        tournaments,
        from_date=from_d,
        to_date=to_d,
        room=args.room,
        format_=args.format,
        currency=args.currency,
    )

    if not tournaments:
        print("По заданным фильтрам турниров не найдено.")
        return

    tournaments.sort(key=lambda t: t.date)

    if args.limit is not None and args.limit > 0:
        tournaments = tournaments[: args.limit]

    # Заголовок таблицы
    header = (
        f"{'DATE':<12} {'NAME':<25} {'BUY-IN':>8} {'RESULT':>8} "
        f"{'PROFIT':>8} {'PLACE':>5} {'PLAYRS':>6} {'FMT':<8}"
    )
    print(header)
    print("-" * len(header))

    for t in tournaments:
        buy_in_total = t.total_cost
        print(
            f"{t.date.strftime('%Y-%m-%d'):<12} "
            f"{t.name[:24]:<25} "
            f"{buy_in_total:>8.2f} "
            f"{t.result:>8.2f} "
            f"{t.profit:>8.2f} "
            f"{t.place:>5d} "
            f"{t.players:>6d} "
            f"{(t.format or '')[:7]:<8}"
        )


# ==========================
# CLI
# ==========================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Анализатор турнирных результатов (PokerOK и др.)"
    )
    parser.set_defaults(func=None)

    subparsers = parser.add_subparsers(dest="command")

    # Общие параметры для чтения CSV
    common_read = argparse.ArgumentParser(add_help=False)
    common_read.add_argument(
        "--file",
        default="tournaments.csv",
        help="Путь к CSV-файлу с турнирами (по умолчанию tournaments.csv)",
    )
    common_read.add_argument(
        "--from",
        dest="from_date",
        help="Дата начала периода (YYYY-MM-DD)",
    )
    common_read.add_argument(
        "--to",
        dest="to_date",
        help="Дата конца периода (YYYY-MM-DD)",
    )
    common_read.add_argument(
        "--room",
        help="Фильтр по руму (например, PokerOK)",
    )
    common_read.add_argument(
        "--format",
        help="Фильтр по формату (MTT, SnG, PKO и т.п.)",
    )
    common_read.add_argument(
        "--currency",
        help="Фильтр по валюте (USD, EUR, RUB и т.п.)",
    )

    # summary
    summary_parser = subparsers.add_parser(
        "summary",
        parents=[common_read],
        help="Сводный отчёт по турнирам",
    )
    summary_parser.add_argument(
        "--show-by",
        choices=["none", "day", "week", "month"],
        default="none",
        help="Группировка по времени (по умолчанию none)",
    )
    summary_parser.add_argument(
        "--export",
        help="Путь к CSV для экспорта агрегированных данных по периодам",
    )
    summary_parser.set_defaults(func=handle_summary)

    # add
    add_parser = subparsers.add_parser(
        "add",
        help="Добавить один турнир в CSV",
    )
    add_parser.add_argument(
        "--file",
        default="tournaments.csv",
        help="CSV-файл (по умолчанию tournaments.csv)",
    )
    add_parser.add_argument(
        "--date",
        help="Дата турнира YYYY-MM-DD (по умолчанию сегодня)",
    )
    add_parser.add_argument(
        "--room",
        help="Рум, по умолчанию PokerOK",
    )
    add_parser.add_argument(
        "--name",
        required=True,
        help="Название турнира",
    )
    add_parser.add_argument(
        "--buy-in",
        help="Бай-ин без рейка",
    )
    add_parser.add_argument(
        "--rake",
        help="Рейк",
    )
    add_parser.add_argument(
        "--currency",
        help="Валюта (по умолчанию USD)",
    )
    add_parser.add_argument(
        "--result",
        help="Полученный приз (0, если не ITM)",
    )
    add_parser.add_argument(
        "--place",
        help="Занятое место (целое число)",
    )
    add_parser.add_argument(
        "--players",
        help="Количество участников",
    )
    add_parser.add_argument(
        "--format",
        help="Формат (MTT, SnG, PKO и т.п., по умолчанию MTT)",
    )
    add_parser.add_argument(
        "--notes",
        help="Заметки (опционально)",
    )
    add_parser.set_defaults(func=handle_add)

    # graph
    graph_parser = subparsers.add_parser(
        "graph",
        parents=[common_read],
        help="Построить график профита или банкролла",
    )
    graph_parser.add_argument(
        "--metric",
        choices=["profit", "bankroll"],
        default="profit",
        help="Метрика: profit (кумулятивный профит) или bankroll (динамика банкролла)",
    )
    graph_parser.add_argument(
        "--start-bankroll",
        type=float,
        help="Начальный банкролл (обязательно при --metric bankroll)",
    )
    graph_parser.add_argument(
        "--output",
        help="Путь для сохранения графика (PNG)",
    )
    graph_parser.set_defaults(func=handle_graph)

    # details
    details_parser = subparsers.add_parser(
        "details",
        parents=[common_read],
        help="Список турниров с фильтрами",
    )
    details_parser.add_argument(
        "--limit",
        type=int,
        help="Ограничить количество выводимых турниров",
    )
    details_parser.set_defaults(func=handle_details)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.func is None:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()