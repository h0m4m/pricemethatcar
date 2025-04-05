DOMAIN_RULES = {
    "www.vipcarrental.ae": {
        "url_prefixes": [
            "/sports-cars/",
            "/luxury-cars/",
            "/economy-cars/",
            "/our-cars/",
            "/cars/"
        ],
        "price_selector": ".price_from, .price-to, p.price_from, .price",
        "price_cleaning": lambda text: text.strip().split()[0] if text else "N/A"
    }
}