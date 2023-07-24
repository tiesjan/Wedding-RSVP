from __future__ import annotations

from typing import TYPE_CHECKING

from flask_wtf import FlaskForm  # type: ignore[import]
from wtforms.fields import (  # type: ignore[import]
    BooleanField,
    EmailField,
    Field,
    RadioField,
    StringField,
)
from wtforms.form import Form  # type: ignore[import]
from wtforms.validators import (  # type: ignore[import]
    Email,
    InputRequired,
    Length,
    Optional as InputOptional,
    ValidationError,
)

from wedding_rsvp.database import RSVP

if TYPE_CHECKING:
    from typing import Any


def lower(value: Any) -> Any:
    """
    Converts the value to lowercase, if the value type supports it.
    """

    if hasattr(value, "lower"):
        value = value.lower()

    return value


def strip_value(value: Any) -> Any:
    """
    Strips whitespace characters surrounding the value, if the value type supports it.
    """

    if hasattr(value, "strip"):
        value = value.strip()

    return value


def value_or_none(value: Any) -> Any:
    """
    Returns the value as-is if truthy, otherwise returns None.
    """

    if value:
        return value

    return None


class RequiredIfTruthy(InputRequired):
    """
    Validator class that requires input data when the value of the given fieldname is truthy.

    If the value of the given fieldname is falsy, executes the `InputOptional` validator instead.
    """

    def __init__(self, fieldname: str, message: str | None = None) -> None:
        self.fieldname = fieldname

        super().__init__(message)

    def __call__(self, form: Form, field: Field) -> None:
        if self.fieldname not in form:
            raise KeyError(f"Form does not contain field: {self.fieldname}")

        other_field = form[self.fieldname]

        if bool(other_field.data) is True:
            super().__call__(form, field)

        else:
            InputOptional().__call__(form, field)


class RSVPForm(FlaskForm):
    """
    Form for RSVP registrations
    """

    guest_first_name = StringField(
        "Wat is je voornaam?",
        filters=[strip_value],
        validators=[InputRequired(), Length(max=50)],
    )
    guest_last_name = StringField(
        "Wat is je achternaam?",
        filters=[strip_value],
        validators=[InputRequired(), Length(max=50)],
    )
    guest_present = RadioField(
        "Ben je aanwezig op de bruiloft?",
        choices=[(True, "Ja, ik ben erbij."), (False, "Nee, helaas niet.")],
        coerce=lambda value: str(value) == str(True),
        filters=[strip_value],
        validators=[InputRequired()],
    )
    guest_present_ceremony = BooleanField(
        "Ceremonie",
        default=True,
        filters=[strip_value],
        validators=[],
    )
    guest_present_reception = BooleanField(
        "Receptie",
        default=True,
        filters=[strip_value],
        validators=[],
    )
    guest_present_dinner = BooleanField(
        "Diner",
        default=True,
        filters=[strip_value],
        validators=[],
    )
    guest_email = EmailField(
        "Wat is je e-mailadres?",
        filters=[strip_value, value_or_none, lower],
        validators=[RequiredIfTruthy("guest_present"), Length(max=254), Email()],
    )
    guest_diet_meat = BooleanField(
        "Vlees",
        filters=[strip_value],
        validators=[],
    )
    guest_diet_fish = BooleanField(
        "Vis",
        filters=[strip_value],
        validators=[],
    )
    guest_diet_vega = BooleanField(
        "Vegetarisch",
        filters=[strip_value],
        validators=[],
    )
    partner_first_name = StringField(
        "Wat is je partner's voornaam?",
        filters=[strip_value],
        validators=[RequiredIfTruthy("guest_present"), Length(max=50)],
    )
    partner_last_name = StringField(
        "Wat is je partner's achternaam?",
        filters=[strip_value],
        validators=[RequiredIfTruthy("guest_present"), Length(max=50)],
    )
    partner_diet_meat = BooleanField(
        "Vlees",
        filters=[strip_value],
        validators=[],
    )
    partner_diet_fish = BooleanField(
        "Vis",
        filters=[strip_value],
        validators=[],
    )
    partner_diet_vega = BooleanField(
        "Vegetarisch",
        filters=[strip_value],
        validators=[],
    )
    remarks = StringField(
        "Zijn er nog dingen die we moeten weten?",
        filters=[strip_value],
        validators=[InputOptional(), Length(max=250)],
    )

    def validate_guest_present_dinner(self, _: Field) -> None:
        any_program_item_present = any(
            item is True
            for item in (
                self.guest_present_ceremony.data,
                self.guest_present_reception.data,
                self.guest_present_dinner.data,
            )
        )

        if self.guest_present.data is True and any_program_item_present is False:
            raise ValidationError("Je dient je aan te melden voor minimaal één onderdeel.")

    def validate_guest_diet_vega(self, _: Field) -> None:
        any_diet_present = any(
            item is True
            for item in (
                self.guest_diet_meat.data,
                self.guest_diet_fish.data,
                self.guest_diet_vega.data,
            )
        )

        if self.guest_present_dinner.data is True and any_diet_present is False:
            raise ValidationError("Je dient minimaal één dieetwens in te vullen.")

    def validate_guest_email(self, field: Field) -> None:
        """
        Validate whether the guest email is unique, if the value has changed.
        """

        if field.data is not None and field.data != field.object_data:
            if RSVP.get_by_guest_email(guest_email=field.data) is not None:
                raise ValidationError(
                    "Je hebt je al met dit e-mailadres aangemeld. "
                    "Controleer je inbox voor de link om je aanmelding aan te passen."
                )

    def validate_partner_diet_vega(self, _: Field) -> None:
        any_diet_present = any(
            item is True
            for item in (
                self.partner_diet_meat.data,
                self.partner_diet_fish.data,
                self.partner_diet_vega.data,
            )
        )

        if self.guest_present_dinner.data is True and any_diet_present is False:
            raise ValidationError("Je dient minimaal één dieetwens in te vullen.")

    class Meta:
        locales = ("nl",)


def create_rsvp_form(*, with_partner: bool, rsvp_instance: RSVP | None = None) -> RSVPForm:
    """
    Convenience function to create an instance of the RSVPForm, based on the given parameters.
    """

    form = RSVPForm(obj=rsvp_instance)

    # Remove partner fields if guest comes alone
    if with_partner is False:
        del form.partner_first_name
        del form.partner_last_name
        del form.partner_diet_meat
        del form.partner_diet_fish
        del form.partner_diet_vega

    return form
