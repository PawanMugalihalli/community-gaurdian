class FallbackService:

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

    @staticmethod
    def analyze(incidents: list) -> dict:
        results = []

        for incident in incidents:
            text = (
                incident.title + ' ' + incident.description
            ).lower()

            if FallbackService._is_noise(text):
                results.append({
                    'id': incident.id,
                    'is_noise': True,
                    'category': '',
                    'severity': None,
                    'action_steps': '',
                })
                continue

            category = FallbackService._get_category(text)
            results.append({
                'id': incident.id,
                'is_noise': False,
                'category': category,
                'severity': FallbackService.SEVERITY_MAP.get(category, 2),
                'action_steps': FallbackService.ACTION_MAP.get(category, ''),
            })

        return {'results': results}

    @staticmethod
    def _is_noise(text: str) -> bool:
        return any(keyword in text for keyword in FallbackService.NOISE_KEYWORDS)

    @staticmethod
    def _get_category(text: str) -> str:
        if any(keyword in text for keyword in FallbackService.DIGITAL_KEYWORDS):
            return 'digital'
        if any(keyword in text for keyword in FallbackService.WEATHER_KEYWORDS):
            return 'weather'
        if any(keyword in text for keyword in FallbackService.PHYSICAL_KEYWORDS):
            return 'physical'
        return 'physical'