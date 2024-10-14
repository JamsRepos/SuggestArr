"""
This module automates the process of retrieving recently watched movies and TV shows
from Jellyfin, finding similar content via TMDb, and requesting the content via Jellyseer.

Classes:
    - JellyfinClient: A client to interact with the Jellyfin API.
    - JellyseerClient: A client to interact with the Jellyseer API.
    - TMDbClient: A client to interact with the TMDb API.
    - ContentAutomation: A class that handles the automation of movie and TV show processing.
"""

import logging
import os
from config import TMDB_API_KEY, JELLYFIN_API_URL, JELLYFIN_TOKEN, JELLYSEER_API_URL, \
    JELLYSEER_TOKEN
from jellyfin.jellyfin_client import JellyfinClient
from jellyseer.jellyseer_client import JellyseerClient
from tmdb.tmdb_client import TMDbClient

# Constants
LOG_DIR = 'logs'
LOG_FILE_PATH = os.path.join(LOG_DIR, 'automate.log')
LOG_LEVEL = logging.INFO

# Ensure the log directory exists
if not os.path.exists(LOG_DIR):
    try:
        os.makedirs(LOG_DIR)
    except OSError as e:
        logging.error("Failed to create log directory: %s", str(e))

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Logs to the console
        logging.FileHandler(LOG_FILE_PATH, mode='a')  # Logs to a file
    ]
)


class ContentAutomation:
    """
    This class handles the automation process of fetching recently watched items from Jellyfin,
    finding similar content via TMDb, and requesting the content via Jellyseer.
    """

    def __init__(self):
        """
        Initialize the clients for Jellyfin, TMDb, and Jellyseer.
        """
        self.jellyfin_client = JellyfinClient(
            JELLYFIN_API_URL,
            JELLYFIN_TOKEN
        )
        self.jellyseer_client = JellyseerClient(
            JELLYSEER_API_URL,
            JELLYSEER_TOKEN
        )
        self.tmdb_client = TMDbClient(
            TMDB_API_KEY
        )

        self.max_similar_movie = min(int(os.getenv('MAX_SIMILAR_MOVIE', '3')), 20)
        self.max_similar_tv = min(int(os.getenv('MAX_SIMILAR_TV', '2')), 20)

        self.processed_series = set()  # To track series already processed

    def run(self):
        """
        Main entry point to start the automation process.
        """
        users = self.jellyfin_client.get_all_users()
        for user in users:
            self.process_user_recent_items(user)

    def process_user_recent_items(self, user):
        """
        Process the recently watched items (movies and TV shows) for a specific Jellyfin user.
        :param user: The Jellyfin user object.
        """
        user_id = user['Id']
        logging.info(
            "Fetching recently watched content for user: %s (%s)", user['Name'], user_id)

        recent_items = self.jellyfin_client.get_recent_items(user_id)
        if recent_items and 'Items' in recent_items:
            for item in recent_items['Items']:
                self.process_item(user_id, item)

    def process_item(self, user_id, item):
        """
        Process an individual item (either a movie or TV show) based on its type.
        :param user_id: The ID of the Jellyfin user.
        :param item: The item to be processed (movie or TV show episode).
        """
        item_type = item['Type']
        item_id = item['Id']

        if item_type == 'Movie':
            self.process_movie(user_id, item_id)
        elif item_type == 'Episode':
            self.process_episode(user_id, item)

    def process_movie(self, user_id, item_id):
        """
        Process a movie by finding similar movies via TMDb and requesting them via Jellyseer.
        :param user_id: The ID of the Jellyfin user.
        :param item_id: The ID of the movie item.
        """
        tmdb_id = self.jellyfin_client.get_item_provider_id(user_id, item_id)
        if tmdb_id:
            similar_movies = self.tmdb_client.find_similar_movies(tmdb_id)
            for similar_movie_id in similar_movies[:self.max_similar_movie]:
                if not self.jellyseer_client.check_already_requested(similar_movie_id, 'movie'):
                    self.jellyseer_client.request_media(
                        'movie', similar_movie_id)
                    logging.info(
                        "Requested download for movie with ID: %s", similar_movie_id)

    def process_episode(self, user_id, item):
        """
        Process a TV show episode by finding similar TV shows via TMDb and requesting them
        via Jellyseer.
        :param user_id: The ID of the Jellyfin user.
        :param item: The episode item to be processed.
        """
        series_id = item.get('SeriesId')
        series_name = item.get('SeriesName')
        if series_id and series_id not in self.processed_series:
            logging.info("Processing series: %s (Series ID: %s)",
                        series_name, series_id)
            self.processed_series.add(series_id)

            tvdb_id = self.jellyfin_client.get_item_provider_id(
                user_id, series_id, provider='Tvdb')
            if tvdb_id:
                self.request_similar_tv_shows(tvdb_id, series_name)

    def request_similar_tv_shows(self, tvdb_id, series_name):
        """
        Request similar TV shows via Jellyseer after finding them through TMDb.
        :param tvdb_id: The TVDb ID of the series.
        :param series_name: The name of the series being processed.
        """
        logging.info("TVDb ID for series '%s': %s", series_name, tvdb_id)
        tmdb_id = self.tmdb_client.find_tmdb_id_from_tvdb(tvdb_id)

        if tmdb_id:
            similar_tvshows = self.tmdb_client.find_similar_tvshows(tmdb_id)
            if similar_tvshows:
                logging.info(
                    "Found %d similar TV shows for '%s'", len(
                        similar_tvshows), series_name
                )

                for similar_tvshow_id in similar_tvshows[:self.max_similar_tv]:
                    if not self.jellyseer_client.check_already_requested(similar_tvshow_id, 'tv'):
                        self.jellyseer_client.request_media(
                            'tv', similar_tvshow_id)
                        logging.info(
                            "Requested download for TV show with ID: %s", similar_tvshow_id)
            else:
                logging.warning(
                    "No similar TV shows found for '%s'", series_name)
        else:
            logging.warning(
                "Could not find TMDb ID for series '%s'", series_name)


if __name__ == "__main__":
    automation = ContentAutomation()
    automation.run()