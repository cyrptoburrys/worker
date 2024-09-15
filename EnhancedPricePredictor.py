import torch
import pandas as pd
from pytorch_forecasting.models.temporal_fusion_transformer import TemporalFusionTransformer
from pytorch_forecasting import TimeSeriesDataSet, QuantileLoss
from pytorch_forecasting.data import NaNLabelEncoder
from pytorch_lightning import Trainer
from pytorch_lightning.loggers import CSVLogger
from torch.utils.data import DataLoader
import requests
import numpy as np

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

# Prepare the dataset for the Temporal Fusion Transformer
def prepare_tft_dataset(symbols, max_encoder_length=120, max_prediction_length=20):
    dfs = []
    for symbol in symbols:
        limit = 1200 if symbol in ['BTCUSDT', 'ETHUSDT', 'BNBUSDT'] else 600
        df = get_binance_data(symbol, limit=limit)
        df['symbol'] = symbol
        dfs.append(df)

    data = pd.concat(dfs).reset_index(drop=True)
    data['time_idx'] = ((data['date'] - data['date'].min()).dt.total_seconds() // 60).astype(int)
    data['group'] = data['symbol']
    data['target'] = data['price']

    # Ensure that the index is unique by resetting and reindexing
    data = data.drop_duplicates(subset=['time_idx', 'group'])
    data = data.sort_values(['group', 'time_idx']).reset_index(drop=True)

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

    return dataset, data

# Training the Temporal Fusion Transformer model
def train_tft_model(dataset, data):
    # Split dataset into training and validation dataloaders
    train_dataloader = dataset.to_dataloader(train=True, batch_size=64, num_workers=0)
    val_dataloader = dataset.to_dataloader(train=False, batch_size=64, num_workers=0)

    # Create the Temporal Fusion Transformer model
    tft = TemporalFusionTransformer.from_dataset(
        dataset,
        learning_rate=0.0005,
        hidden_size=128,
        attention_head_size=4,
        dropout=0.3,
        hidden_continuous_size=64,
        output_size=7,
        loss=QuantileLoss(),
        reduce_on_plateau_patience=5,
    )

    # Define the Trainer with logger
    logger = CSVLogger("logs", name="tft_model")
    trainer = Trainer(
        max_epochs=50,
        logger=logger,
        check_val_every_n_epoch=1,  # Ensure validation runs at least every epoch
        checkpoint_callback=False,  # Disable checkpointing for PyTorch Lightning <=1.4.x
        log_every_n_steps=10,  # Lower the logging interval for more frequent updates
    )

    # Fit the model using the defined dataloaders
    trainer.fit(tft, train_dataloader=train_dataloader, val_dataloaders=val_dataloader)

    # Save the trained model checkpoint
    trainer.save_checkpoint("final_tft_model.pth")
    print("Model trained and saved as final_tft_model.pth")

# Main execution
if __name__ == "__main__":
    symbols = ['BNBUSDT', 'BTCUSDT', 'ETHUSDT', 'SOLUSDT']
    dataset, data = prepare_tft_dataset(symbols, max_encoder_length=120, max_prediction_length=20)
    train_tft_model(dataset, data)

