import requests
import time
from flask import Flask, jsonify

app = Flask(__name__)

# Shopify API Configuration
api_version = "2025-04"
store_name = "Test Aviator Nation"
access_token = "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"

# Target Settings (same as your script)
target_settings = {
    "types": {
        "hoodie": [
            {"metafield_key": "male_model_size", "size_display_name": "L"},
            {"metafield_key": "female_model_size", "size_display_name": "XS"}
        ],
        "sweatshirt": [
            {"metafield_key": "male_model_size", "size_display_name": "L"},
            {"metafield_key": "female_model_size", "size_display_name": "XS"}
        ],
        "men's sweatshorts": [{"metafield_key": "male_model_size", "size_display_name": "L"}],
        "men's board shorts": [{"metafield_key": "male_model_size", "size_display_name": "32"}],
        "sports bra": [{"metafield_key": "female_model_size", "size_display_name": "XS"}],
        "leggings": [{"metafield_key": "female_model_size", "size_display_name": "XS"}],
        "women's active shorts": [{"metafield_key": "female_model_size", "size_display_name": "XS"}],
        "women's board shorts": [{"metafield_key": "female_model_size", "size_display_name": "S"}],
        "women's jogger shorts": [{"metafield_key": "female_model_size", "size_display_name": "S"}],
        "women's shorts": [{"metafield_key": "female_model_size", "size_display_name": "S"}],
        "swim": [{"metafield_key": "female_model_size", "size_display_name": "XS"}],
        "polo": [{"metafield_key": "male_model_size", "size_display_name": "L"}],
        "men's tank": [{"metafield_key": "male_model_size", "size_display_name": "L"}],
        "women's tank": [{"metafield_key": "female_model_size", "size_display_name": "XS"}],
        "denim shorts": [{"metafield_key": "female_model_size", "size_display_name": "24"}],
        "women's jeans": [{"metafield_key": "female_model_size", "size_display_name": "24"}],
        "men's jeans": [{"metafield_key": "male_model_size", "size_display_name": "32"}],
        "women's outerwear": [{"metafield_key": "female_model_size", "size_display_name": "XS"}],
        "men's outerwear": [{"metafield_key": "male_model_size", "size_display_name": "L"}],
        "men's vest": [{"metafield_key": "male_model_size", "size_display_name": "L"}],
        "women's vest": [{"metafield_key": "female_model_size", "size_display_name": "XS"}]
    },
    "tags": {
        ("cropped crew sweatshirt",): [{"metafield_key": "female_model_size", "size_display_name": "XS"}],
        ("relaxed pullover hoodie", "cropped hoodie"): [{"metafield_key": "female_model_size", "size_display_name": "XS"}],
        ("jogger jean short",): [{"metafield_key": "female_model_size", "size_display_name": "XS"}]
    }
}

headers = {
    "X-Shopify-Access-Token": access_token,
    "Content-Type": "application/json"
}

def get_metaobject_id(display_name):
    url = f"https://{store_name}.myshopify.com/admin/api/{api_version}/graphql.json"
    query = """
    query($type: String!, $first: Int!) {
      metaobjects(type: $type, first: $first) {
        edges {
          node {
            id
            displayName
          }
        }
      }
    }
    """
    variables = {"type": "shopify--size", "first": 50}
    response = requests.post(url, headers=headers, json={"query": query, "variables": variables}, timeout=10)
    time.sleep(0.5)
    response.raise_for_status()
    for edge in response.json().get("data", {}).get("metaobjects", {}).get("edges", []):
        node = edge.get("node", {})
        if node.get("displayName") == display_name:
            return node.get("id")
    raise ValueError(f"No metaobject ID for '{display_name}'")

def get_products():
    products = []
    url = f"https://{store_name}.myshopify.com/admin/api/{api_version}/products.json?limit=250"
    while url:
        resp = requests.get(url, headers=headers, timeout=10)
        time.sleep(0.5)
        resp.raise_for_status()
        data = resp.json()
        products.extend(data.get("products", []))
        url = None
        link_header = resp.headers.get("Link")
        if link_header:
            for link in link_header.split(","):
                if 'rel="next"' in link:
                    url = link[link.find("<")+1:link.find(">")]
                    break
    return products

