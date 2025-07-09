from flask import Flask
import os
from dotenv import load_dotenv
from metafields_manager import run_metafield_updates

load_dotenv()

app = Flask(__name__)

@app.route("/")
def home():
    return "Shopify Metafield Manager is running."

@app.route("/run-update", methods=["GET"])
def trigger_update():
    run_metafield_updates()
    return "Metafield updates complete!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

