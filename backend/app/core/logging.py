import logging
import sys

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"

handlers = [logging.StreamHandler(sys.stdout)]
logging.basicConfig(level=logging.INFO, handlers=handlers, format=LOG_FORMAT)
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

logger = logging.getLogger("ifesdoc")
