#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'EOF'
Использование:
  bash report.sh КАТАЛОГ УРОВЕНЬ [--top N]

Аргументы:
  КАТАЛОГ   каталог с файлами *.log
  УРОВЕНЬ   ERROR или WARN
  --top N   показать только первые N модулей

Пример:
  bash report.sh data ERROR --top 3
EOF
}

if (( $# < 2 )); then
    usage >&2
    exit 1
fi

LOG_DIR=$1
LEVEL=$2
shift 2
TOP=0

if (( $# > 0 )); then
    if (( $# == 2 )) && [[ $1 == "--top" && $2 =~ ^[1-9][0-9]*$ ]]; then
        TOP=$2
    else
        echo "Ошибка: неверные аргументы." >&2
        usage >&2
        exit 1
    fi
fi

if [[ ! -d $LOG_DIR ]]; then
    echo "Ошибка: каталог '$LOG_DIR' не существует." >&2
    exit 1
fi

if [[ $LEVEL != "ERROR" && $LEVEL != "WARN" ]]; then
    echo "Ошибка: уровень должен быть ERROR или WARN." >&2
    exit 1
fi

shopt -s nullglob
LOG_FILES=("$LOG_DIR"/*.log)
if (( ${#LOG_FILES[@]} == 0 )); then
    echo "Ошибка: в каталоге '$LOG_DIR' нет файлов *.log." >&2
    exit 1
fi

awk -v wanted="$LEVEL" '
{
    if ($3 != wanted) {
        next
    }
    for (i = 4; i <= NF; i++) {
        if ($i ~ /^module=/) {
            module = substr($i, 8)
            counts[module]++
            break
        }
    }
}
END {
    for (module in counts) {
        printf "%s\t%d\n", module, counts[module]
    }
}
' "${LOG_FILES[@]}" |
    sort -t $'\t' -k2,2nr -k1,1 |
    awk -F '\t' -v top="$TOP" '
BEGIN {
    printf "%-20s %10s\n", "МОДУЛЬ", "СООБЩЕНИЙ"
    printf "%-20s %10s\n", "--------------------", "----------"
}
top == 0 || NR <= top {
    printf "%-20s %10d\n", $1, $2
}
'
