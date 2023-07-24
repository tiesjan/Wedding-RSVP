from urllib.parse import urljoin

from flask import current_app, render_template, request, url_for
from flask_mail import Mail, Message  # type: ignore[import]

mail = Mail()


def send_confirmation_email(*, email_address: str, first_name: str, rsvp_code: str) -> None:
    """
    Send confirmation email to the given email address.
    """

    rsvp_url = urljoin(request.host_url, url_for("manage_rsvp", rsvp_code=rsvp_code))

    text_body = render_template("confirmation_email.txt", first_name=first_name, rsvp_url=rsvp_url)
    html_body = render_template("confirmation_email.html", first_name=first_name, rsvp_url=rsvp_url)

    message = Message(
        subject="Bedankt voor je aanmelding voor de bruiloft van Zhen & Ties Jan!",
        recipients=[email_address],
        body=text_body,
        html=html_body,
        sender=current_app.config["CONTACT_EMAIL"],
        charset="UTF-8",
    )

    mail.send(message)
