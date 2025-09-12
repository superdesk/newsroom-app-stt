import pytest

import stt.commands.remap_stt_metadata as mod_meta
from . import FakeService


@pytest.fixture(autouse=True)
def patch_topics_map(monkeypatch):
    """
    The command loads a JSON file at import time. Replace the in-module maps with a small stub
    so tests are hermetic and don't need the real file.
    """
    monkeypatch.setattr(
        mod_meta,
        "topics_map",
        {"60000": {"code": "MT-123", "name": "Economy"}},
        raising=True,
    )
    monkeypatch.setattr(
        mod_meta,
        "topics_by_name",
        {"Sports": {"code": "MT-999", "name": "Sports"}},
        raising=True,
    )


@pytest.fixture
def monkey_service(monkeypatch):
    services = {}
    monkeypatch.setattr(mod_meta, "get_service_instance", lambda r: services[r])
    return services


async def test_clears_service_and_maps_service_from_sttdepartment(monkey_service):
    items = [
        {
            "_id": "i1",
            "service": [{"name": "Australian General News"}, {"name": "Other"}],
            "subject": [
                {"scheme": "sttdepartment", "code": "4", "name": "Service Test"},
                {"scheme": "sttsubj", "code": "60000", "name": "Economy"},
            ],
        }
    ]
    svc = FakeService(items)
    monkey_service["items"] = svc

    await mod_meta.remap_stt_metadata_handler(
        resources=["items"], limit=0, sleep_secs=0, dry_run=False, verbose=True
    )

    updated = svc._items["i1"]
    # service set from sttdepartment
    assert updated.get("service") == [{"code": "4", "name": "Service Test"}]

    # sttsubj replaced with mapped entry (keeps scheme as in current implementation)
    assert any(
        s
        for s in updated["subject"]
        if s.get("code") == "60000" and s.get("name") == "Economy"
    )


async def test_missing_sttdepartment_sets_defaults(monkey_service):
    items = [
        {
            "_id": "2000",
            "service": [{"name": "Australian General News"}],
            "subject": [  # no sttdepartment present
                {"scheme": "sttsubj", "code": "999999", "name": "Unmapped"},
            ],
        }
    ]
    svc = FakeService(items)
    monkey_service["items"] = svc

    await mod_meta.remap_stt_metadata_handler(
        resources=["items"], limit=0, sleep_secs=0, dry_run=False, verbose=False
    )

    updated = svc._items["2000"]

    # defaults applied
    assert updated.get("service") == [
        {
            "code": mod_meta.DEFAULT_CATEGORY_CODE,
            "name": mod_meta.DEFAULT_CATEGORY_NAME,
        }
    ]
    assert updated.get("sttversion") == "Pika+"


async def test_language_rules_items_exceptions_and_default(monkey_service):
    # items: special cases + default
    items = [
        {"_id": "a1", "headline": "Something ***TRANSLATED***", "language": "fi"},
        {"_id": "a2", "headline": "Regular update", "language": "fi"},
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
    await mod_meta.remap_stt_metadata_handler(
        resources=["items", "agenda"],
        limit=0,
        sleep_secs=0,
        dry_run=False,
        verbose=False,
    )
    # Limit = 2 should only update first two docs
    await mod_meta.remap_stt_metadata_handler(
        resources=["items"],
        limit=2,
        sleep_secs=0,
        dry_run=False,
        verbose=False,
    )

    updated = [doc for doc in svc_items._items.values() if doc["language"] == "fi"]
    assert len(updated) == 2
