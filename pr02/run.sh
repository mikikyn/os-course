#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v strace > /dev/null 2>&1; then
    echo "Не найден strace. Установи его командой: sudo apt update && sudo apt install -y strace"
    exit 1
fi

shopt -s nullglob
EXISTING_LOGS=(data/*.log)
if (( ${#EXISTING_LOGS[@]} == 0 )); then
    python3 generate_data.py data
fi

SAMPLE="data/01.log"
RESULTS="results.txt"
: > "$RESULTS"
exec 3>&1 4>&2
exec > >(tee -a "$RESULTS") 2>&1

echo "=== ПР-2, вариант B: Bash и системные вызовы ==="
date
echo '$ python3 --version'
python3 --version
echo '$ strace --version | head -n 1'
strace --version | head -n 1
echo

echo '$ bash report.sh data ERROR'
bash report.sh data ERROR
echo

echo '$ bash report.sh data WARN --top 3'
bash report.sh data WARN --top 3
echo

echo '$ bash report.sh  # проверка запуска без аргументов'
set +e
NO_ARGS_OUTPUT="$(bash report.sh 2>&1)"
NO_ARGS_STATUS=$?
set -e
printf '%s\n' "$NO_ARGS_OUTPUT"
printf 'Код возврата без аргументов: %d\n' "$NO_ARGS_STATUS"
if (( NO_ARGS_STATUS != 1 )); then
    echo "Ошибка проверки: без аргументов ожидался код 1." >&2
    exit 1
fi
echo

echo '$ python3 hello.py data/01.log'
python3 hello.py "$SAMPLE"
echo

echo '$ strace -f -o trace.txt python3 hello.py data/01.log'
strace -f -o trace.txt python3 hello.py "$SAMPLE"
echo '$ strace -f -o trace_cat.txt cat data/01.log'
strace -f -o trace_cat.txt cat "$SAMPLE" > /dev/null
echo

echo '$ python3 analyze_trace.py --python-trace trace.txt --cat-trace trace_cat.txt --sample data/01.log'
python3 analyze_trace.py --python-trace trace.txt --cat-trace trace_cat.txt --sample "$SAMPLE"
echo

echo '=== Автоматическая проверка ==='
[[ -s trace.txt ]]
[[ -s trace_cat.txt ]]
bash report.sh data ERROR --top 1 | grep -q 'МОДУЛЬ'
echo 'OK: report.sh, --top, код возврата, hello.py и обе трассировки проверены.'

exec 1>&3 2>&4

cat > README.md <<'EOF'
# Практическая работа № 2 — Bash и системные вызовы

**Вариант:** B  
**Среда:** Ubuntu 22.04+, Python 3.11+, strace

## Цель

Написать Bash-скрипт для анализа журналов и сравнить системные вызовы обычной утилиты `cat` и программы на Python.

## Файлы

- `report.sh` — таблица «модуль → число сообщений» для ERROR/WARN, поддержка `--top N`;
- `hello.py` — читает файл и выводит размер;
- `generate_data.py` — создаёт 50 учебных журналов, если каталог `data/` пуст;
- `analyze_trace.py` — подсчитывает вызовы в трассировках;
- `trace.txt` — полная трассировка `python3 hello.py`;
- `trace_cat.txt` — трассировка `cat` для сравнения;
- `results.txt` — вывод проверочного запуска.

## Запуск

```bash
sudo apt update && sudo apt install -y strace
bash run.sh
```

После запуска этот README автоматически заполняется реальными результатами.

Отдельные команды:

```bash
bash report.sh data ERROR
bash report.sh data WARN --top 3
python3 hello.py data/01.log
strace -f -o trace.txt python3 hello.py data/01.log
```

## Реальные результаты

```text
EOF
cat "$RESULTS" >> README.md
cat >> README.md <<'EOF'
```

## Анализ трассировки

Полный вывод `strace` находится в `trace.txt`, а не вставлен целиком в README. Для подсчёта использованы строки самих системных вызовов; служебные строки завершения процессов в общее число не входят. К чтению учебного файла отнесены его `openat`, вызовы `read` на выданном файловом дескрипторе и `close`.

Python выполняет значительно больше системных вызовов, чем `cat`: до чтения указанного файла интерпретатор загружает исполняемый код, динамические библиотеки, стандартные модули и настраивает среду выполнения. `cat` — небольшая скомпилированная утилита, поэтому её накладные расходы намного ниже.

## Контрольные вопросы

### Почему нельзя обратиться к диску напрямую из пользовательской программы?

Диском управляет ядро через драйверы. Прямой доступ из пользовательской программы нарушил бы изоляцию процессов, права доступа и целостность файловой системы. Поэтому программа обращается к ядру через системные вызовы, а ядро проверяет права и выполняет операцию.

### Что дороже — вызов функции или системный вызов?

Системный вызов дороже. Обычный вызов функции остаётся в пользовательском режиме, а системный требует перехода в режим ядра, проверки аргументов и прав, выполнения кода ядра и возврата в пользовательский режим.

## Вывод

`report.sh` фильтрует сообщения по уровню, группирует их по модулям и сортирует по убыванию числа сообщений. Режим `--top N`, справка без аргументов с кодом 1 и проверка каталога реализованы. Трассировка показывает, что основная работа по чтению файла занимает лишь несколько вызовов, а большая часть вызовов Python относится к запуску интерпретатора.
EOF

printf '\nГотово: %s/README.md заполнен реальными результатами.\n' "$SCRIPT_DIR"
