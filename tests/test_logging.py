from __future__ import annotations

import logging

import schematico.logging as schematico_logging
from schematico.logging import get_logger


def test_get_logger_namespacing():
    logger = get_logger("core.discovery")
    assert logger.name == "schematico.core.discovery"


def test_configure_logging_is_idempotent():
    schematico_logging._configured = False
    root = logging.getLogger("schematico")
    root.handlers.clear()

    get_logger("cli.main")
    get_logger("core.discovery")

    assert len(root.handlers) == 1
