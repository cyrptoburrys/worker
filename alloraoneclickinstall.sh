#!/bin/bash

# One-Click Installation Script for Allora

if [ "$(id -u)" != "0" ]; then
    echo "This script must be run as root. Use 'sudo ./install_allora.sh'"
    exit 1
fi

apt-get update && apt-get upgrade -y
apt-get install -y curl wget git nano jq

# Install Docker
echo "Installing Docker..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io
docker version

# Install Docker-Compose
echo "Installing Docker Compose..."
VER=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep tag_name | cut -d '"' -f 4)
curl -L "https://github.com/docker/compose/releases/download/$VER/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
docker-compose --version

# Add user to Docker group
sudo groupadd docker
sudo usermod -aG docker $USER

# Clean up old Docker containers
docker compose down -v
docker container prune -f
cd $HOME && rm -rf allora-huggingface-walkthrough

# Clone Allora repository
echo "Cloning Allora repository..."
git clone https://github.com/allora-network/allora-huggingface-walkthrough
cd allora-huggingface-walkthrough

# Setup workers for ETH, BTC, BNB, SOL only
cat > config.json <<EOL
{
    "wallet": {
        "addressKeyName": "test",
        "addressRestoreMnemonic": "<your mnemonic phrase>",
        "alloraHomeDir": "/root/.allorad",
        "gas": "1000000",
        "gasAdjustment": 1.5,
        "nodeRpc": "https://allora-rpc.testnet.allora.network",
        "maxRetries": 1,
        "delay": 1,
        "submitTx": true
    },
    "worker": [
        {
            "topicId": 1,
            "inferenceEntrypointName": "api-worker-reputer",
            "loopSeconds": 4,
            "parameters": {
                "InferenceEndpoint": "http://inference:8000/inference/{Token}",
                "Token": "ETH"
            }
        },
        {
            "topicId": 3,
            "inferenceEntrypointName": "api-worker-reputer",
            "loopSeconds": 6,
            "parameters": {
                "InferenceEndpoint": "http://inference:8000/inference/{Token}",
                "Token": "BTC"
            }
        },
        {
            "topicId": 5,
            "inferenceEntrypointName": "api-worker-reputer",
            "loopSeconds": 8,
            "parameters": {
                "InferenceEndpoint": "http://inference:8000/inference/{Token}",
                "Token": "SOL"
            }
        },
        {
            "topicId": 7,
            "inferenceEntrypointName": "api-worker-reputer",
            "loopSeconds": 2,
            "parameters": {
                "InferenceEndpoint": "http://inference:8000/inference/{Token}",
                "Token": "BNB"
            }
        }
    ]
}
EOL

# Prompt user for addressKeyName and addressRestoreMnemonic
read -p "Enter your addressKeyName: " addressKeyName
read -p "Enter your addressRestoreMnemonic: " addressRestoreMnemonic

# Update the config.json with user-provided values
jq --arg keyName "$addressKeyName" --arg mnemonic "$addressRestoreMnemonic" \
   '.wallet.addressKeyName = $keyName | .wallet.addressRestoreMnemonic = $mnemonic' config.json > temp.json && mv temp.json config.json

# Export and run the initialization script
chmod +x init.config
./init.config

# Download and run the upgrade script
echo "Downloading and running the upgrade script..."
wget https://raw.githubusercontent.com/cyrptoburrys/worker/main/upgrade-model.sh
chmod +x upgrade-model.sh
./upgrade-model.sh

echo "Installation complete! You can check your wallet here: http://worker-tx.nodium.xyz/"
