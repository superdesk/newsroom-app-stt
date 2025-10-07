from typing import Any
from copy import copy

from eve_elastic.elastic import parse_date

from newsroom.signals import publish_item

from .wire import STTWireItem


STT_NESTED_FIELDS = ["sttdepartment", "sttversion"]
STT_ROOT_FIELDS = ["sttgenre", "sttdone1"]
STT_FIELDS = STT_NESTED_FIELDS + STT_ROOT_FIELDS


async def get_previous_version(guid: str, version: str) -> STTWireItem | None:
    service = STTWireItem.get_service()
    for i in range(int(version) - 1, 1, -1):
        version_id = "{}:{}".format(guid, i)
        original = await service.find_by_id(version_id)
        if original:
            return original

    return await service.find_by_id(guid)


async def on_publish_item(item: dict[str, Any], is_new: bool) -> None:
    """Populate stt department and version fields."""
    if item.get("subject"):
        for subject in item["subject"]:
            if subject.get("scheme", "") in STT_FIELDS:
                item[subject["scheme"]] = subject.get("name", subject.get("code"))
        item["subject"] = [
            subject
            for subject in item["subject"]
            if subject.get("scheme") != "sttdone1"
        ]

    # add private note to ednote
    if item.get("extra", {}).get("sttnote_private"):
        if item.get("ednote"):
            item["ednote"] = "{}\n{}".format(
                item["ednote"], item["extra"]["sttnote_private"]
            )
        else:
            item["ednote"] = item["extra"]["sttnote_private"]

    # set versioncreated for archive items
    if item.get("firstpublished") and is_new:
        if isinstance(item.get("firstpublished"), str):
            firstpublished = parse_date(item["firstpublished"])
        else:
            firstpublished = item["firstpublished"]

        if firstpublished < item["versioncreated"]:
            item["versioncreated"] = firstpublished

    # link the previous versions and update the id of the story
    if not is_new and "evolvedfrom" not in item:
        original = await get_previous_version(item["guid"], item["version"])

        if original:
            if original.version == item["version"]:
                # the same version of the story been sent again so no need to create new version
                return

            service = STTWireItem.get_service()
            new_id = "{}:{}".format(item["guid"], item["version"])
            await service.system_update(original.id, {"nextversion": new_id})
            item["guid"] = new_id

            item["ancestors"] = copy(original.ancestors or []) + [original.id]
            item["bookmarks"] = original.bookmarks or []

    # dump abstract
    for field in ("description_html", "description_text"):
        item.pop(field, None)


def init_app(app):
    publish_item.connect(on_publish_item)
