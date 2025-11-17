"""Small utility helpers used by tests and scripts."""
import logging


def get_logger(name: str = __name__):
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    return logging.getLogger(name)


def ensure_dir(path: str) -> None:
    import os
    os.makedirs(path, exist_ok=True)
