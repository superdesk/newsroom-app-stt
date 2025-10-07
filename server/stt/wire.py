from superdesk.core.app import SuperdeskAsyncApp
from superdesk.core.resources import fields

from newsroom.types import WireItem
from newsroom.wire.module import (
    module,
    wire_items_resource_config,
    init_module as init_wire_module,
)

__all__ = ["module", "STTWireItem"]


class STTWireItem(WireItem):
    sttdepartment: fields.Keyword | None = None
    sttversion: fields.Keyword | None = None
    sttgenre: fields.Keyword | None = None
    sttdone1: fields.Keyword | None = None


def init_module(app: SuperdeskAsyncApp) -> None:
    init_wire_module(app)
    # TODO-ASYNC: Fix hack needed to get around extending existing resource
    WireItem.model_resource_name = STTWireItem.model_resource_name


wire_items_resource_config.data_class = STTWireItem
module.init = init_module
