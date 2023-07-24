from __future__ import annotations

from typing import TYPE_CHECKING

from flask import flash, g, make_response, redirect, render_template, url_for
from werkzeug.exceptions import NotFound

from wedding_rsvp.auth import UserType, http_auth
from wedding_rsvp.database import RSVP, db
from wedding_rsvp.export import export_rsvps_as_csv
from wedding_rsvp.forms import create_rsvp_form
from wedding_rsvp.mail import send_confirmation_email

if TYPE_CHECKING:
    import flask
    import werkzeug
    from werkzeug.exceptions import HTTPException

    HTTPResponse = flask.Response | werkzeug.Response


def handle_http_exception(exception: HTTPException) -> str:
    """
    Handle HTTP exceptions.
    """

    template_context = {
        "page_title": f"{exception.code or ''} {exception.name}".strip(),
        "exception": exception,
    }
    return render_template("exception.html", **template_context)


@http_auth.login_required(optional=True)
def register_rsvp(with_partner: bool) -> str | HTTPResponse:
    """
    Create or manage an RSVP registration.
    """

    form = create_rsvp_form(with_partner=with_partner)

    form_enabled = http_auth.current_user() is UserType.ADMIN or not g.deadline_passed

    if form_enabled and form.validate_on_submit():
        rsvp_instance = RSVP()
        form.populate_obj(rsvp_instance)

        rsvp_instance.with_partner = with_partner

        db.session.add(rsvp_instance)
        db.session.commit()

        if rsvp_instance.guest_present is True:
            try:
                send_confirmation_email(
                    email_address=rsvp_instance.guest_email,
                    first_name=rsvp_instance.guest_first_name,
                    rsvp_code=rsvp_instance.rsvp_code,
                )
            except Exception:
                db.session.delete(rsvp_instance)
                db.session.commit()
                raise

        flash("Je aanmelding is succesvol verwerkt.", category="success")
        return redirect(url_for("manage_rsvp", rsvp_code=rsvp_instance.rsvp_code))

    template_context = {
        "form": form,
        "form_enabled": form_enabled,
        "with_partner": with_partner,
    }
    return render_template("rsvp.html", **template_context)


@http_auth.login_required(optional=True)
def manage_rsvp(rsvp_code: str) -> str | HTTPResponse:
    """
    Create or manage an RSVP registration.
    """

    rsvp_instance = RSVP.get_by_rsvp_code(rsvp_code=rsvp_code)
    if rsvp_instance is None:
        raise NotFound(
            "Kon de aanmelding niet vinden. Controleer of je de volledige link hebt gekopieerd."
        )

    with_partner = rsvp_instance.with_partner

    form = create_rsvp_form(with_partner=with_partner, rsvp_instance=rsvp_instance)

    form_enabled = http_auth.current_user() is UserType.ADMIN or not g.deadline_passed

    if form_enabled and form.validate_on_submit():
        form.populate_obj(rsvp_instance)

        db.session.add(rsvp_instance)
        db.session.commit()

        flash("Je aanmelding is succesvol bijgewerkt.", category="success")
        return redirect(url_for("manage_rsvp", rsvp_code=rsvp_instance.rsvp_code))

    template_context = {
        "form": form,
        "form_enabled": form_enabled,
        "with_partner": with_partner,
    }
    return render_template("rsvp.html", **template_context)


@http_auth.login_required
def admin() -> str | HTTPResponse:
    """
    Admin page with a list of registered RSVPs.
    """

    template_context = {
        "rsvp_instances": RSVP.get_all(),
    }
    return render_template("admin.html", **template_context)


@http_auth.login_required
def rsvp_csv() -> str | HTTPResponse:
    """
    CSV export of registered rsvps.
    """

    rsvps_as_csv = export_rsvps_as_csv()

    response = make_response(rsvps_as_csv)
    response.mimetype = "text/csv"
    response.headers["Content-Disposition"] = "attachment"
    return response
