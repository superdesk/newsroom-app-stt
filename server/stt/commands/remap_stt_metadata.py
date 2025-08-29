import time

from dataclasses import dataclass
from superdesk import get_resource_service
from newsroom.commands.manager import manager


@dataclass(frozen=True)
class DefaultCategory:
    code: str = "3"  # NOTE: is 3 always for `Kotimaa` category?
    name: str = "Kotimaa"


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
def remap_stt_metadata(resources, limit, sleep_secs, dry_run):
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
            category = get_category_mapping(item)
            updates["anpa_category"] = [category]

            if category.get("name") == DefaultCategory.name:
                updates["sttversion"] = "Pika+"

            if dry_run:
                print(f"Would update {resource} item {item['_id']} with {updates}")
            else:
                print(f"Updating {resource} item {item['_id']} with {updates}")
                service.system_update(item["_id"], updates, item)

            processed += 1

            # sleep after each batch
            if processed % 100 == 0:
                print(".", end="", flush=True)
                time.sleep(sleep_secs)

        print(f"Finished '{resource}'. Total processed: {processed}")

    print("Category remapping completed.")
