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
    echo -e "${LIGHT_BLUE}Cloning & Replacing old files...${RESET}"
    rm -rf app.py
    rm -rf EnhancedPricePredictor.py
    rm -rf final_tft_model.pth
    rm -rf requirements.txt
    wget -q https://raw.githubusercontent.com/cyrptoburrys/worker/main/app.py -O /root/allora-huggingface-walkthrough/app.py
    wget -q https://raw.githubusercontent.com/cyrptoburrys/worker/main/EnhancedPricePredictor.py -O /root/allora-huggingface-walkthrough/EnhancedPricePredictor.py
    wget -q https://github.com/cyrptoburrys/worker/main/final_tft_model.pth -O /root/allora-huggingface-walkthrough/final_tft_model.pth
    wget -q https://github.com/cyrptoburrys/worker/main/requirements.txt -O /root/allora-huggingface-walkthrough/requirements.txt
    wait
    
    echo -e "${LIGHT_BLUE}Rebuilding and running the model...${RESET}"
    cd /root/allora-huggingface-walkthrough/
    docker compose up --build -d
    docker compose logs -f
else
    echo -e "${BRIGHT_GREEN}Operation Canceled.${RESET}"
fi

echo -e "${MAGENTA}==============0xTnpxSGT | Allora===============${RESET}"
