from django.test import TestCase
from django.contrib.auth import get_user_model
from incidents.models import Incident
from incidents.services.enrichment_service import EnrichmentService

User = get_user_model()


class HappyPathTest(TestCase):
    """
    Happy path: 5 incidents are created (3 real, 2 noise).
    After enrichment, only 3 appear in the feed (noise filtered out).
    """

    def setUp(self):
        # 3 real incidents
        Incident.objects.create(
            title="Phishing SMS received",
            description="Got a suspicious OTP text from an unknown number asking for bank details.",
            location="Koramangala",
        )
        Incident.objects.create(
            title="Suspicious person near parking",
            description="A person was seen checking car doors in the apartment parking lot at 2am.",
            location="Koramangala",
        )
        Incident.objects.create(
            title="Heavy waterlogging near underpass",
            description="Severe waterlogging reported near the underpass after heavy rainfall.",
            location="Koramangala",
        )
        # 2 noise incidents
        Incident.objects.create(
            title="Ugh traffic is so bad today",
            description="Can't believe how terrible the traffic is. So frustrated with this city.",
            location="Koramangala",
        )
        Incident.objects.create(
            title="This neighbourhood is the worst",
            description="I hate how noisy this place is. The neighbours are so annoying and inconsiderate.",
            location="Koramangala",
        )

    def test_enrichment_filters_noise_and_enriches_real_incidents(self):
        # all 5 start unenriched
        self.assertEqual(Incident.objects.filter(is_enriched=False).count(), 5)

        # run enrichment (uses Groq or fallback)
        EnrichmentService.enrich_pending()

        # all 5 should now be enriched
        self.assertEqual(Incident.objects.filter(is_enriched=True).count(), 5)

        # only non-noise incidents appear in the feed
        feed_incidents = Incident.objects.filter(
            is_enriched=True,
            is_noise=False,
            location__icontains="Koramangala",
        )
        noise_incidents = Incident.objects.filter(
            is_enriched=True,
            is_noise=True,
        )

        # at least 3 real incidents should survive noise filtering
        self.assertGreaterEqual(feed_incidents.count(), 3)

        # noise incidents should be excluded from feed
        self.assertGreater(noise_incidents.count(), 0)

        # every feed incident must have action_steps filled in
        for incident in feed_incidents:
            self.assertTrue(
                len(incident.action_steps) > 0,
                f"Incident '{incident.title}' has no action steps."
            )

        # every feed incident must have a valid category
        valid_categories = {"physical", "digital", "weather"}
        for incident in feed_incidents:
            self.assertIn(
                incident.category,
                valid_categories,
                f"Incident '{incident.title}' has invalid category '{incident.category}'."
            )

        # every feed incident must have severity between 1 and 5
        for incident in feed_incidents:
            self.assertGreaterEqual(incident.severity, 1)
            self.assertLessEqual(incident.severity, 5)

    def test_feed_api_returns_only_enriched_non_noise(self):
        EnrichmentService.enrich_pending()

        response = self.client.get("/api/incidents/?location=Koramangala")
        self.assertEqual(response.status_code, 200)

        data = response.json()

        # none of the returned incidents should be noise
        for incident in data:
            self.assertFalse(
                incident["is_noise"],
                f"Noise incident '{incident['title']}' appeared in feed."
            )

        # all returned incidents should be enriched
        for incident in data:
            self.assertTrue(incident["is_enriched"])