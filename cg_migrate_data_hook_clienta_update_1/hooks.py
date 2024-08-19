import base64
import datetime

# import locale
import re
import logging
from collections import defaultdict

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)
LST_KEY_EVENT = []


def post_init_hook(cr, e):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info("Start update 1")

    # Fix all formation without user, but they buy it
    slide_channel_ids = env["slide.channel"].search([("active", "=", False)])
    for slide_channel_id in slide_channel_ids:
        product_id = slide_channel_id.product_id
        sale_order_line_ids = env["sale.order.line"].search(
            [("product_id", "=", product_id.id)]
        )
        for sale_order_line_id in sale_order_line_ids:
            # partner_ids = env["res.partner"].browse(
            #     [a.order_partner_id.id for a in sale_order_line_ids]
            # )
            partner_id = sale_order_line_id.order_partner_id
            value_slide_channel_partner = {
                "channel_id": slide_channel_id.id,
                "completion": 0,
                "completed_slides_count": 0,
                "completed": False,
                "partner_id": partner_id.id,
                "create_date": sale_order_line_id.create_date,
            }
            # Validate if exist
            obj_slide_channel_partner = env["slide.channel.partner"].search(
                [
                    ("partner_id", "=", partner_id.id),
                    ("channel_id", "=", slide_channel_id.id),
                ],
                limit=1,
            )
            if not obj_slide_channel_partner:
                obj_slide_channel_partner = env[
                    "slide.channel.partner"
                ].create(value_slide_channel_partner)

    # Create event if not exist and update with all partner with invoice
    # pattern_formation_no = r"\b\d+\.\w+\b"
    # product_ids = env["product.template"].search(
    #     [("detailed_type", "=", "course")]
    # )
    # for product_id in product_ids:
    #     partner_id = env["res.partner"]
    #     match = re.search(pattern_formation_no, product_id.name)
    #     if match:
    #         no_formation = match.group()
    #         if no_formation in LST_KEY_EVENT:
    #             sale_order_line_ids = env["sale.order.line"].search(
    #                 [("product_id", "=", product_id.id)]
    #             )
    #             for sale_order_line_id in sale_order_line_ids:
    #                 partner_id += sale_order_line_id.order_partner_id
    #         if partner_id.exists():
    #             # Search event, or create it
    #             event_ids = env["event.event"].search([])
    #             for event_id in event_ids:
    #                 if no_formation.lower() in event_id.name.lower():
    #                     break
    #             else:
    #                 # Not found
    #                 value_event = {"name": f"Formation {no_formation}"}
    #                 event_id = env["event.event"].create(value_event)
    #             if event_id:
    #                 print("ok")
