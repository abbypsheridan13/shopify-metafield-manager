import os
import time
import random
import requests

# Configuration
api_version = os.getenv("API_VERSION")
store_name = os.getenv("STORE_NAME")
access_token = os.getenv("ACCESS_TOKEN")

# Shopify headers
headers = {
    "X-Shopify-Access-Token": access_token,
    "Content-Type": "application/json"
}
graphql_headers = {**headers, "Accept": "application/json"}

# Retry logic
def safe_request(method, url, **kwargs):
    max_retries = 5
    for retry in range(max_retries):
        response = method(url, **kwargs)
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", "1"))
            print(f"[429] Rate limited. Waiting {retry_after}s...")
            time.sleep(retry_after)
        elif response.status_code >= 500:
            delay = 1.5 ** retry + random.uniform(0, 1)
            print(f"[{response.status_code}] Server error. Retrying in {delay:.2f}s...")
            time.sleep(delay)
        else:
            return response
    raise Exception("Too many retries — giving up.")

target_settings = {
    "types": {
        # "hoodie": [
        #     {"metafield_key": "male_model_size", "size_display_name": "L"},
        #     {"metafield_key": "female_model_size", "size_display_name": "XS"}
        # ],
        # "sweatshirt": [
        #     {"metafield_key": "male_model_size", "size_display_name": "L"},
        #     {"metafield_key": "female_model_size", "size_display_name": "XS"}
        # ],
        "destination hoodie": [
            {"metafield_key": "male_model_size", "size_display_name": "L"},
            {"metafield_key": "female_model_size", "size_display_name": "XS"}
            ],
        "destination sweatshirt": [
            {"metafield_key": "male_model_size", "size_display_name": "L"},
            {"metafield_key": "female_model_size", "size_display_name": "XS"}
        ],
        "destination tees": [
            {"metafield_key": "male_model_size", "size_display_name": "L"},
            {"metafield_key": "female_model_size", "size_display_name": "XS"}
        ],
        "destination men's sweatpants": [{"metafield_key": "male_model_size", "size_display_name": "L"}],
        "destination women's sweatpants": [{"metafield_key": "female_model_size", "size_display_name": "XS"}],
        "women's sweatpants": [{"metafield_key": "female_model_size", "size_display_name": "S"}],
        "men's sweatpants": [{"metafield_key": "male_model_size", "size_display_name": "M"}],
        "destination BF tees": [{"metafield_key": "female_model_size", "size_display_name": "S"}],
        "boyfriend tee": [{"metafield_key": "female_model_size", "size_display_name": "S"}],
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
    response = safe_request(
        requests.post, url,
        headers=graphql_headers,
        json={"query": query, "variables": variables},
        timeout=10
    )
    for edge in response.json().get("data", {}).get("metaobjects", {}).get("edges", []):
        node = edge.get("node", {})
        if node.get("displayName") == display_name:
            return node.get("id")
    raise ValueError(f"No metaobject ID for '{display_name}'")

def get_products():
    products = []
    url = f"https://{store_name}.myshopify.com/admin/api/{api_version}/products.json?limit=250"
    while url:
        resp = safe_request(requests.get, url, headers=headers, timeout=10)
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

def get_all_metafields(product_id):
    url = f"https://{store_name}.myshopify.com/admin/api/{api_version}/products/{product_id}/metafields.json"
    resp = safe_request(requests.get, url, headers=headers, timeout=10)
    return resp.json().get("metafields", [])

def update_or_create_metafield(product_id, metafields, namespace, key, value, value_type="metaobject_reference"):
    existing = next((mf for mf in metafields if mf["namespace"] == namespace and mf["key"] == key), None)
    body = {"metafield": {"namespace": namespace, "key": key, "value": value, "type": value_type}}

    if existing:
        url = f"https://{store_name}.myshopify.com/admin/api/{api_version}/metafields/{existing['id']}.json"
        response = safe_request(requests.put, url, headers=headers, json=body, timeout=10)
    else:
        url = f"https://{store_name}.myshopify.com/admin/api/{api_version}/products/{product_id}/metafields.json"
        response = safe_request(requests.post, url, headers=headers, json=body, timeout=10)

    if response.status_code not in (200, 201):
        print(f"Error setting metafield '{key}' for product {product_id}: {response.status_code}")

def delete_metafield(metafield_id):
    url = f"https://{store_name}.myshopify.com/admin/api/{api_version}/metafields/{metafield_id}.json"
    resp = safe_request(requests.delete, url, headers=headers, timeout=10)
    if resp.status_code != 200:
        print(f"Failed to delete metafield ID {metafield_id}: {resp.status_code}")

def run_metafield_updates():
    print("target_settings type:", type(target_settings))
    print("target_settings['types'] type:", type(target_settings.get("types")))
    print("target_settings['tags'] type:", type(target_settings.get("tags")))

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

    for product in products:
        pid = product["id"]
        ptype = product.get("product_type", "").lower()
        ptags = set(tag.strip().lower() for tag in product.get("tags", "").split(",") if tag.strip())
        metafields = get_all_metafields(pid)
        matched = False

        # Type-based logic
        if ptags & override_tags:
            print(f"Skipping type-based update for {pid} due to override tags: {ptags & override_tags}")
        elif ptype in target_settings["types"]:
            for setting in target_settings["types"][ptype]:
                k = setting["metafield_key"]
                display = setting["size_display_name"]
                val = size_name_to_id[display]
                existing = next((mf for mf in metafields if mf["namespace"] == "custom" and mf["key"] == k), None)
                if existing and existing.get("value") == val:
                    print(f"Product {pid}: '{k}' already updated")
                    continue
                update_or_create_metafield(pid, metafields, "custom", k, val)
                matched = True

        # Tag-based logic
        for tag_combo, settings in target_settings["tags"].items():
            if all(tag in ptags for tag in tag_combo):
                if "cropped crew sweatshirt" in tag_combo or "cropped hoodie" in tag_combo:
                    bad = next((mf for mf in metafields if mf["namespace"] == "custom" and mf["key"] == "male_model_size"), None)
                    if bad:
                        delete_metafield(bad["id"])
                for setting in settings:
                    k = setting["metafield_key"]
                    display = setting["size_display_name"]
                    val = size_name_to_id[display]
                    existing = next((mf for mf in metafields if mf["namespace"] == "custom" and mf["key"] == k), None)
                    if existing and existing.get("value") == val:
                        print(f"Product {pid}: '{k}' already updated")
                        continue
                    update_or_create_metafield(pid, metafields, "custom", k, val)
                    matched = True

        if not matched:
            print(f"Skipping {pid} — no applicable rules")
    print("Metafield updates completed.")