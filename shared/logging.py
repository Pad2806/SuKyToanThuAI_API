"""Shared logging configuration."""
import logging
import sys


def setup_logging(service_name: str, level: str = "INFO") -> logging.Logger:
    logging.basicConfig(
        stream=sys.stdout,
        level=getattr(logging, level.upper(), logging.INFO),
        format=f"%(asctime)s [{service_name}] %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    return logging.getLogger(service_name)
