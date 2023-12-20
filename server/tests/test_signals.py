
from stt.signals import publish_planning, set_planning_all_day


def test_publish_planning_signal():
    publish_planning.connect(set_planning_all_day)
    item = {"dates": {"start": 1, "end": 1}}
    publish_planning.send(None, item=item, foo=1)
    assert item["dates"]["all_day"] is True
