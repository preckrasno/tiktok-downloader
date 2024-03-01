#!/bin/bash

r_flag=''

print_usage() {
    printf "Usage: ..."
}

while getopts "r" flag; do
    case "${flag}" in
    r) r_flag='true' ;;
    *)
        print_usage
        exit 1
        ;;
    esac
done

cd "$(dirname "$0")"

# check if telegram API_TOKEN is set in .env
if ! grep -w "API_TOKEN" .env >/dev/null; then
    echo "API_TOKEN not set in .env"
    exit 1
fi

if ps -A | grep "tiktok-download" | grep -v grep | grep -v "start-tiktok-downloader.sh" >/dev/null; then
    echo "Running"
else
    echo "Stopped"
    cd "$(dirname "$0")"
    if [ -e dist/tiktok-downloader ]; then
        echo "binary available"
    else
        pip install virtualenv
        echo "virtualenv installed"
        python3 -m venv venv
        echo "venv created"
        . venv/bin/activate
        echo "venv activated"
        pip install -r requirements.txt
        echo "modules installed"
        pyinstaller main.py --onefile --name tiktok-downloader
        echo "binary compiled"
        chmod a+x dist/tiktok-downloader
        echo "binary granted execute rights"
    fi
    dist/tiktok-downloader &
    echo "binary started"
fi

if crontab -l | grep start-tiktok-downloader.sh >/dev/null; then
    echo "Cronjob exists"
else
    echo "Cronjob does not exist"
    crontab -l >mycron
    SCRIPT=$(readlink -f "$0")
    echo "*/15 * * * * $SCRIPT" >>mycron
    echo "@reboot $SCRIPT" >>mycron
    crontab mycron
    rm mycron
fi

if [ "$r_flag" = 'true' ]; then
    killall tiktok-downloader
    echo "binary stopped"
    rm -rf dist
    rm -rf build
    rm -rf venv
    echo "removed old files"
    python3 -m venv venv
    echo "venv created"
    . venv/bin/activate
    echo "venv activated"
    pip install -r requirements.txt
    echo "modules installed"
    pyinstaller main.py --onefile --name tiktok-downloader
    echo "binary compiled"
    chmod a+x dist/tiktok-downloader
    echo "binary granted execute rights"
fi
