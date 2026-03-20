from incidents.fallback_constants import (
    ACTION_MAP,
    DIGITAL_KEYWORDS,
    NOISE_KEYWORDS,
    PHYSICAL_KEYWORDS,
    SEVERITY_MAP,
    WEATHER_KEYWORDS,
)


class FallbackService:

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
                'severity': SEVERITY_MAP.get(category, 2),
                'action_steps': ACTION_MAP.get(category, ''),
            })

        return {'results': results}

    @staticmethod
    def _is_noise(text: str) -> bool:
        return any(keyword in text for keyword in NOISE_KEYWORDS)

    @staticmethod
    def _get_category(text: str) -> str:
        if any(keyword in text for keyword in DIGITAL_KEYWORDS):
            return 'digital'
        if any(keyword in text for keyword in WEATHER_KEYWORDS):
            return 'weather'
        if any(keyword in text for keyword in PHYSICAL_KEYWORDS):
            return 'physical'
        return 'physical'
