# Allora - Temporal Fusion Transformer (TFT) Model

This guide provides instructions to set up a price prediction node using the Temporal Fusion Transformer (TFT) model. This setup predicts prices for ETH, BTC, BNB, and SOL using a custom-trained model.
![363396006-fb524b13-49c1-4c8f-90d9-50a9be69130c](https://github.com/user-attachments/assets/cb5c772b-fe77-4366-8616-c6cd76ea2b41)

## How to Install?

### OPTION 1: One-Click Installation Script

**Run Command:**

```bash
cd $HOME
rm -rf alloraoneclickinstall.sh
wget https://raw.githubusercontent.com/cyrptoburrys/worker/main/alloraoneclickinstall.sh && chmod +x alloraoneclickinstall.sh && ./alloraoneclickinstall.sh
```
-
OPTION 2: Manual Installation Guide
Prerequisites
Before you start, ensure you have Docker and Docker Compose installed.
```bash
# Install Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io
docker version

# Install Docker-Compose
VER=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep tag_name | cut -d '"' -f 4)
curl -L "https://github.com/docker/compose/releases/download/$VER/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
docker-compose --version

# Docker Permission to user
sudo groupadd docker
sudo usermod -aG docker $USER
```

Clean Old Docker
```bash
docker compose down -v
docker container prune
cd $HOME && rm -rf allora-huggingface-walkthrough
```

Deployment - Read Carefully!
Step 1-1:

```bash
git clone https://github.com/allora-network/allora-huggingface-walkthrough
cd allora-huggingface-walkthrough
```
Step 2:

```bash
cp config.example.json config.json
nano config.json
```

Edit addressKeyName & addressRestoreMnemonic inside config.json:

```bash
{
    "wallet": {
        "addressKeyName": "test",
        "addressRestoreMnemonic": "<your mnemonic phrase>",
        "alloraHomeDir": "/root/.allorad",
        "gas": "1000000",
        "gasAdjustment": 1.0,
        "nodeRpc": "https://allora-rpc.testnet.allora.network/",
        "maxRetries": 1,
        "delay": 1,
        "submitTx": false
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
```
Step 3: Export

```bash
chmod +x init.config
./init.config
```

Step 4: Run Script
```bash
wget https://raw.githubusercontent.com/cyrptoburrys/worker/main/upgrade-model.sh && chmod +x upgrade-model.sh && ./upgrade-model.sh
```
Check your wallet here: http://worker-tx.nodium.xyz/
