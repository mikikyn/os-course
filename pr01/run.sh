#!/usr/bin/env bash
set -euo pipefail

if (( EUID != 0 )); then
    echo "Нужны права администратора. Запусти: sudo bash run.sh"
    exit 1
fi

MAIN_USER="${SUDO_USER:-}"
if [[ -z "$MAIN_USER" || "$MAIN_USER" == "root" ]]; then
    echo "Не удалось определить основного пользователя. Запускай через sudo из своей обычной учётной записи."
    exit 1
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
RESULTS="$SCRIPT_DIR/results.txt"
SHARED_DIR="/srv/shared"
SHARED_FILE="$SHARED_DIR/student2.txt"
MAIN_HOME="$(getent passwd "$MAIN_USER" | cut -d: -f6)"
BASHRC="$MAIN_HOME/.bashrc"

if [[ -z "$MAIN_HOME" || ! -d "$MAIN_HOME" ]]; then
    echo "Домашний каталог пользователя $MAIN_USER не найден."
    exit 1
fi

: > "$RESULTS"
exec 3>&1 4>&2
exec > >(tee -a "$RESULTS") 2>&1

echo "=== ПР-1, вариант B: настройка пользователей и прав ==="
date
printf 'Основной пользователь: %s\n\n' "$MAIN_USER"

echo '$ git --version'
git --version
echo '$ python3 --version'
python3 --version
echo

echo '$ sudo groupadd developers  # выполняется только если группы ещё нет'
if ! getent group developers > /dev/null; then
    groupadd developers
fi
getent group developers

echo '$ sudo adduser --disabled-password --gecos "" student2  # если пользователя ещё нет'
if ! id student2 > /dev/null 2>&1; then
    adduser --disabled-password --gecos "" student2
fi

echo '$ sudo usermod -aG developers student2'
usermod -aG developers student2
echo '$ id student2'
id student2
echo

echo '$ sudo mkdir -p /srv/shared'
mkdir -p "$SHARED_DIR"
echo '$ sudo chown root:developers /srv/shared'
chown root:developers "$SHARED_DIR"
echo '$ sudo chmod 2775 /srv/shared'
chmod 2775 "$SHARED_DIR"
echo '$ ls -ld /srv/shared'
ls -ld "$SHARED_DIR"
echo '$ stat -c "владелец=%U группа=%G права=%a" /srv/shared'
stat -c 'владелец=%U группа=%G права=%a' "$SHARED_DIR"
echo

echo '$ sudo -u student2 bash -c "umask 002; echo ... > /srv/shared/student2.txt"'
runuser -u student2 -- bash -c "umask 002; printf 'Файл создан пользователем student2.\n' > '$SHARED_FILE'"
echo '$ ls -l /srv/shared/student2.txt'
ls -l "$SHARED_FILE"
echo '$ stat -c "владелец=%U группа=%G права=%a" /srv/shared/student2.txt'
stat -c 'владелец=%U группа=%G права=%a' "$SHARED_FILE"
echo

echo "$ sudo -u $MAIN_USER rm /srv/shared/student2.txt"
set +e
DELETE_OUTPUT="$(runuser -u "$MAIN_USER" -- rm -f "$SHARED_FILE" 2>&1)"
DELETE_STATUS=$?
set -e
printf '%s\n' "$DELETE_OUTPUT"
printf 'Код возврата rm: %d\n' "$DELETE_STATUS"

if (( DELETE_STATUS == 0 )); then
    DELETE_EXPLANATION="Основной пользователь смог удалить файл, потому что у него есть право записи в каталог /srv/shared (он входит в группу developers). Право удаления определяется каталогом, а не владельцем файла. После проверки файл создан повторно."
    runuser -u student2 -- bash -c "umask 002; printf 'Файл создан пользователем student2.\n' > '$SHARED_FILE'"
else
    DELETE_EXPLANATION="Основной пользователь не смог удалить файл: у него нет права записи в каталог /srv/shared. Для удаления файла нужны права на запись и переход в его каталоге; права на сам файл при удалении не проверяются."
fi
echo

echo '$ # Добавление двух alias и переменной окружения в ~/.bashrc'
touch "$BASHRC"
if ! grep -Fq '# BEGIN OS COURSE PR01' "$BASHRC"; then
    cat >> "$BASHRC" <<'EOF'

