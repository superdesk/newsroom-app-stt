from typing import Any

from newsroom.signals import publish_planning


def set_planning_all_day(item: dict[str, Any], is_new: bool) -> None:
    item["dates"].setdefault("all_day", True)


def init_app(app):
    publish_planning.connect(set_planning_all_day)
