from __future__ import annotations

import logging


def configure_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure a predictable console logger for evaluation runs."""
    logger = logging.getLogger("llm_eval_harness")
    logger.setLevel(level)
    logger.propagate = False

    if not any(isinstance(handler, logging.StreamHandler) for handler in logger.handlers):
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
