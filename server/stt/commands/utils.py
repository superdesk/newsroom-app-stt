import time
from superdesk import get_resource_service


def iterate_items(resource, limit, sleep_secs):
    """Yield items from a resource in batches, sorted by _created descending."""

    service = get_resource_service(resource)
    source = {
        "query": {"bool": {"must": []}},
        "sort": [{"_created": {"order": "desc"}}],
        "size": 100,
        "from": 0,
    }
    processed = 0

    while True:
        if limit != 0 and processed >= limit:
            print(f"Reached limit of {limit} items for {resource}.")
            break
        items = list(service.search(source))

        if not items:
            print(f"No more items to process in {resource}.")
            break

        for item in items:
            yield item

            processed += 1

        print(".", end="", flush=True)
        source["from"] += source["size"]
        time.sleep(sleep_secs)

    print(f"Finished {resource}. Total processed: {processed}")
