import os
import logging
from constants import LOG_DIR

log_path = os.path.join(LOG_DIR, 'dev.log')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s in %(filename)s(Line: %(lineno)s): %(message)s')
file_handler = logging.FileHandler(log_path)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
