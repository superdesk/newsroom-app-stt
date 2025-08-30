import pytest

import stt.commands.remap_stt_language as mod_lang

from . import FakeService


@pytest.fixture
def monkey_service(monkeypatch):
    """Patch get_resource_service to return a FakeService per resource label."""
    services = {}

    def _factory(resource):
        return services[resource]

    monkeypatch.setattr(mod_lang, "get_resource_service", _factory)
    return services


def test_language_rules_items_exceptions_and_default(monkey_service):
    # items: special cases + default
    items = [
        {"_id": "a1", "headline": "Something ***TRANSLATED***", "language": "fi"},
        {"_id": "a2", "headline": "NEWS BULLETIN: Update", "language": "fi"},
        {"_id": "a3", "headline": "Regular Finnish story", "language": "en"},
    ]
    svc_items = FakeService(items)
    monkey_service["items"] = svc_items

    # agenda: even if headline matches, exceptions only apply to items
    agenda = [
        {"_id": "p1", "headline": "Something ***TRANSLATED***", "language": "en"},
        {"_id": "p2", "headline": "Normal planning", "language": "en"},
    ]
    svc_agenda = FakeService(agenda)
    monkey_service["agenda"] = svc_agenda

    # Run: process both resources, apply updates (dry_run=False)
    mod_lang.remap_stt_language(
        resources=["items", "agenda"], limit=0, sleep_secs=0, dry_run=False
    )

    # items: a1,a2 -> en; a3 -> fi
    assert svc_items._items["a1"]["language"] == "en"
    assert svc_items._items["a2"]["language"] == "en"
    assert svc_items._items["a3"]["language"] == "fi"

    # agenda: defaults to fi (no items-only exceptions)
    assert svc_agenda._items["p1"]["language"] == "fi"
    assert svc_agenda._items["p2"]["language"] == "fi"


def test_language_limit_stops_processing(monkey_service):
    items = [{"_id": f"x{i}", "headline": "post", "language": "en"} for i in range(5)]
    svc_items = FakeService(items)
    monkey_service["items"] = svc_items

    # Limit = 2 should only update first two docs
    mod_lang.remap_stt_language(
        resources=["items"], limit=2, sleep_secs=0, dry_run=False
    )

    updated = [doc for doc in svc_items._items.values() if doc["language"] == "fi"]
    assert len(updated) == 2
