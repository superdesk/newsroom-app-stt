from superdesk import get_resource_service
from newsroom.commands.manager import manager

from .utils import iterate_items


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

    for resource in resources:
        print(f"Processing resource: {resource}")
        service = get_resource_service(resource)

        for item in iterate_items(resource, limit, sleep_secs):
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

    print("Language remapping completed.")
