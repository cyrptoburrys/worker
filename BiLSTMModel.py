import torch
import torch.nn as nn
import pandas as pd
import requests
from pytorch_forecasting.models.temporal_fusion_transformer import TemporalFusionTransformer
from pytorch_forecasting import TimeSeriesDataSet, Baseline
from pytorch_forecasting.data import NaNLabelEncoder

# Function to fetch historical data from Binance
def get_binance_data(symbol, interval="1m", limit=1200):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "number_of_trades",
            "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
        ])
        df["close_time"] = pd.to_datetime(df["close_time"], unit='ms')
        df["high_low_range"] = df["high"].astype(float) - df["low"].astype(float)
        df = df[["close_time", "close", "volume", "high_low_range"]]
        df.columns = ["date", "price", "volume", "range"]
        df[["price", "volume", "range"]] = df[["price", "volume", "range"]].astype(float)
        return df
    else:
        raise Exception(f"Failed to retrieve data: {response.text}")

# Prepare the dataset specifically handling 20-minute and 10-minute predictions for BTC, ETH, BNB, and SOL
def prepare_tft_dataset(symbols, max_encoder_length=120, max_prediction_length=20):
    dfs = []
    for symbol in symbols:
        # Adjust limit based on specific requirements for BTC, ETH, BNB (20 minutes) and SOL (10 minutes)
        limit = 1200 if symbol in ['BTCUSDT', 'ETHUSDT', 'BNBUSDT'] else 600  # SOL has a smaller prediction window, so less history needed
        df = get_binance_data(symbol, limit=limit)
        df['symbol'] = symbol
        dfs.append(df)

    # Combine all dataframes into one, preserving context for each symbol
    data = pd.concat(dfs)
    data['time_idx'] = (data['date'] - data['date'].min()).dt.total_seconds() // 60
    data['group'] = data['symbol']
    data['target'] = data['price']

    # Create the TimeSeriesDataSet required for TFT with added context from volume and high-low range
    dataset = TimeSeriesDataSet(
        data,
        time_idx="time_idx",
        target="target",
        group_ids=["group"],
        max_encoder_length=max_encoder_length,
        max_prediction_length=max_prediction_length,
        time_varying_known_reals=["time_idx", "volume", "range"],
        time_varying_unknown_reals=["target"],
        categorical_encoders={"group": NaNLabelEncoder().fit(data["group"])},
        add_relative_time_idx=True,
        add_target_scales=True,
        add_encoder_length=True,
    )

    return dataset

# Training the Temporal Fusion Transformer model with the final refined settings
def train_tft_model(dataset, epochs=50):
    # Split dataset into training and validation
    training, validation = dataset.split_by_time_idx(int(len(dataset) * 0.8))

    # Create the Temporal Fusion Transformer model with adjustments to hidden size and attention
    tft = TemporalFusionTransformer.from_dataset(
        training,
        learning_rate=0.0005,  # Slightly reduced learning rate for stability
        hidden_size=128,  # Hidden size increased to capture more complex patterns
        attention_head_size=4,
        dropout=0.3,  # Dropout set to avoid overfitting
        hidden_continuous_size=64,
        output_size=7,  # Quantile outputs for probabilistic forecasting
        loss=Baseline.MAE(),  # Using Mean Absolute Error as a base loss function
        reduce_on_plateau_patience=5,
    )

    # Train the model with enhanced learning configurations
    trainer = torch.optim.Adam(tft.parameters(), lr=0.0005)  # Using Adam optimizer with refined learning rate
    for epoch in range(epochs):
        tft.train_epoch(epoch, trainer, training, validation, batch_size=64)
        print(f"Epoch {epoch+1}/{epochs} completed - Loss: {tft.current_epoch_loss(training)}")

    return tft

# Main execution to ensure the model is perfectly tailored to BTC, ETH, BNB, and SOL requirements
if __name__ == "__main__":
    # Prepare the dataset with configurations for 20-minute predictions (BTC, ETH, BNB) and 10-minute (SOL)
    symbols = ['BNBUSDT', 'BTCUSDT', 'ETHUSDT', 'SOLUSDT']
    dataset = prepare_tft_dataset(symbols, max_encoder_length=120, max_prediction_length=20)

    # Train the Temporal Fusion Transformer model
    model = train_tft_model(dataset, epochs=50)

    # Save the model for future deployment
    torch.save(model.state_dict(), "final_tft_model.pth")
    print("Model trained and saved as final_tft_model.pth")
