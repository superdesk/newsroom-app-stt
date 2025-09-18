import sys
import superdesk

from superdesk.resource import Resource


class UiConfigWorkaround(Resource):
    endpoint_name = "ui_config"


def init_app(app) -> None:
    # temporal workaround to register ui_config resource before initialize_data command
    # as the new UI Config works async and the `initialize_data` command is not async compatible yet
    if len(sys.argv) > 1 and sys.argv[1] == "initialize_data":
        superdesk.register_resource(
            "ui_config", UiConfigWorkaround, superdesk.Service, _app=app
        )
