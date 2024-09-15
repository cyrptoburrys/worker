import torch
import pandas as pd
import requests
from flask import Flask, Response, json
import logging
from datetime import datetime
from pytorch_forecasting.models.temporal_fusion_transformer import TemporalFusionTransformer
from pytorch_forecasting import TimeSeriesDataSet
from pytorch_forecasting.data import NaNLabelEncoder
from torch.utils.data import DataLoader

app = Flask(__name__)

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("main")

# Load the saved TFT model
model = TemporalFusionTransformer.load_from_checkpoint("final_tft_model.pth")
model.eval()

# Function to fetch historical data from Binance
def get_binance_url(symbol="ETHUSDT", interval="1m", limit=120):
    return f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"

@app.route("/inference/<string:token>")
def get_inference(token):
    if model is None:
        return Response(json.dumps({"error": "Model is not available"}), status=500, mimetype='application/json')

    symbol_map = {
        'ETH': 'ETHUSDT',
        'BTC': 'BTCUSDT',
        'BNB': 'BNBUSDT',
        'SOL': 'SOLUSDT'
    }

    token = token.upper()
    if token in symbol_map:
        symbol = symbol_map[token]
    else:
        return Response(json.dumps({"error": "Unsupported token"}), status=400, mimetype='application/json')

    url = get_binance_url(symbol=symbol)
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
        df['symbol'] = symbol

        # Prepare data for prediction
        data = df.copy()
        data['time_idx'] = ((data['date'] - data['date'].min()).dt.total_seconds() // 60).astype(int)
        data['group'] = data['symbol']
        data['target'] = data['price']

        # Ensure that the index is unique by resetting and reindexing
        data = data.drop_duplicates(subset=['time_idx', 'group'])
        data = data.sort_values(['group', 'time_idx']).reset_index(drop=True)

        # Use same parameters as during training
        max_encoder_length = 120
        max_prediction_length = 20

        # Create TimeSeriesDataSet
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

        # Select the last sequence for prediction
        predict_data = dataset.from_dataset(dataset, data.iloc[[-max_encoder_length]])

        # Create DataLoader
        predict_dataloader = DataLoader(predict_data, batch_size=1, num_workers=0)

        # Get prediction
        with torch.no_grad():
            raw_predictions, x = model.predict(predict_dataloader, mode="raw", return_x=True)
            y_pred = raw_predictions['prediction'][0][0][0].item()  # Get the first prediction

        predicted_price = round(y_pred, 2)
        logger.info(f"Prediction: {predicted_price}")
        return Response(json.dumps({"prediction": predicted_price}), status=200, mimetype='application/json')
    else:
        return Response(json.dumps({"error": "Failed to retrieve data from Binance API", "details": response.text}), 
                        status=response.status_code, 
                        mimetype='application/json')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
