from django.test import TestCase
from unittest.mock import patch
from incidents.models import Incident
from incidents.services.enrichment_service import EnrichmentService


class EdgeCaseTest(TestCase):
    """
    Edge case: Groq/AI service throws an exception.
    Fallback must run automatically and incidents must still get enriched.
    ai_enriched must be False to indicate fallback was used.
    """

    def setUp(self):
        Incident.objects.create(
            title="Phishing SMS received",
            description="Got a suspicious OTP text asking for bank details and card info.",
            location="Bangalore",
        )
        Incident.objects.create(
            title="Suspicious person near parking",
            description="A person was seen checking car doors in the apartment parking lot at midnight.",
            location="Bangalore",
        )
        Incident.objects.create(
            title="Ugh traffic is terrible today",
            description="Can't believe how bad the traffic is. So annoying and frustrating.",
            location="Bangalore",
        )

    @patch("incidents.services.enrichment_service.GroqService.analyze")
    def test_fallback_runs_when_ai_fails(self, mock_groq):
        # make Groq throw an exception
        mock_groq.side_effect = Exception("Groq API unavailable — simulated failure")

        # enrichment should still complete without raising
        try:
            EnrichmentService.enrich_pending()
        except Exception:
            self.fail("EnrichmentService raised an exception when AI failed — fallback did not catch it.")

        # all incidents must be enriched despite AI failure
        self.assertEqual(
            Incident.objects.filter(is_enriched=True).count(),
            3,
            "Not all incidents were enriched after fallback ran."
        )

        # ai_enriched must be False — fallback ran, not Groq
        self.assertEqual(
            Incident.objects.filter(ai_enriched=True).count(),
            0,
            "ai_enriched should be False when fallback ran."
        )
        self.assertEqual(
            Incident.objects.filter(ai_enriched=False, is_enriched=True).count(),
            3,
        )

        # fallback must have filled in action_steps for non-noise incidents
        real_incidents = Incident.objects.filter(is_enriched=True, is_noise=False)
        for incident in real_incidents:
            self.assertTrue(
                len(incident.action_steps) > 0,
                f"Fallback did not fill action_steps for '{incident.title}'."
            )

    @patch("incidents.services.enrichment_service.GroqService.analyze")
    def test_fallback_result_has_correct_structure(self, mock_groq):
        mock_groq.side_effect = Exception("Groq quota exceeded — simulated failure")

        EnrichmentService.enrich_pending()

        enriched = Incident.objects.filter(is_enriched=True)
        self.assertEqual(enriched.count(), 3)

        valid_categories = {"physical", "digital", "weather", ""}
        for incident in enriched:
            if not incident.is_noise:
                self.assertIn(
                    incident.category,
                    valid_categories,
                    f"Invalid category '{incident.category}' from fallback."
                )
                self.assertGreaterEqual(incident.severity, 1)
                self.assertLessEqual(incident.severity, 5)

    @patch("incidents.services.enrichment_service.GroqService.analyze")
    def test_second_batch_retries_fallback_incidents(self, mock_groq):
        """
        Incidents enriched by fallback (ai_enriched=False) should be
        picked up again on the next cron run when AI recovers.
        """
        # first run — AI fails, fallback enriches everything
        mock_groq.side_effect = Exception("AI down")
        EnrichmentService.enrich_pending()

        self.assertEqual(Incident.objects.filter(ai_enriched=False, is_enriched=True).count(), 3)

        # second run — AI recovers
        mock_groq.side_effect = None
        mock_groq.return_value = {
            "results": [
                {
                    "id": i.id,
                    "is_noise": False,
                    "category": "digital",
                    "severity": 4,
                    "action_steps": "Do not click suspicious links. Enable 2FA immediately."
                }
                for i in Incident.objects.all()
            ]
        }

        EnrichmentService.enrich_pending()

        # now all should be ai_enriched=True
        self.assertEqual(
            Incident.objects.filter(ai_enriched=True).count(),
            3,
            "Fallback incidents were not retried when AI recovered."
        )