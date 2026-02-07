# Трекер результатов MTT/SnG на ПокерОк

Анализатор турнирных результатов для рума PokerOK на Python. Скрипт работает с CSV-логом турниров и помогает:

- вести историю MTT / SnG турниров;
- считать:
  - общий профит;
  - ROI;
  - ITM%;
  - суммарные бай-ины / рейк / призы;
- смотреть статистику по форматам и диапазонам бай-инов;
- быстро добавлять новые турниры через командную строку;
- строить графики:
  - кумулятивного профита;
  - динамики банкролла;
- просматривать детальный список турниров с фильтрами.

Скрипт не привязан жёстко к одному руму, но ориентирован в первую очередь на GG PokerOK.

---

## Требования

- Python 3.8+
- Для команды `graph` дополнительно нужен `matplotlib`:

```bash
pip install matplotlib
````

---

## Установка

1. Склонировать репозиторий:

```bash
git clone https://github.com/PokerOk-H1/Tournament-Results-Tracker.git
cd Tournament-Results-Tracker
```

2. Убедиться, что Python установлен:

```bash
python --version
# или
python3 --version
```

3. (Опционально) Установить зависимости для графиков:

```bash
pip install matplotlib
```

---

## Формат данных (tournaments.csv)

По умолчанию скрипт использует файл `tournaments.csv` в корне проекта.

### Заголовки CSV

Первая строка файла должна содержать заголовки:

```csv
date,room,name,buy_in,rake,currency,result,place,players,format,notes
```

### Описание полей

* `date` — дата турнира (формат `YYYY-MM-DD`, например: `2025-12-03`)
* `room` — рум (`PokerOK`, `GG`, `Stars`, и т.д.)
* `name` — название турнира (`Daily Main`, `Sunday PKO`, ...)
* `buy_in` — бай-ин **без рейка** (float, с точкой)
* `rake` — рейк (float)
* `currency` — валюта (`USD`, `EUR`, `RUB`, и т.п.)
* `result` — полученный приз (0, если не ITM)
* `place` — занятое место (целое число, `1` — победа)
* `players` — количество участников (целое число)
* `format` — формат турнира (`MTT`, `SnG`, `PKO`, `Turbo`, `Bounty`, …)
* `notes` — любые заметки (можно оставить пустым)

### Пример строки

```csv
2025-11-30,PokerOK,Daily Main,10,1,USD,45,3,120,MTT,"Deep run, coolered on FT"
```

> Разделитель — запятая `,`.
> Десятичный разделитель — точка `.`.
> Кодировка — UTF-8.

---

## Запуск

Общий формат:

```bash
python tournament.py <команда> [опции]
# или
python3 tournament.py <команда> [опции]
```

Основные команды:

* `summary` — сводный отчёт;
* `add` — добавить один турнир в CSV;
* `graph` — построить график профита/банкролла;
* `details` — детальный список турниров.

---

## Общие фильтры

Многие команды принимают одинаковые параметры для фильтрации:

```bash
--file PATH       # путь к CSV (по умолчанию tournaments.csv)
--from YYYY-MM-DD # дата начала периода (включительно)
--to YYYY-MM-DD   # дата конца периода (включительно)
--room ROOM       # рум (PokerOK, GG, ...)
--format FORMAT   # формат (MTT, SnG, PKO и т.п.)
--currency CUR    # валюта (USD, EUR, RUB, ...)
```

Например:

```bash
python tournament.py summary --from 2025-11-01 --to 2025-11-30 --room PokerOK
```

---

## Команда `summary` — сводный отчёт

Сводная статистика за выбранный период.

```bash
python tournament.py summary [опции]
```

### Примеры

Все турниры:

```bash
python tournament.py summary
```

Только PokerOK за ноябрь 2025:

```bash
python tournament.py summary --room PokerOK --from 2025-11-01 --to 2025-11-30
```

Только MTT в долларах:

```bash
python tournament.py summary --format MTT --currency USD
```

### Группировка по времени

Опция:

```bash
--show-by none|day|week|month
```

Примеры:

```bash
# Группировка по дням
python tournament.py summary --show-by day

# Группировка по неделям
python tournament.py summary --show-by week

