DOMAIN_RULES = {
    "www.rotanastar.ae": {
        "url_prefixes": ["/car/"],
    "price_selector": "p.price span.woocommerce-Price-amount.amount bdi",
    "price_cleaning": lambda x: x.strip().split()[0].replace(',', '')
    },
    "phantomrentcar.com": {
        "url_prefixes": ["/car/"],
        "price_selector": "div.details-text .col-6:nth-of-type(1) span.brown.bold",
        "price_cleaning": lambda x: x.strip().replace(',', '')
    },
    "mkrentacar.com": {
        "url_prefixes": [
            "/cars/rent-suv-cars/",
            "/cars/rent-sports-cars/",
            "/cars/rent-luxury-cars/",
            "/cars/rent-exotic-cars/",
            "/cars/rent-convertible-cars/",
            "/cars/rent-economy-cars/"
        ],
        "price_selector": "div.price h5",
        "price_cleaning": lambda x: x.strip().split()[0].replace(',', '')
    },
    "superiorrental.ae": {
        "url_prefixes": ["/cars/"],
        "price_selector": "div.rounded-xl h3.font-semibold",
        "price_cleaning": lambda x: ''.join(filter(str.isdigit, x))
    },
    # "octane.rent": {
    #     "url_prefixes": [
    #         "/suv-cars/",
    #         "/sports-cars/",
    #         "/luxury-cars/",
    #         "/cars/",
    #         "/convertible-cars/",
    #         "/sedan/"
    #     ],
    # "price_selector": "div[data-id='car_price-1'] span.wpcs_price",
    # "price_cleaning": lambda x: x.strip().replace(',', '')
    # },
    "www.uptowndxb.com": {
        "url_prefixes": [
            "/Rental/sport-cars/",
            "/Rental/all-cars/",
            "/Rental/luxury-cars/",
            "/Rental/suv/"
        ],
        "price_selector": "p.price span.woocommerce-Price-amount bdi",
        "price_cleaning": lambda x: x.strip().split()[0]
    },
    "www.bevip.ae": {
        "url_prefixes": [
            "/luxury-car/",
        ],
        "price_selector": "span.price span.price",
        "price_cleaning": lambda x: x.strip().split()[0]
    },
    "xcarrental.com": {
        "url_prefixes": [
            "/car/",
            "/sports/",
            "/luxury/",
            "/suv/",
            "/4x4/",
            "/convertible/",
            "/7-seater/",
            "/hatchback/",
            "/economic/"
        ],
        "price_selector": "span.single_car_price",
        "price_cleaning": lambda x: x.strip().split()[0]
    },
    "ferrorental.com": {
        "url_prefixes": [
            "/rent/convertible/",
            "/rent/coupe/",
            "/rent/premium/",
            "/rent/suvs/",
            "/rent/sport/"
        ],
        "price_selector": "div.product-page_price",
        "price_cleaning": lambda x: x.strip().split()[1] if len(x.strip().split()) > 1 else x.strip().split()[0]
    },
    "mtn-rentacar.com": {
        "url_prefixes": [
            "/product/",
        ],
        "price_selector": "div.w-hwrapper.valign_baseline.wrap.align_center p.product_field.price ins span.woocommerce-Price-amount.amount bdi",
        "price_cleaning": lambda x: x.strip().split()[0].replace(',', '')
    },
    "www.selyarentacar.com": {
        "url_prefixes": [
            "/",
        ],
        "price_selector": "div.hRdzm4 div.cGWabE:first-child div.comp-l6q464402 h3.font_3 span.wixui-rich-text__text span.wixui-rich-text__text",
        "price_cleaning": lambda x: x.strip().split()[0].replace(',', '')
    },
    "firstsupercarrental.com": {
        "url_prefixes": ["/rent-cars/"],
        "price_selector": "div[data-id='25ce782'] .elementor-heading-title",
        "price_cleaning": lambda x: x.strip().split()[0]
    }
}