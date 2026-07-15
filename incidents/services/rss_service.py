import logging
import feedparser

from incidents.models import Incident
from incidents.ingestion.cities import CITIES


logger = logging.getLogger(__name__)


class RSSService:


    @staticmethod
    def fetch_all_cities():

        total_created = 0


        for city in CITIES:

            created = RSSService.fetch_city(city)

            total_created += created


        logger.info(
            f"RSS ingestion completed. "
            f"Added {total_created} incidents"
        )



    @staticmethod
    def fetch_city(city):

        created_count = 0


        feeds = CITIES[city]["feeds"]


        for url in feeds:

            try:

                feed = feedparser.parse(url)


                for item in feed.entries:


                    title = item.get(
                        "title",
                        ""
                    )


                    description = item.get(
                        "summary",
                        ""
                    )


                    link = item.get(
                        "link",
                        ""
                    )


                    if not title:
                        continue



                    # duplicate prevention
                    exists = Incident.objects.filter(
                        title=title,
                        location=city
                    ).exists()


                    if exists:
                        continue



                    Incident.objects.create(

                        title=title[:255],

                        description=description,

                        location=city,

                        source=link[:100],

                    )


                    created_count += 1



            except Exception as e:

                logger.error(
                    f"RSS failed for {city}: {e}"
                )



        return created_count