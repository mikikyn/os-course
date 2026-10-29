#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RESULTS="results.txt"
: > "$RESULTS"
exec 3>&1 4>&2
exec > >(tee -a "$RESULTS") 2>&1

echo "=== ПР-3, вариант B: процессы в Linux ==="
date
echo '$ python3 --version'
python3 --version
echo

echo '$ python3 ptree.py'
python3 ptree.py > ptree_output.txt
head -n 40 ptree_output.txt
echo

echo '$ python3 runner.py 3 /bin/sleep 1'
python3 runner.py 3 /bin/sleep 1
echo

echo '$ python3 zombie.py  # одновременно снимаем вывод ps'
python3 zombie.py > zombie_output.txt &
ZOMBIE_PARENT=$!
sleep 2
ZOMBIE_CHILD="$(ps -o pid= --ppid "$ZOMBIE_PARENT" | awk 'NR == 1 {print $1}')"
echo '$ ps -o pid,ppid,stat,cmd -p РОДИТЕЛЬ,РЕБЁНОК'
ps -o pid,ppid,stat,cmd -p "$ZOMBIE_PARENT","$ZOMBIE_CHILD"
wait "$ZOMBIE_PARENT"
cat zombie_output.txt
echo

echo '$ python3 orphan.py  # одновременно снимаем вывод ps'
rm -f orphan.pid
python3 orphan.py > orphan_output.txt &
ORPHAN_PARENT=$!
sleep 2
ORPHAN_CHILD="$(cat orphan.pid)"
echo '$ ps -o pid,ppid,stat,cmd -p СИРОТА'
ps -o pid,ppid,stat,cmd -p "$ORPHAN_CHILD"
ADOPT_PPID="$(ps -o ppid= -p "$ORPHAN_CHILD" | tr -d ' ')"
ADOPT_NAME="$(ps -o comm= -p "$ADOPT_PPID" | tr -d ' ')"
wait "$ORPHAN_PARENT"
sleep 3
cat orphan_output.txt
rm -f orphan.pid
echo

echo '$ python3 cow.py'
python3 cow.py | tee cow_output.txt
echo

echo '=== Автоматическая проверка ==='
grep -q 'Z (zombie)' zombie_output.txt
grep -q 'после ухода родителя' orphan_output.txt
grep -q 'Списки различаются' cow_output.txt
if [[ -e "/proc/$ORPHAN_CHILD" ]]; then
    echo "Ошибка: дочерний процесс-сирота ещё остался." >&2
    exit 1
fi
echo 'OK: дерево, fork/exec/wait, zombie, orphan и copy-on-write проверены; фоновых процессов не осталось.'

exec 1>&3 2>&4

if [[ -n "$ADOPT_PPID" && -n "$ADOPT_NAME" ]]; then
    ADOPT_TEXT="В этой системе сироту усыновил процесс PID=$ADOPT_PPID ($ADOPT_NAME). Это видно по изменившемуся PPID ребёнка."
else
    ADOPT_TEXT="Новый PPID показан в выводе выше: после завершения начального родителя сирота был усыновлён системным процессом."
fi

cat > README.md <<'EOF'
# Практическая работа № 3 — процессы в Linux

**Вариант:** B  
**Среда:** Ubuntu 22.04+, Python 3.11+

## Цель

Изучить дерево процессов, создание и завершение через `fork/exec/wait`, состояния zombie и orphan, а также ленивое копирование памяти copy-on-write.

## Файлы

- `ptree.py` — дерево процессов текущего пользователя только по `/proc`, без `ps`;
- `runner.py` — N дочерних процессов через `fork` и `exec`, ожидание и время каждого;
- `zombie.py` — временный zombie с последующим `waitpid`;
- `orphan.py` — усыновление сироты после завершения родителя;
- `cow.py` — память ребёнка до и после изменения унаследованного списка;
- `results.txt`, `ptree_output.txt`, `zombie_output.txt`, `orphan_output.txt`, `cow_output.txt` — результаты запуска.

## Запуск

```bash
bash run.sh
```

Отдельные команды:

```bash
python3 ptree.py
python3 runner.py 3 /bin/sleep 1
python3 zombie.py
python3 orphan.py
python3 cow.py
```

Для ручного наблюдения zombie или orphan можно запустить соответствующий скрипт в одном терминале, а в другом выполнить `ps -eo pid,ppid,stat,cmd`.

## Реальные результаты

```text
EOF
cat "$RESULTS" >> README.md
cat >> README.md <<EOF
\`\`\`

## Объяснение

### Zombie

Zombie — это уже завершившийся процесс, запись о котором остаётся в таблице процессов, пока родитель не прочитает код завершения через \`wait\`/\`waitpid\`. На выводе \`ps\` виден статус \`Z\`. После \`waitpid\` запись исчезает. Если родитель завершается, не забрав статус, система усыновляет его детей и затем убирает такие записи.

### Orphan

Сирота — процесс, чей родитель завершился раньше него. Сам ребёнок при этом продолжает работать. $ADOPT_TEXT

### Copy-on-write

Сразу после \`fork\` родитель и ребёнок используют одни физические страницы памяти. Поэтому измерять только \`VmRSS\` недостаточно: RSS может показывать похожие числа и до, и после записи. При изменении данных ребёнком ядро копирует затронутые страницы. В \`smaps_rollup\` это видно по уменьшению \`Shared_Dirty\` и росту \`Private_Dirty\` у ребёнка. Разные контрольные суммы родителя и ребёнка подтверждают, что изменения не попали обратно в память родителя.

## Контрольные вопросы

### Почему fork возвращает два разных значения?

После \`fork\` выполняются два процесса. Родителю возвращается PID нового ребёнка, чтобы родитель мог ждать его или управлять им. Ребёнку возвращается \`0\`, а при ошибке родитель получает \`-1\`.

### Что изменится, если вызвать exec без fork?

\`exec\` заменит код текущего процесса новой программой. PID сохранится, но прежняя программа перестанет выполняться и не получит управление после завершения новой. Поэтому оболочка обычно сначала делает \`fork\`, а \`exec\` выполняет только ребёнок.

## Вывод

Дерево построено напрямую по \`/proc\`. \`runner.py\` создал и дождался всех детей, выведя коды и время. Zombie убран через \`waitpid\`, сирота завершился после усыновления, а эксперимент COW показал копирование страниц только при записи. После проверочного запуска фоновых процессов не остаётся.
EOF

printf '\nГотово: %s/README.md заполнен реальными результатами.\n' "$SCRIPT_DIR"