def get_metafield(product_id, key):
    url = f"https://{store_name}.myshopify.com/admin/api/{api_version}/products/{product_id}/metafields.json"
    resp = requests.get(url, headers=headers, timeout=10)
    time.sleep(0.5)
    resp.raise_for_status()
    for mf in resp.json().get("metafields", []):
        if mf["namespace"] == "custom" and mf["key"] == key:
            return mf
    return None

def update_or_create_metafield(product_id, namespace, key, value, value_type="metaobject_reference"):
    existing = get_metafield(product_id, key)
    body = {"metafield": {"namespace": namespace, "key": key, "value": value, "type": value_type}}
    if existing:
        url = f"https://{store_name}.myshopify.com/admin/api/{api_version}/metafields/{existing['id']}.json"
        response = requests.put(url, headers=headers, json=body, timeout=10)
    else:
        url = f"https://{store_name}.myshopify.com/admin/api/{api_version}/products/{product_id}/metafields.json"
        response = requests.post(url, headers=headers, json=body, timeout=10)
    time.sleep(0.5)
    if response.status_code in (200, 201):
        print(f"Set metafield '{key}' for product {product_id}")
    else:
        print(f"Error setting metafield '{key}' for product {product_id}: {response.status_code}")

def delete_metafield(metafield_id):
    url = f"https://{store_name}.myshopify.com/admin/api/{api_version}/metafields/{metafield_id}.json"
    resp = requests.delete(url, headers=headers, timeout=10)
    time.sleep(0.5)
    if resp.status_code == 200:
        print(f"Deleted metafield ID {metafield_id}")
    else:
        print(f"Failed to delete metafield ID {metafield_id}: {resp.status_code}")

def update_metafields():
    size_name_to_id = {}
    for section in ["types", "tags"]:
        for settings in target_settings[section].values():
            for s in settings:
                display = s["size_display_name"]
                if display not in size_name_to_id:
                    print(f"Fetching metaobject ID for size: {display}")
                    size_name_to_id[display] = get_metaobject_id(display)

    override_tags = {
        "cropped crew sweatshirt",
        "relaxed crew sweatshirt",
        "cropped hoodie",
        "relaxed pullover hoodie"
    }

    products = get_products()
    print(f"Fetched {len(products)} products")

    updated_count = 0

    for product in products:
        pid = product["id"]
        ptype = product.get("product_type", "").lower()
        ptags = set(tag.strip().lower() for tag in product.get("tags", "").split(",") if tag.strip())
        matched = False

        if ptags & override_tags:
            print(f"Skipping type-based update for {pid} due to override tags: {ptags & override_tags}")
        else:
            if ptype in target_settings["types"]:
                for setting in target_settings["types"][ptype]:
                    k = setting["metafield_key"]
                    display = setting["size_display_name"]
                    val = size_name_to_id[display]
                    existing = get_metafield(pid, k)
                    if existing and existing.get("value") == val:
                        print(f"Skipped {pid}: '{k}' already correct")
                        continue
                    print(f"Setting '{k}' = '{display}' on {pid} by type")
                    update_or_create_metafield(pid, "custom", k, val)
                    matched = True

        for tag_combo, settings in target_settings["tags"].items():
            if all(tag in ptags for tag in tag_combo):
                if "cropped crew sweatshirt" in tag_combo or "cropped hoodie" in tag_combo:
                    bad = get_metafield(pid, "male_model_size")
                    if bad:
                        print(f"Deleting incorrect 'male_model_size' on {pid}")
                        delete_metafield(bad["id"])
                for setting in settings:
                    k = setting["metafield_key"]
                    display = setting["size_display_name"]
                    val = size_name_to_id[display]
                    existing = get_metafield(pid, k)
                    if existing and existing.get("value") == val:
                        print(f"Skipped {pid}: '{k}' already correct (tag logic)")
                        continue
                    print(f"Setting '{k}' = '{display}' on {pid} by tags")
                    update_or_create_metafield(pid, "custom", k, val)
                    matched = True

        if matched:
            updated_count += 1
        else:
            print(f"Skipping {pid} — no applicable rules")

    print("Metafield updates complete.")
    return updated_count

@app.route('/')
def home():
    return "Shopify metafield update app is running. Go to /run-update to start."

@app.route('/run-update')
def run_update():
    try:
        count = update_metafields()
        return jsonify({"status": "success", "updated_products_count": count})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
