import logging, os
from datetime import datetime
import src.pycon2026.constants.constants as constants

def setup_file_logging(agent_name: str) -> None:
    os.makedirs(constants.LOGS_FOLDER, exist_ok=True)
    filename = datetime.now().strftime(constants.LOG_FILENAME_TEMPLATE.format(agent_name=agent_name))
    handler = logging.FileHandler(os.path.join(constants.LOGS_FOLDER, filename))
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S"))
    logging.getLogger("src.pycon2026").addHandler(handler)