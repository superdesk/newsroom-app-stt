class FakeService:
    """FakeService is a mock resource service for testing.

    - Stores items in a dict keyed by '_id' for efficient lookup and update.
    - Provides batch retrieval via get_all_batch().
    - Supports updating items with system_update().
    """

    def __init__(self, items):
        # store by _id for easier updates
        self._items = {i["_id"]: i for i in items}

    def get_all_batch(self, size=100, max_iterations=10000):
        # simple paginator over current values
        items = list(self._items.values())
        for i in range(0, min(len(items), size * max_iterations), size):
            yield from items[i:i + size]

    def system_update(self, _id, updates, original):
        self._items[_id].update(updates)
