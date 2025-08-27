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
def remap_stt_language(resources, limit, sleep_secs, dry_run=False):
    """
    Remap the language field for Wire and Agenda items in Newsroom for STT metadata.
    """

    print(limit)

    for resource in resources:
        print(f"Processing resource: {resource}")
        service = get_resource_service(resource)
        source = {
            "query": {"bool": {"must": []}},
            "sort": [{"_created": {"order": "desc"}}],
            "size": 100,
            "from": 0,
        }
        processed = 0

        while True:
            # stop if limit is reached and not unlimited (limit != 0)
            if limit != 0 and processed >= limit:
                print(f"Reached limit of {limit} items for {resource}.")
                break

            items = list(service.search(source))
            if not items:
                print(f"No more items to process in {resource}.")
                break

            for item in items:
                headline = (item.get("headline") or "").lower()
                new_language = "fi"

                if resource == "items" and (
                    headline.endswith("***translated***")
                    or "news in brief" in headline
                    or "news bulletin" in headline
                ):
                    new_language = "en"

                updates = {"language": new_language}

                if dry_run:
                    print(
                        f"Would update {resource} item {item['_id']} with language: {new_language}"
                    )
                else:
                    print(
                        f"Updating {resource} item {item['_id']} with language: {new_language}"
                    )
                    service.system_update(item["_id"], updates, item)

                processed += 1

                # check limit after each item to avoid overshooting
                if limit != 0 and processed >= limit:
                    print(f"Reached limit of {limit} items for {resource}.")
                    break

            print(".", end="", flush=True)
            source["from"] += source["size"]
            time.sleep(int(sleep_secs))

        print(f"Finished processing {resource}. Total items processed: {processed}")

    print("Language remapping completed.")
