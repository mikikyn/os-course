#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RESULTS="results.txt"
: > "$RESULTS"
exec 3>&1 4>&2
exec > >(tee -a "$RESULTS") 2>&1

echo "=== ПР-5, вариант B: планирование CPU ==="
date
echo '$ python3 --version'
python3 --version
echo

echo '$ python3 selftest.py'
python3 selftest.py
echo

echo '$ python3 sched.py --algo srtf set1.txt'
python3 sched.py --algo srtf set1.txt
echo

echo '$ python3 sched.py --algo rr --quantum 3 set1.txt'
python3 sched.py --algo rr --quantum 3 set1.txt
echo

echo '$ python3 compare.py'
python3 compare.py
echo

echo '$ python3 rr_sweep.py'
python3 rr_sweep.py
echo

echo '$ python3 aging_demo.py'
python3 aging_demo.py | tee aging_output.txt
echo

echo '=== Автоматическая проверка ==='
[[ -s comparison.csv ]]
[[ -s rr_sweep.csv ]]
[[ -s rr_sweep.png ]]
grep -q 'Все пять алгоритмов совпали' "$RESULTS"
grep -q 'Улучшение отклика LP' aging_output.txt
echo 'OK: эталоны, метрики, три набора, RR sweep, PNG и aging проверены.'

exec 1>&3 2>&4

cat > README.md <<'EOF'
# Практическая работа № 5 — симулятор планирования CPU

**Вариант:** B  
**Среда:** Ubuntu 22.04+, Python 3.11+; внешние пакеты не нужны

## Цель

Реализовать FCFS, SJF, SRTF, вытесняющий Priority и Round Robin, сравнить метрики, исследовать квант RR и показать устранение голодания через aging.

## Файлы

- `sched.py` — единая функция `simulate(processes, algorithm, **params)` и CLI;
- `selftest.py` — сверка всех эталонов set1;
- `compare.py`, `comparison.csv` — алгоритмы × наборы × метрики;
- `rr_sweep.py`, `rr_sweep.csv`, `rr_sweep.png` — кванты 1…10 на set2;
- `aging_demo.py`, `aging_output.txt`, `starve.txt` — голодание и старение;
- `plot_png.py` — построение PNG стандартной библиотекой;
- `results.txt` — полный проверочный вывод.

## Запуск

```bash
bash run.sh
```

Отдельные примеры:

```bash
python3 sched.py --algo rr --quantum 3 set1.txt
python3 sched.py --algo srtf set1.txt
python3 compare.py
python3 rr_sweep.py
python3 aging_demo.py
```

## Реальные результаты

```text
EOF
cat "$RESULTS" >> README.md
cat >> README.md <<'EOF'
```

## Как считаются метрики

- Оборот: `completion − arrival`.
- Ожидание: `оборот − burst`.
- Отклик: `первый запуск − arrival`.
- Загрузка CPU: занятое процессами время / общее время от нулевого тика до последнего завершения × 100%.
- Переключения: смена одного непосредственного PID на другой на границах интервалов; переходы через IDLE не считаются переключением двух процессов.

Для RR соблюдено правило методички: процессы, прибывшие к моменту окончания кванта, ставятся в очередь раньше вытесненного процесса. При равенстве критериев используется раннее прибытие, затем меньший номер PID.

## Компромисс кванта RR

При маленьком кванте система чаще переключается: интерактивный отклик может улучшаться, но растут накладные расходы. При увеличении кванта число переключений падает, а RR постепенно приближается к FCFS. Среднее ожидание не обязано меняться строго монотонно, потому что порядок интервалов зависит от конкретных времён прибытия и burst.

## Aging и голодание

В `starve.txt` длинный LP имеет приоритет 10, а короткие процессы с приоритетом 1 регулярно прибывают. Без старения LP ждёт окончания всего потока HP. При старении каждые 2 тика его эффективный приоритет повышается с учётом ожидания, поэтому LP запускается раньше. Главный показатель здесь — **response LP**, а не среднее ожидание всех процессов: среднее может ухудшиться, хотя голодание конкретного LP устранено.

## Контрольные вопросы

### Почему SJF нельзя применять в реальной ОС напрямую?

Заранее точная длительность следующего CPU burst обычно неизвестна. Её можно только прогнозировать по прошлому поведению. Кроме того, при постоянном потоке коротких задач длинные могут голодать.

### Что происходит при кванте RR, стремящемся к бесконечности?

Процесс не вытесняется до завершения своего burst, поэтому Round Robin вырождается в FCFS.

## Вывод

Все пять алгоритмов совпали с эталонами set1. На set2 и set3 метрики сравниваются в `comparison.csv`. График показывает снижение числа переключений с ростом кванта, а aging уменьшает время первого отклика голодающего LP.
EOF

printf '\nГотово: %s/README.md заполнен реальными результатами.\n' "$SCRIPT_DIR"
