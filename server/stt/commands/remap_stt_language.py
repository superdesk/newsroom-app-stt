import time

from superdesk import get_resource_service
from newsroom.commands.manager import manager


@manager.option("--resources", dest="resources", nargs="+", default=["items", "agenda"])
@manager.option(
    "--limit", dest="limit", type=int, default=500, help="Pass 0 for unlimited"
)
@manager.option(
    "--sleep-secs", dest="sleep_secs", type=float, default=2, help="Default: 2 seconds"
)
@manager.option("--dry-run", dest="dry_run", action="store_true")
def remap_stt_language(resources, limit, sleep_secs, dry_run):
    """
    Remap the language field for Wire and Agenda items in Newsroom for STT metadata.
    """

    BATCH_SIZE = 100

    for resource in resources:
        print(f"Processing resource: {resource}")
        service = get_resource_service(resource)
        processed = 0

        for item in service.get_all_batch(size=BATCH_SIZE, max_iterations=10000):
            if limit != 0 and processed >= limit:
                print(f"Reached limit of {limit} items for {resource}.")
                break

            headline = (item.get("headline") or "").lower()
            new_language = "fi"

            if resource == "items" and (
                headline.endswith("***translated***")
                or "news in brief" in headline
                or "news bulletin" in headline
            ):
                new_language = "en"

            updates = {"language": new_language}

            prefix = "DRY RUN: " if dry_run else ""
            print(
                f"{prefix}Updating {resource} item '{item['_id']}' with language: {new_language}"
            )

            if not dry_run:
                service.system_update(item["_id"], updates, item)

            processed += 1

            # sleep after each batch
            if processed % BATCH_SIZE == 0:
                print(".", end="", flush=True)
                time.sleep(sleep_secs)

    print("Language remapping completed.")
