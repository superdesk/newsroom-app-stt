class _DictWrapper:
    def __init__(self, d):
        self._d = d

    def to_dict(self):
        return self._d


class FakeService:
    """FakeService is a mock resource service for testing.

    - Stores items in a dict keyed by '_id' for efficient lookup and update.
    - Provides batch retrieval via get_all_batch().
    - Supports updating items with system_update().
    """

    def __init__(self, items):
        # store by _id for easier updates
        self._items = {i["_id"]: i for i in items}

    async def get_all_batch(self, size=100, max_iterations=10000, lookup=None):
        # simple paginator over current values, now async
        items = list(self._items.values())
        for i in range(0, min(len(items), size * max_iterations), size):
            for item in items[i : i + size]:  # noqa
                yield _DictWrapper(item)

    async def system_update(self, _id, updates):
        self._items[_id].update(updates)
