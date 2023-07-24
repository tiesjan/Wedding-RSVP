from __future__ import annotations

import logging
from datetime import date
from logging.handlers import WatchedFileHandler

import click
from flask import Flask, g
from werkzeug.exceptions import HTTPException

from wedding_rsvp import views
from wedding_rsvp.config import APP_CONFIG_DEFAULTS, check_app_config
from wedding_rsvp.database import db
from wedding_rsvp.mail import mail


def create_app() -> Flask:
    app = Flask(__name__)

    # Configure application
    app.config.from_mapping(APP_CONFIG_DEFAULTS)
    app.config.from_envvar("WEDDING_RSVP_CONFIG_FILE", silent=True)
    check_app_config(app_config=app.config)

    # Configure logging if log file is set in app configuration
    if "LOG_FILE" in app.config:
        log_level = logging.INFO if app.debug else logging.WARNING

        logging.basicConfig(
            format=app.config["LOG_FORMAT"],
            level=log_level,
            handlers=[WatchedFileHandler(filename=app.config["LOG_FILE"])],
        )

        for logger_name in ("sqlalchemy", "werkzeug"):
            logging.getLogger(logger_name).setLevel(log_level)

    # Initialize apps
    db.init_app(app)
    mail.init_app(app)

    # Register CLI command group
    app.cli.add_command(rsvp_cli, name="rsvp")

    # Register request processors
    @app.before_request
    def build_request_context() -> None:
        """Store global request context"""
        if app.config.get("RSVP_DEADLINE") is not None:
            g.deadline_passed = date.today() >= app.config["RSVP_DEADLINE"]
        else:
            g.deadline_passed = False

    # Register URLs
    app.add_url_rule(
        "/registreren",
        view_func=views.register_rsvp,
        methods=["GET", "POST"],
        defaults={"with_partner": False},
    )
    app.add_url_rule(
        "/registreren-met-partner",
        view_func=views.register_rsvp,
        methods=["GET", "POST"],
        defaults={"with_partner": True},
    )
    app.add_url_rule(
        "/<string:rsvp_code>",
        view_func=views.manage_rsvp,
        methods=["GET", "POST"],
        defaults={},
    )
    app.add_url_rule(
        "/admin",
        view_func=views.admin,
        methods=["GET"],
    )
    app.add_url_rule(
        "/admin/rsvp.csv",
        view_func=views.rsvp_csv,
        methods=["GET"],
    )

    # Register error handlers
    app.register_error_handler(HTTPException, views.handle_http_exception)

    return app


# CLI commands
@click.group()
def rsvp_cli() -> None:
    pass


@rsvp_cli.command()
def create_db() -> None:
    """
    Creates tables that do not yet exist in the database.
    """

    click.echo("Creating tables that do not yet exist in the database...")

    db.create_all()
