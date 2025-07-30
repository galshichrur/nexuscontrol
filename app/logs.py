import logging
import datetime
import json
from typing import List
from config import Config

LOG_FILE_PATH = Config.LOGS_PATH


class FileLogHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "event_type": record.levelname.lower(),
            "message": log_entry
        }
        with open(LOG_FILE_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")


def load_logs(limit: int) -> List[dict]:
    try:
        with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
        logs = [json.loads(line) for line in lines if line.strip()]
        return logs[-limit:]
    except FileNotFoundError:
        return []


# Configure logger
logger = logging.getLogger(LOG_FILE_PATH)
logger.setLevel(logging.INFO)
file_handler = FileLogHandler()
formatter = logging.Formatter("%(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)