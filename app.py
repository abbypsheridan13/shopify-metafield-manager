from flask import Flask, render_template, request, redirect
import os
from dotenv import load_dotenv
import requests
from metafields_manager import run_metafield_updates

load_dotenv()

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/run-update", methods=["GET"])
def trigger_update():
    run_metafield_updates()
    return "Metafield updates complete!"

SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY")
SHOPIFY_API_SECRET = os.getenv("SHOPIFY_API_SECRET")
SCOPES = os.getenv("SCOPES", "read_products,write_products")
REDIRECT_URI = os.getenv("REDIRECT_URI")

@app.route("/auth")
def auth():
    shop = request.args.get("shop")
    if not shop:
        return "Missing shop param", 400

    redirect_url = f"https://{shop}/admin/oauth/authorize?client_id={SHOPIFY_API_KEY}&scope={SCOPES}&redirect_uri={REDIRECT_URI}"
    return redirect(redirect_url)

@app.route("/auth/callback")
def auth_callback():
    shop = request.args.get("shop")
    code = request.args.get("code")

    if not shop or not code:
        return "Missing params", 400

    token_url = f"https://{shop}/admin/oauth/access_token"
    payload = {
        "client_id": SHOPIFY_API_KEY,
        "client_secret": SHOPIFY_API_SECRET,
        "code": code
    }

    res = requests.post(token_url, json=payload)
    res_data = res.json()

    access_token = res_data.get("access_token")
    if not access_token:
        return "Failed to get access token", 400

    print(f"Access token for {shop}: {access_token}")

    return f"App installed successfully for {shop}!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
