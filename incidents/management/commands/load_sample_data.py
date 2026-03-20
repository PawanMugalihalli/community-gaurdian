import json
import os
from django.core.management.base import BaseCommand
from incidents.models import Incident


class Command(BaseCommand):
    help = 'Load synthetic sample incidents from data/incidents_sample.json'

    def handle(self, *args, **kwargs):
        base_dir = os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(os.path.abspath(__file__))
                )
            )
        )
        file_path = os.path.join(base_dir, 'data', 'incidents_sample.json')

        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR(f'File not found: {file_path}')
            )
            return

        with open(file_path, 'r') as f:
            incidents = json.load(f)

        created = 0
        skipped = 0

        for incident in incidents:
            obj, was_created = Incident.objects.get_or_create(
                title=incident['title'],
                location=incident['location'],
                defaults={
                    'description': incident['description'],
                    'source': incident.get('source', 'user_report'),
                }
            )
            if was_created:
                created += 1
            else:
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Done. {created} incidents created, {skipped} already existed.'
            )
        )