# Группировка по месяцам
python tournament.py summary --show-by month
```

### Экспорт агрегированных данных

Если используется `--show-by`, можно экспортировать сгруппированную статистику в CSV:

```bash
python tournament.py summary --show-by month --export monthly_report.csv
```

В файл попадут колонки:

* `period` — период (день, неделя, месяц);
* `count` — количество турниров;
* `itm_pct` — ITM%;
* `roi_pct` — ROI%;
* `profit` — суммарный профит.

---

## Команда `add` — добавление турнира

Быстрое добавление одной записи в CSV-файл через параметры командной строки.

```bash
python tournament.py add [опции]
```

### Основные параметры

* `--file` — путь к CSV (по умолчанию `tournaments.csv`)
* `--date` — дата турнира (`YYYY-MM-DD`, по умолчанию — сегодняшняя)
* `--room` — рум (по умолчанию `PokerOK`)
* `--name` — **обязательный** параметр, название турнира
* `--buy-in` — бай-ин без рейка
* `--rake` — рейк
* `--currency` — валюта (по умолчанию `USD`)
* `--result` — приз
* `--place` — место
* `--players` — количество участников
* `--format` — формат (`MTT` по умолчанию)
* `--notes` — заметки

### Примеры

Добавление турнира:

```bash
python tournament.py add \
  --date 2025-12-03 \
  --room PokerOK \
  --name "Daily Main" \
  --buy-in 10 \
  --rake 1 \
  --currency USD \
  --result 45 \
  --place 3 \
  --players 120 \
  --format MTT \
  --notes "Deep run, финалка"
```

Если `tournaments.csv` ещё не существует, он будет создан автоматически с заголовком.

---

## Команда `graph` — графики профита и банкролла

Построение графиков на основе истории турниров. Требуется установленный `matplotlib`.

```bash
python tournament.py graph [опции]
```

### Метрики

```bash
--metric profit|bankroll
```

* `profit` — кумулятивный профит;
* `bankroll` — динамика банкролла.

Для `bankroll` обязательно указать начальный банкролл:

```bash
--start-bankroll FLOAT
```

### Примеры

График кумулятивного профита за всё время:

```bash
python tournament.py graph --metric profit
```

График банкролла за ноябрь 2025, стартовый банкролл 100$:

```bash
python tournament.py graph \
  --metric bankroll \
  --start-bankroll 100 \
  --from 2025-11-01 \
  --to 2025-11-30
```

Сохранение графика в файл:

```bash
python tournament.py graph --metric profit --output profit_november.png
```

---

## Команда `details` — детальный список турниров

Выводит таблицу турниров с выбранными фильтрами.

```bash
python tournament.py details [опции]
```

### Дополнительные параметры

* `--limit N` — ограничивает количество выводимых строк.

### Примеры

Все турниры:

```bash
python tournament.py details
```

Только PKO-турниры за месяц, не более 20 строк:

```bash
python tournament.py details --format PKO --from 2025-11-01 --to 2025-11-30 --limit 20
```

Вывод будет примерно таким:

```text
DATE        NAME                      BUY-IN   RESULT   PROFIT PLACE PLAYRS FMT     
-----------------------------------------------------------------------------------
2025-11-30  Daily Main                  11.00    45.00    34.00     3    120 MTT     
2025-11-28  PKO Madness                  5.50     0.00    -5.50   240    800 PKO     
...
```

---

## Обработка ошибок

Скрипт пытается быть максимально дружелюбным:

* Если файл CSV не найден (для `summary`, `graph`, `details`) — выводится понятное сообщение;
* При некорректных числовых значениях строки не ломают выполнение, но помечаются предупреждением;
* При неправильном формате даты выводится ошибка;
* Если после фильтрации турниров нет — выводится сообщение:
  `По заданным фильтрам турниров не найдено.`
* Для `graph` при метрике `bankroll` без `--start-bankroll` также выводится понятная ошибка.

---

## Как внести вклад

Pull Request’ы приветствуются.

Примерный процесс:

1. Сделать форк репозитория.
2. Создать ветку для своей фичи/фикса:

   ```bash
   git checkout -b feature/my-improvement
   ```
3. Внести изменения, добавить/обновить примеры.
4. Открыть Pull Request в репозиторий `Tournament-Results-Tracker`.

Если у вас есть идеи по улучшению логики анализа (например, свои диапазоны бай-инов или дополнительные метрики), их можно описать в разделе Issues.

---

## Лицензия

Проект распространяется по лицензии **MIT**. Полный текст лицензии — в файле [`LICENSE`](./LICENSE).
