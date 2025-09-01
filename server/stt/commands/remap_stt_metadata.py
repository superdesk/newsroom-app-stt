import time
import json

from pathlib import Path
from superdesk import get_resource_service
from newsroom.commands.manager import manager


DEFAULT_CATEGORY_CODE = "3"  # NOTE: is 3 always for `Kotimaa` category?
DEFAULT_CATEGORY_NAME = "Kotimaa"


# Load topics CV from json file based on STT-1210
topics_cv_path = Path(__file__).parent / "data" / "STT_Media_Topics.json"
with open(topics_cv_path, "r", encoding="utf-8") as f:
    topics_cv = json.load(f)
topics_map = {
    int(item.get("iptc_subject")): item
    for item in topics_cv.get("items", [])
    if item.get("iptc_subject")
}

# used as fallback in case the code is not found
topics_by_name = {
    item.get("name"): item
    for item in topics_cv.get("items", [])
}


def update_service(item, updates):
    """Clear all service field values, including those with name: 'Australian General News'."""

    if item.get("service"):
        updates["service"] = []


def update_category(item, updates):
    """Update anpa_category and sttversion from subject (sttdepartment)."""

    subject = item.get("subject", [])
    for entry in subject:
        if entry.get("scheme") == "sttdepartment":
            updates["anpa_category"] = [
                {"qcode": entry.get("code"), "name": entry.get("name")}
            ]
            return
    updates["anpa_category"] = [
        {"qcode": DEFAULT_CATEGORY_CODE, "name": DEFAULT_CATEGORY_NAME}
    ]
    updates["sttversion"] = "Pika+"


def update_subject(item, updates, not_found):
    """Update subject by mapping sttsubj to Media topics CV."""

    subject = item.get("subject", [])
    new_subjects = [entry for entry in subject if entry.get("scheme") != "sttsubj"]

    for entry in subject:
        if entry.get("scheme") == "sttsubj":
            code = entry.get("code")
            name = entry.get("name")
            topic = topics_map.get(int(code)) or topics_by_name.get(name)

            if topic:
                new_subjects.append(
                    {
                        "code": topic.get("qcode"),
                        "name": topic.get("name"),
                        "scheme": "mediatopic",  # TODO: should it be `sttsubj` instead?
                    }
                )
            else:
                not_found.add(code)
                new_subjects.append(
                    {"code": code, "name": name, "scheme": "mediatopic"}
                )

    updates["subject"] = new_subjects


def update_priority(item, updates):
    """Update the priority field in updates based on the stturgency subject code.

    This function looks for a subject entry with the scheme 'stturgency' in the item's subject list.
    If found, it attempts to extract the priority as an integer from the code and sets it in the updates dict.
    """

    for entry in item.get("subject", []):
        if entry.get("scheme") == "stturgency":
            try:
                updates["priority"] = int(entry.get("code")[-1])
                return
            except Exception:
                continue


@manager.option("--resources", dest="resources", nargs="+", default=["items", "agenda"])
@manager.option("--limit", dest="limit", type=int, default=500)
@manager.option("--sleep-secs", dest="sleep_secs", type=float, default=2)
@manager.option("--dry-run", dest="dry_run", action="store_true")
@manager.option("-v", "--verbose", dest="verbose", action="store_true")
def remap_stt_metadata(resources, limit, sleep_secs, dry_run, verbose):
    """
    Remap STT metadata fields for Wire and Agenda items in Newsroom.

    This command updates items by:
      - Mapping 'sttdepartment' to 'anpa_category'
      - Mapping 'sttsubj' to Media Topics controlled vocabulary
      - Updating priority based on 'stturgency' codes for planning items

    Supports dry-run mode, resource selection, batch processing, and verbosity.
    """

    BATCH_SIZE = 100
    topics_not_found = set()

    for resource in resources:
        print(f"Processing resource: '{resource}'")
        service = get_resource_service(resource)
        processed = 0

        for item in service.get_all_batch(size=BATCH_SIZE, max_iterations=10000):
            if limit != 0 and processed >= limit:
                print(f"Reached limit of {limit} items for {resource}.")
                break

            updates = {}
            update_service(item, updates)
            update_category(item, updates)
            update_subject(item, updates, topics_not_found)

            if resource == "agenda" and item.get("item_type") == "planning":
                update_priority(item, updates)

            if not updates:
                continue

            prefix = "DRY RUN: " if dry_run else ""
            msg = f"{prefix}Updating {resource} item '{item['_id']}'"
            if verbose:
                msg += f" with {updates}"
            print(msg)

            if not dry_run:
                service.system_update(item["_id"], updates, item)

            processed += 1

            # sleep after each batch
            if processed % BATCH_SIZE == 0:
                print(".", end="", flush=True)
                time.sleep(sleep_secs)

        if verbose:
            print(f"Topics not found: {topics_not_found}")

        print(f"Finished '{resource}'. Total processed: {processed}")

    print("Category remapping completed.")
