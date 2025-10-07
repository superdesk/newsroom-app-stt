import time
import json
import click

from pathlib import Path

from superdesk import json_utils

from newsroom.commands.cli import newsroom_cli
from newsroom.core import get_current_wsgi_app


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
topics_by_name = {item.get("name"): item for item in topics_cv.get("items", [])}


def reset_service(item, updates):
    """Clear all service field values, including those with name: 'Australian General News'."""

    if item.get("service"):
        updates["service"] = []


def remap_sttdepartment_to_service(item, updates):
    """
    Map 'sttdepartment' entries in the subject list to the 'service' field.
    If no 'sttdepartment' is found, set a default service value.
    Also sets the 'sttversion' field to 'Pika+'.
    """

    subject = item.get("subject", [])
    for entry in subject:
        if entry.get("scheme") == "sttdepartment":
            updates["service"] = [
                {"code": entry.get("code"), "name": entry.get("name")}
            ]
            return

    updates["service"] = [
        {"code": DEFAULT_CATEGORY_CODE, "name": DEFAULT_CATEGORY_NAME}
    ]
    updates["sttversion"] = "Pika+"


def remap_subject(item, updates, not_found):
    """
    - Update subject by mapping sttsubj to media topics.
    - Removes any entry with scheme 'sttdepartment' as it was mapped to 'service'.
    """

    subject = item.get("subject", [])
    new_subjects = [
        entry
        for entry in subject
        if entry.get("scheme") not in ["sttsubj", "sttdepartment"]
    ]

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
                        "scheme": "topics",
                    }
                )
            else:
                not_found.add(code)
                new_subjects.append({"code": code, "name": name, "scheme": "topics"})

    updates["subject"] = new_subjects


def update_language(item, updates, resource):
    """Update the language field for Wire and Agenda items in Newsroom for STT metadata."""

    headline = (item.get("headline") or "").lower()
    new_language = "fi"

    if resource == "items" and (
        headline.endswith("***translated***")
        or "news in brief" in headline
        or "news bulletin" in headline
    ):
        new_language = "en"

    updates["language"] = new_language


def get_service_instance(resource):
    app = get_current_wsgi_app()
    return app.async_app.resources.get_resource_service(resource)


@newsroom_cli.command("remap_stt_metadata")
@click.option(
    "--resources",
    multiple=True,
    default=["items", "agenda"],
    show_default=True,
    help="List of resources to process (can specify multiple times)",
)
@click.option(
    "--limit",
    default=1000,
    show_default=True,
    type=int,
    help="Maximum number of items to process per resource (0 for unlimited)",
)
@click.option(
    "--sleep-secs",
    default=2.0,
    show_default=True,
    type=float,
    help="Seconds to sleep between batches",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Run in dry mode (no changes will be made)",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Enable verbose output",
)
@click.option(
    "--query",
    type=str,
    help="JSON query to filter items (will be passed as lookup parameter)",
)
async def remap_stt_metadata(
    resources, limit, sleep_secs, dry_run, verbose, query=None
):
    """
    Remap STT metadata fields for Wire and Agenda items in Newsroom.

    This command updates items by:
      - Mapping 'sttdepartment' to 'service'
      - Mapping 'sttsubj' to Media Topics controlled vocabulary
      - Updating priority based on 'stturgency' codes for planning items
      - Remapping the language field for STT metadata (fi/en)

    Supports dry-run mode, resource selection, batch processing, and verbosity.
    Query parameter can be used to filter items using MongoDB query syntax.
    If datetime fields are included in `query`, these should be in the same format
    as `DATE_FORMAT` setting.
    """

    await remap_stt_metadata_handler(
        resources, limit, sleep_secs, dry_run, verbose, query
    )


async def remap_stt_metadata_handler(
    resources, limit, sleep_secs, dry_run, verbose, query=None
):
    """Handler function to remap STT metadata fields."""

    BATCH_SIZE = 500
    topics_not_found = set()

    # If resources is a tuple (from click), convert to list for compatibility
    if isinstance(resources, tuple):
        resources = list(resources)

    lookup = json_utils.loads(query) if query else None

    for resource in resources:
        print(f"Processing resource: '{resource}'")
        service = get_service_instance(resource)
        processed = 0

        async for item in service.get_all_batch(
            size=BATCH_SIZE,
            max_iterations=10000,
            lookup=lookup,
        ):
            item = item.to_dict()
            if limit != 0 and processed >= limit:
                print(f"Reached limit of {limit} items for {resource}.")
                break

            updates = {}
            reset_service(item, updates)
            remap_sttdepartment_to_service(item, updates)
            remap_subject(item, updates, topics_not_found)
            update_language(item, updates, resource)

            if not updates:
                continue

            prefix = "DRY RUN: " if dry_run else ""
            msg = f"{prefix}Updating {resource} item '{item['_id']}'"
            if verbose:
                msg += f" with {updates}"
            print(msg)

            if not dry_run:
                await service.system_update(item["_id"], updates)

            processed += 1

            # sleep after each batch
            if processed % BATCH_SIZE == 0:
                print(".", end="", flush=True)
                time.sleep(sleep_secs)

        if verbose:
            print(f"Topics not found: {topics_not_found}")

        print(f"Finished '{resource}'. Total processed: {processed}")

    print("Metadata and language remapping completed.")
