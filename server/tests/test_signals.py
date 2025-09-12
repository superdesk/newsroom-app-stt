from stt.signals import publish_planning, set_planning_all_day


async def test_publish_planning_signal():
    publish_planning.connect(set_planning_all_day)
    item = {"dates": {"start": 1, "end": 1}}
    await publish_planning.send(item, False)
    assert item["dates"]["all_day"] is True
