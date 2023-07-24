from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask import Config


APP_CONFIG_DEFAULTS = {
    "LOG_FORMAT": "[%(asctime)s] [%(name)s] %(levelname)s in %(module)s: %(message)s",
    "WTF_I18N_ENABLED": False,
}


REQUIRED_CONFIG_KEYS = ("ADMIN_PASSWORD", "CONTACT_EMAIL", "RSVP_DEADLINE")


class MissingConfigurationKeyError(Exception):
    """
    Error denoting a missing configuration key that is required to be set.
    """

    def __init__(self, *, missing_key: str):
        super().__init__(missing_key)


def check_app_config(*, app_config: Config) -> None:
    """
    Checks whether all the required config keys are set on the given `app_config`.
    """

    for config_key in REQUIRED_CONFIG_KEYS:
        if config_key not in app_config:
            raise MissingConfigurationKeyError(missing_key=config_key)
