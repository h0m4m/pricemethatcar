import re

def normalize_car_name(make, model):
    """
    Convert a car make/model into a URL-friendly format:
    - Lowercase
    - Replace spaces and non-alphanumeric characters with a hyphen
    - Collapse multiple hyphens
    - Remove leading/trailing hyphens

    :param make: Car make (e.g., 'BMW')
    :param model: Car model (e.g., 'X5')
    :return: A normalized, hyphenated string (e.g., 'bmw-x5')
    :complexity: O(m), where m is the combined length of make and model
    """
    combined = f"{make}-{model}" if make else model
    combined = combined.lower()

    # Replace non-alphanumeric chars with hyphen
    slug = re.sub(r'[^a-z0-9]+', '-', combined)

    # Strip leading/trailing hyphens
    slug = slug.strip('-')

    return slug

# Example
print(normalize_car_name("Mercedes", "G Class"))  # Output: mercedes-g-class
print(normalize_car_name("Lamborghini", "Huracan Evo RWD Spyder"))  # lamborghini-huracan-evo-rwd-spyder