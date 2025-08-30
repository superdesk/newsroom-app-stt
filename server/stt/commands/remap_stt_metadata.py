import time
import json

from pathlib import Path
from dataclasses import dataclass
from superdesk import get_resource_service
from newsroom.commands.manager import manager


@dataclass(frozen=True)
class DefaultCategory:
    code: str = "3"  # NOTE: is 3 always for `Kotimaa` category?
    name: str = "Kotimaa"


# Load topics CV from json file based on STT-1210
topics_cv_path = Path(__file__).parent / "data" / "STT_Media_Topics.json"
with open(topics_cv_path, "r", encoding="utf-8") as f:
    topics_cv = json.load(f)
topics_map = {
    item.get("iptc_subject"): item
    for item in topics_cv.get("items", [])
    if item.get("iptc_subject")
}

# used as fallback in case the code is not found
topics_by_name = {
    item.get("name"): item
    for item in topics_cv.get("items", [])
    if item.get("iptc_subject")
}


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
        {"qcode": DefaultCategory.code, "name": DefaultCategory.name}
    ]
    updates["sttversion"] = "Pika+"


def update_subject(item, updates):
    """Update subject by mapping sttsubj to Media topics CV."""

    subject = item.get("subject", [])
    new_subjects = [entry for entry in subject if entry.get("scheme") != "sttsubj"]

    for entry in subject:
        if entry.get("scheme") == "sttsubj":
            code = entry.get("code")
            name = entry.get("name")
            topic = topics_map.get(code) or topics_by_name.get(name)

            if topic:
                new_subjects.append(
                    {
                        "code": topic.get("qcode"),
                        "name": topic.get("name"),
                        "scheme": "sttsubj", # NOTE: should it be something else?
                    }
                )
            else:
                print(f"Topic not found for '{name}' and code '{code}'.")
                new_subjects.append({"code": code, "name": name, "scheme": "sttsubj"})

    updates["subject"] = new_subjects


def get_category_mapping(item):
    """Extract sttdepartment code and name from subject field or default to `Kotimaa`."""

    subject = item.get("subject", [])
    for entry in subject:
        if entry.get("scheme") == "sttdepartment":
            return {"qcode": entry.get("code"), "name": entry.get("name")}

    return dict(qcode=DefaultCategory.code, name=DefaultCategory.name)


@manager.option("--resources", dest="resources", nargs="+", default=["items", "agenda"])
@manager.option("--limit", dest="limit", type=int, default=500)
@manager.option("--sleep-secs", dest="sleep_secs", type=float, default=2)
@manager.option("--dry-run", dest="dry_run", action="store_true")
@manager.option("-v", "--verbose", dest="verbose", action="store_true")
def remap_stt_metadata(resources, limit, sleep_secs, dry_run, verbose):
    """Remap sttdepartment to anpa_category for Wire and Agenda items in Newsroom."""

    for resource in resources:
        print(f"Processing resource: '{resource}'")
        service = get_resource_service(resource)
        processed = 0

        for item in service.get_all_batch(size=100, max_iterations=10000):
            if limit != 0 and processed >= limit:
                print(f"Reached limit of {limit} items for {resource}.")
                break

            updates = {}
            update_category(item, updates)
            update_subject(item, updates)

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
            if processed % 100 == 0:
                print(".", end="", flush=True)
                time.sleep(sleep_secs)

        print(f"Finished '{resource}'. Total processed: {processed}")

    print("Category remapping completed.")
