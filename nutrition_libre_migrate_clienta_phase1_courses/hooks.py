import os
import time

import logging
import json

from odoo import SUPERUSER_ID, _, api, fields, models

_logger = logging.getLogger(__name__)


def post_init_hook(cr, e):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info("Start migration phase 1 courses")

    script_dir = os.path.abspath(os.path.dirname(__file__))
    data_file_path = os.path.join(script_dir, "data.json")

    course_ids = env["slide.channel"].search(
        ["|", ("active", "=", True), ("active", "=", False)]
    )
    lst_new_course = []
    with open(data_file_path, "r") as f:
        json_data = json.load(f)
        for course_name, dct_course_value in json_data.items():
            course_id_str = course_name[: course_name.find("_")]
            note = dct_course_value.get("note")
            lst_course_id = [a for a in course_ids if course_id_str in a.name]
            if not lst_course_id:
                # _logger.error(f"Cannot found courses with id {course_id_str}")
                # continue
                value_course = {
                    "name": course_name,
                    "is_published": True,
                }
                course_id = env["slide.channel"].create(value_course)
                lst_new_course.append(course_name)
            else:
                course_id = lst_course_id[0]

                # Force re-enable it
                course_id.active = True
                # Delete all items except certification, because was empty
                slide_slide_ids = env["slide.slide"].search(
                    [
                        ("slide_type", "!=", "certification"),
                        ("channel_id", "=", course_id.id),
                    ]
                )
                if slide_slide_ids:
                    slide_slide_ids.unlink()
                slide_slide_ids = env["slide.slide"].search(
                    [
                        ("slide_type", "=", "certification"),
                        ("channel_id", "=", course_id.id),
                    ]
                )
                for slide_slide_id in slide_slide_ids:
                    slide_slide_id.sequence = 100

            for item_name, item_url in dct_course_value.get("courses").items():
                slide_slide_value = {
                    "channel_id": course_id.id,
                    "name": item_name,
                    "is_published": True,
                    "website_published": True,
                }
                if item_name == "note":
                    if not note:
                        _logger.warning("Note is empty, not suppose to!")
                        continue
                    slide_slide_value["sequence"] = -1
                    slide_slide_value["html_content"] = note[1:].strip()
                    slide_slide_value["slide_category"] = "article"
                    slide_slide_value["slide_type"] = "article"
                    # slide_slide_value["user_id"] = False
                elif item_name.endswith(".pdf"):
                    slide_slide_value["source_type"] = "external"
                    slide_slide_value["slide_category"] = "document"
                    slide_slide_value["slide_type"] = "pdf"
                    slide_slide_value["url"] = item_url
                elif item_name.endswith(".mp4"):
                    slide_slide_value["slide_category"] = "video"
                    slide_slide_value["slide_type"] = "google_drive_video"
                    slide_slide_value["url"] = item_url
                else:
                    if item_name[-4] == ".":
                        _logger.error(f"Cannot identify file {item_name}")
                        continue
                    else:
                        # It's a pptx without extension
                        slide_slide_value["source_type"] = "external"
                        slide_slide_value["slide_category"] = "document"
                        slide_slide_value["slide_type"] = "slides"
                        slide_slide_value["url"] = item_url
                if slide_slide_value:
                    try:
                        slide_slide_id = env["slide.slide"].create(
                            slide_slide_value
                        )
                    except Exception as e:
                        time.sleep(1)
                        slide_slide_id = env["slide.slide"].create(
                            slide_slide_value
                        )
                print(item_name)
            print(course_name)
    print(lst_new_course)
    _logger.info("End migration phase 1 courses")
