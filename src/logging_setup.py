# logging_setup.py
import logging
import sys
from logging.handlers import RotatingFileHandler


def setup_logging(log_file, console_level=logging.INFO, file_level=logging.DEBUG):
    fmt_console = "%(asctime)s | %(levelname)-8s | %(message)s"
    fmt_file = "%(asctime)s | %(name)-25s | %(levelname)-8s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(console_level)
    ch.setFormatter(logging.Formatter(fmt_console, datefmt))

    fh = RotatingFileHandler(log_file, maxBytes=10_000_000, backupCount=5)
    fh.setLevel(file_level)
    fh.setFormatter(logging.Formatter(fmt_file, datefmt))

    root = logging.getLogger()
    root.setLevel(min(console_level, file_level))
    root.addHandler(ch)
    root.addHandler(fh)

    for lib in ["matplotlib", "urllib3", "numexpr", "PIL"]:
        logging.getLogger(lib).setLevel(logging.WARNING)