# BEGIN OS COURSE PR01
alias ll='ls -alF'
alias gs='git status --short'
export OS_COURSE='operating-systems'
# END OS COURSE PR01
EOF
fi
chown "$MAIN_USER:$MAIN_USER" "$BASHRC"

echo '$ # Проверка в новой интерактивной bash-сессии'
runuser -u "$MAIN_USER" -- bash -ic 'alias ll; alias gs; printf "OS_COURSE=%s\n" "$OS_COURSE"'
echo

echo '=== Автоматическая проверка ==='
[[ "$(stat -c '%U' "$SHARED_DIR")" == "root" ]]
[[ "$(stat -c '%G' "$SHARED_DIR")" == "developers" ]]
[[ "$(stat -c '%a' "$SHARED_DIR")" == "2775" ]]
id -nG student2 | grep -qw developers
[[ -f "$SHARED_FILE" ]]
grep -Fq "alias ll='ls -alF'" "$BASHRC"
grep -Fq "alias gs='git status --short'" "$BASHRC"
grep -Fq "export OS_COURSE='operating-systems'" "$BASHRC"
echo 'OK: пользователь, группа, права, общий файл, aliases и переменная настроены.'

exec 1>&3 2>&4

cat > "$SCRIPT_DIR/README.md" <<'EOF'
# Практическая работа № 1 — пользователи, группы и права Linux

**Вариант:** B  
**Среда:** Ubuntu 22.04+

## Цель

Настроить пользователей и группы, проверить права доступа к общему каталогу, объяснить удаление чужого файла и закрепить настройку Bash через `~/.bashrc`.

## Запуск

Из каталога `pr01`:

```bash
sudo bash run.sh
```

Скрипт создаёт пользователя `student2` и группу `developers`, настраивает `/srv/shared`, добавляет настройки в `~/.bashrc`, выполняет проверки и записывает реальный вывод ниже и в `results.txt`.

## Реальный вывод команд

```text
EOF
cat "$RESULTS" >> "$SCRIPT_DIR/README.md"
cat >> "$SCRIPT_DIR/README.md" <<EOF
\`\`\`

## Объяснение результатов

### Права и удаление файла

Каталог \`/srv/shared\` имеет владельца \`root\`, группу \`developers\` и права \`2775\`:

- \`2\` — setgid: новые файлы наследуют группу каталога;
- \`7\` для владельца — чтение, запись и переход;
- \`7\` для группы — члены \`developers\` могут создавать и удалять файлы;
- \`5\` для остальных — чтение содержимого каталога и переход в него, но без создания и удаления файлов.

$DELETE_EXPLANATION

### Чем su отличается от sudo

\`su\` запускает оболочку другого пользователя (по умолчанию root) и обычно требует пароль этого пользователя. \`sudo\` выполняет отдельную команду от имени root или другого пользователя, проверяет права вызывающего в \`/etc/sudoers\` и обычно спрашивает его собственный пароль. Действия через \`sudo\` журналируются, а полномочия можно выдать точечно.

### Почему в Ubuntu заблокирован вход под root

В Ubuntu у root по умолчанию нет действующего пароля для прямого входа. Это уменьшает риск постоянной работы с неограниченными правами и случайных разрушительных команд. Административные действия выполняются явно через \`sudo\`, поэтому система видит, какой пользователь запросил повышение привилегий.

### Настройка Bash

В \`~/.bashrc\` добавлены:

- \`ll='ls -alF'\` — подробный список файлов, включая скрытые;
- \`gs='git status --short'\` — короткий статус Git;
- \`OS_COURSE=operating-systems\` — переменная окружения.

Проверка выполнена в новой интерактивной Bash-сессии, поэтому подтверждает, что \`~/.bashrc\` действительно читается при запуске.

## Вывод

Пользователь \`student2\` добавлен в \`developers\`. Общий каталог настроен с минимально достаточными правами \`2775\`, без небезопасного \`chmod 777\`. Проверка удаления показала, что она зависит от прав на каталог. Два alias и переменная окружения работают в новой сессии.
EOF

chown "$MAIN_USER:$MAIN_USER" "$SCRIPT_DIR/README.md" "$RESULTS"
printf '\nГотово: %s/README.md заполнен реальными результатами.\n' "$SCRIPT_DIR"
