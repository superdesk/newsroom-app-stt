
from newsroom.signals import publish_planning


def set_planning_all_day(app, item, **kwargs):
    item["dates"].setdefault("all_day", True)


def init_app(app):
    publish_planning.connect(set_planning_all_day)
