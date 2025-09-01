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
        {
            "60000": {"qcode": "MT-123", "name": "Economy"},
        },
        raising=True,
    )
    monkeypatch.setattr(
        mod_meta,
        "topics_by_name",
        {
            "Sports": {"qcode": "MT-999", "name": "Sports"},
        },
        raising=True,
    )


@pytest.fixture
def monkey_service(monkeypatch):
    services = {}
    monkeypatch.setattr(mod_meta, "get_resource_service", lambda r: services[r])
    return services


def test_clears_service_and_maps_anpa_from_sttdepartment(monkey_service):
    items = [
        {
            "_id": "i1",
            "service": [{"name": "Australian General News"}, {"name": "Other"}],
            "subject": [
                {"scheme": "sttdepartment", "code": "3", "name": "Kotimaa"},
                {"scheme": "sttsubj", "code": "60000", "name": "Economy"},
            ],
        }
    ]
    svc = FakeService(items)
    monkey_service["items"] = svc

    mod_meta.remap_stt_metadata(
        resources=["items"], limit=0, sleep_secs=0, dry_run=False, verbose=True
    )

    updated = svc._items["i1"]
    # service cleared
    assert updated.get("service") == []
    # anpa_category set from sttdepartment
    assert updated.get("anpa_category") == [{"qcode": "3", "name": "Kotimaa"}]
    # sttsubj replaced with mapped entry (keeps scheme as in current implementation)
    assert any(
        s
        for s in updated["subject"]
        if s.get("code") == "60000" and s.get("name") == "Economy"
    )


def test_missing_sttdepartment_sets_defaults(monkey_service):
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

    mod_meta.remap_stt_metadata(
        resources=["items"], limit=0, sleep_secs=0, dry_run=False, verbose=False
    )

    updated = svc._items["2000"]
    # service cleared
    assert updated.get("service") == []
    # defaults applied
    assert updated.get("anpa_category") == [
        {
            "qcode": mod_meta.DEFAULT_CATEGORY_CODE,
            "name": mod_meta.DEFAULT_CATEGORY_NAME,
        }
    ]
    assert updated.get("sttversion") == "Pika+"


def test_planning_priority_from_stturgency(monkey_service):
    agenda = [
        {
            "_id": "30000",
            "item_type": "planning",
            "subject": [
                {"scheme": "stturgency", "code": "urgency-2", "name": "Medium"},
            ],
        }
    ]
    svc = FakeService(agenda)
    monkey_service["agenda"] = svc

    mod_meta.remap_stt_metadata(
        resources=["agenda"], limit=0, sleep_secs=0, dry_run=False, verbose=False
    )

    assert svc._items["30000"]["priority"] == 2
