"""Static keyword lists and maps for rule-based incident enrichment."""

NOISE_KEYWORDS = [
    'ugh', 'so annoying', "can't believe", 'why is everyone',
    'terrible', 'worst', 'hate this', 'so frustrated',
    'unbelievable', 'ridiculous', 'complain', 'rant',
]

DIGITAL_KEYWORDS = [
    'phishing', 'scam', 'otp', 'fraud', 'suspicious email',
    'breach', 'hack', 'malware', 'virus', 'password',
    'bank details', 'credit card', 'identity theft',
    'suspicious link', 'fake website', 'ransomware',
]

PHYSICAL_KEYWORDS = [
    'theft', 'accident', 'fire', 'break-in', 'suspicious person',
    'robbery', 'assault', 'vandalism', 'burglary', 'shooting',
    'fight', 'weapon', 'injury', 'ambulance', 'police',
    'missing', 'flood', 'explosion', 'gas leak',
]

WEATHER_KEYWORDS = [
    'storm', 'flood', 'earthquake', 'lightning', 'tornado',
    'heavy rain', 'cyclone', 'tsunami', 'landslide', 'drought',
    'heatwave', 'snowfall', 'hail', 'thunder',
]

SEVERITY_MAP = {
    'physical': 3,
    'digital': 3,
    'weather': 2,
}

ACTION_MAP = {
    'physical': (
        "Stay alert and avoid the area if possible. "
        "Report to local authorities if the situation persists."
    ),
    'digital': (
        "Do not click any suspicious links. "
        "Change your passwords and enable two-factor authentication immediately."
    ),
    'weather': (
        "Stay indoors and follow local weather advisories. "
        "Keep emergency contacts handy."
    ),
}
