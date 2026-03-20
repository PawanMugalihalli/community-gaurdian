import json
from groq import Groq
from django.conf import settings


client = Groq(api_key=settings.GROQ_API_KEY)


PROMPT_TEMPLATE = """
You are a calm and responsible community safety assistant.

You will be given a list of raw incident reports from a neighborhood.
Your job is to analyze each one and return a structured JSON response.

For each incident you must:
1. Determine if it is noise (venting, repetitive, irrelevant, non-safety related)
2. If it is not noise, categorize it as one of: physical, digital, weather
3. Assign a severity score from 1 to 5 (5 being most severe)
4. Write one calm, clear, actionable step the user can take

Rules:
- Be calm and factual. Never use alarming language.
- If an incident is noise, set is_noise to true and leave category, severity, action_steps empty.
- Return ONLY valid JSON. No extra text, no markdown, no explanation.

Return this exact JSON structure:
{{
    "results": [
        {{
            "id": <incident_id>,
            "is_noise": <true or false>,
            "category": "<physical | digital | weather | >",
            "severity": <1-5 or null if noise>,
            "action_steps": "<one calm actionable step or empty string if noise>"
        }}
    ]
}}

Incidents:
{incidents}
"""


class GroqService:

    @staticmethod
    def analyze(incidents: list) -> dict:
        formatted = json.dumps([
            {
                "id": i.id,
                "title": i.title,
                "description": i.description,
                "location": i.location,
            }
            for i in incidents
        ], indent=2)

        prompt = PROMPT_TEMPLATE.format(incidents=formatted)

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "You are a community safety assistant. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            max_tokens=1000,
        )

        cleaned = response.choices[0].message.content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]

        return json.loads(cleaned)