#!/bin/bash

BOLD="\033[1m"
UNDERLINE="\033[4m"
LIGHT_BLUE="\033[1;34m"
BRIGHT_GREEN="\033[1;32m"
MAGENTA="\033[1;35m"
RESET="\033[0m"

echo -e "${LIGHT_BLUE}Upgrade Your Allora Model(TYPE:Y):${RESET}"
read -p "" installdep
echo

if [[ "$installdep" =~ ^[Yy]$ ]]; then
    echo -e "${LIGHT_BLUE}Clone & Replace old file :${RESET}"
    rm -rf app.py
    rm -rf requirements.txt
    wget -q https://raw.githubusercontent.com/your_repo/app.py -O /root/allora-huggingface-walkthrough/app.py
    wget -q https://raw.githubusercontent.com/your_repo/requirements.txt -O /root/allora-huggingface-walkthrough/requirements.txt
    wget -q https://github.com/your_repo/final_tft_model.pth -O /root/allora-huggingface-walkthrough/final_tft_model.pth
    wait
    
    echo -e "${LIGHT_BLUE}Rebuild and run a model :${RESET}"
    cd /root/allora-huggingface-walkthrough/
    docker compose up --build -d
    docker compose logs -f
else
    echo -e "${BRIGHT_GREEN}Operation Canceled :${RESET}"
fi

echo
echo -e "${MAGENTA}==============0xTnpxSGT | Allora===============${RESET}"
