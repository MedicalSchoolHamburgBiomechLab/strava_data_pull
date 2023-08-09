from pathlib import Path
import os

ROOT_PATH = Path(__file__).parents[0]  # todo: remove ugly workaround
LOG_DIR = os.path.join(ROOT_PATH, 'log')

CLIENT_ID = 'YOUR_STRAVA_CLIENT_ID'
CLIENT_SECRET = 'YOUR_STRAVA_CLIENT_SECRET'
