from __future__ import annotations

import csv
from io import StringIO

from wedding_rsvp.database import RSVP


def export_rsvps_as_csv() -> str:
    """
    Export the registered RSVPs as CSV formatted string.
    """

    field_to_header_mapping = {
        "rsvp_code": "Code",
        "guest_first_name": "Voornaam",
        "guest_last_name": "Achternaam",
        "guest_present": "Aanwezig",
        "guest_present_ceremony": "Aanwezig: ceremonie",
        "guest_present_reception": "Aanwezig: receptie",
        "guest_present_dinner": "Aanwezig: diner",
        "guest_email": "E-mail",
        "guest_diet_meat": "Dieetwensen: Vlees",
        "guest_diet_fish": "Dieetwensen: Vis",
        "guest_diet_vega": "Dieetwensen: Vegetarisch",
        "with_partner": "Met partner",
        "partner_first_name": "Partner voornaam",
        "partner_last_name": "Partner achternaam",
        "partner_diet_meat": "Partner dieetwensen: Vlees",
        "partner_diet_fish": "Partner dieetwensen: Vis",
        "partner_diet_vega": "Partner dieetwensen: Vegetarisch",
        "remarks": "Opmerkingen",
        "created_at": "Registratiedatum",
        "updated_at": "Laatst aangepast",
    }
    fields = tuple(field_to_header_mapping.keys())

    csv_buffer = StringIO()
    csv_writer = csv.DictWriter(csv_buffer, fieldnames=fields)

    csv_writer.writerow(field_to_header_mapping)

    for rsvp in RSVP.get_all():
        row = {}
        for field in fields:
            field_value = getattr(rsvp, field)

            if isinstance(field_value, bool):
                field_value = "Ja" if field_value is True else "Nee"

            if field_value is None:
                field_value = ""

            row[field] = field_value

        csv_writer.writerow(row)

    return csv_buffer.getvalue()
