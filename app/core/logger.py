"""Central application logging: one configuration point, one logger namespace."""

import logging

LOGGER_NAME = "cargohub"
LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"


def configure_logging(level: str = "INFO") -> None:
    """Configure the root handler; safe to call again (reloads, tests)."""
    logging.basicConfig(level=level, format=LOG_FORMAT, force=True)


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a logger inside the ``cargohub`` namespace."""
    return logging.getLogger(f"{LOGGER_NAME}.{name}" if name else LOGGER_NAME)
