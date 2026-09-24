#!/usr/bin/env bash
set -e  

if [ "$(uname -s)" != "Linux" ]; then
    echo "Этот скрипт предназначен только для Linux." >&2
    exit 1
fi

if [ "$(id -u)" -eq 0 ]; then
    SUDO=""
else
    if command -v sudo >/dev/null 2>&1; then
        SUDO="sudo"
    else
        echo "Нужны права root, но sudo не найден. Запустите скрипт от root." >&2
        exit 1
    fi
fi

echo ">>> Определяем пакетный менеджер..."

install_base() {
    if command -v apt-get >/dev/null 2>&1; then
        echo ">>> Найден apt (Debian/Ubuntu/Mint/Pop!_OS/...) "
        $SUDO apt-get update -y
        $SUDO apt-get install -y python3-pip

    elif command -v dnf >/dev/null 2>&1; then
        echo ">>> Найден dnf (Fedora/RHEL/CentOS Stream)"
        $SUDO dnf install -y python3-pip

    elif command -v yum >/dev/null 2>&1; then
        echo ">>> Найден yum (CentOS/RHEL старые)"
        $SUDO yum install -y python3-pip

    elif command -v pacman >/dev/null 2>&1; then
        echo ">>> Найден pacman (Arch/Manjaro/EndeavourOS)"
        $SUDO pacman -Sy --noconfirm python-pip

    elif command -v zypper >/dev/null 2>&1; then
        echo ">>> Найден zypper (openSUSE/SLES)"
        $SUDO zypper --non-interactive install python3-pip

    elif command -v apk >/dev/null 2>&1; then
        echo ">>> Найден apk (Alpine)"
        $SUDO apk add --no-cache py3-pip

    elif command -v emerge >/dev/null 2>&1; then
        echo ">>> Найден emerge (Gentoo)"
        $SUDO emerge --ask=n dev-python/pip

    elif command -v xbps-install >/dev/null 2>&1; then
        echo ">>> Найден xbps (Void Linux)"
        $SUDO xbps-install -Sy python3-pip

    elif command -v eopkg >/dev/null 2>&1; then
        echo ">>> Найден eopkg (Solus)"
        $SUDO eopkg install -y python3-pip

    else
        echo "Не удалось определить пакетный менеджер." >&2
        echo "Установите pip вручную, затем запустите:" >&2
        echo "    pip3 install colorama" >&2
        exit 1
    fi
}

NEED_BASE=0
command -v pip3    >/dev/null 2>&1 || NEED_BASE=1

if [ "$NEED_BASE" -eq 1 ]; then
    install_base
else
    echo ">>> pip3 уже установлен, пропускаем."
fi

echo ">>> Устанавливаем colorama..."

if pip3 install --user colorama 2>/dev/null; then
    echo ">>> colorama установлена в пользовательское окружение (--user)."
elif pip3 install --user --break-system-packages colorama; then
    echo ">>> colorama установлена с флагом --break-system-packages."
else
    echo ">>> Не удалось установить через pip. Пробуем пакет из репозитория..."
    if command -v apt-get >/dev/null 2>&1; then
        $SUDO apt-get install -y python3-colorama
    elif command -v dnf >/dev/null 2>&1; then
        $SUDO dnf install -y python3-colorama
    elif command -v pacman >/dev/null 2>&1; then
        $SUDO pacman -S --noconfirm python-colorama
    elif command -v zypper >/dev/null 2>&1; then
        $SUDO zypper --non-interactive install python3-colorama
    elif command -v apk >/dev/null 2>&1; then
        $SUDO apk add --no-cache py3-colorama
    else
        echo "Установите colorama вручную." >&2
        exit 1
    fi
fi

echo ">>> Проверяем установку..."
python3 -c "import colorama; print('>>> colorama-' + colorama.Fore.YELLOW + colorama.__version__ + colorama.Fore.GREEN + ' успешно установлена' + colorama.Fore.WHITE)"

echo ">>> Готово."