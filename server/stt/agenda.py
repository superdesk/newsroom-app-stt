from superdesk.core.module import Module, SuperdeskAsyncApp
from newsroom.agenda.filters import PRIVATE_FIELDS


def init_module(app: SuperdeskAsyncApp):
    if "coverages.scheduled" not in PRIVATE_FIELDS:
        PRIVATE_FIELDS.extend([
            "coverages.scheduled",
            "planning_items.coverages.planning.scheduled",
        ])

module = Module(name="stt.agenda", init=init_module)
