import logging

import sentry_sdk
from sentry_sdk import set_level
from sentry_sdk.integrations.logging import LoggingIntegration


def init_sentry(dsn: str, env: str):
    if not dsn:
        return
    logging_integration = LoggingIntegration(level=logging.ERROR, event_level=logging.ERROR)
    sentry_sdk.init(
        dsn=dsn,
        integrations=[logging_integration],
        environment=env
    )
