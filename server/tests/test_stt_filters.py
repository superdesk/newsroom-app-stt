import bson
import hmac

from stt.wire import STTWireItem
from stt.filters import init_app


def get_signature_headers(data, key):
    mac = hmac.new(key, data.encode(), "sha1")
    return {"x-superdesk-signature": "sha1=%s" % mac.hexdigest()}


item = {
    "guid": "foo",
    "type": "text",
    "headline": "Foo",
    "firstcreated": "2017-11-27T08:00:57+0000",
    "body_html": "<p>foo bar</p>",
    "renditions": {
        "thumbnail": {
            "href": "http://example.com/foo",
            "media": "foo",
        }
    },
    "genre": [{"name": "News", "code": "news"}],
    "associations": {
        "featured": {
            "type": "picture",
            "renditions": {
                "thumbnail": {
                    "href": "http://example.com/bar",
                    "media": "bar",
                }
            },
        }
    },
    "event_id": "urn:event/1",
    "coverage_id": "urn:coverage/1",
}


async def get_wire_item(guid: str) -> STTWireItem | None:
    return await STTWireItem.get_service().find_by_id(guid)


async def test_push_updates_ednote(client, app):
    init_app(app)
    payload = item.copy()
    payload["ednote"] = "foo"
    await client.post("/push", json=payload)
    parsed = await get_wire_item(item["guid"])
    assert parsed.ednote == "foo"

    payload["guid"] = "bar"
    payload["extra"] = {"sttnote_private": "private message"}
    await client.post("/push", json=payload)
    parsed = await get_wire_item(payload["guid"])
    assert parsed.ednote == "foo\nprivate message"

    payload["guid"] = "baz"
    payload.pop("ednote")
    payload["extra"] = {"sttnote_private": "private message"}
    await client.post("/push", json=payload)
    parsed = await get_wire_item(payload["guid"])
    assert parsed.ednote == "private message"


async def test_push_firstcreated_is_older_copies_to_versioncreated(client, app):
    init_app(app)
    payload = item.copy()
    payload["firstpublished"] = "2017-11-26T08:00:57+0000"
    payload["versioncreated"] = "2017-11-27T08:00:57+0000"
    payload["version"] = "1"
    await client.post("/push", json=payload)
    parsed = await get_wire_item(item["guid"])
    assert parsed.firstpublished == parsed.versioncreated

    # post the same story again as a correction, versioncreated is preserved
    payload["versioncreated"] = "2017-11-28T08:00:57+0000"
    await client.post("/push", json=payload)
    parsed = await get_wire_item(item["guid"])
    assert parsed.firstpublished.strftime("%Y%m%d%H%M") == "201711260800"
    assert parsed.versioncreated.strftime("%Y%m%d%H%M") == "201711280800"


async def test_push_new_versions_will_update_ancestors(client, app):
    init_app(app)
    payload = item.copy()
    payload["version"] = "1"
    await client.post("/push", json=payload)
    parsed = await get_wire_item(item["guid"])
    assert parsed.version == "1"

    bookmarks = [bson.ObjectId()]
    saved = await get_wire_item(item["guid"])
    await STTWireItem.get_service().update(saved.id, {"bookmarks": bookmarks})

    # post the new version of the story, it will update the ancestors
    payload["version"] = "2"
    payload["headline"] = "bar"
    await client.post("/push", json=payload)
    new_story = await get_wire_item("foo:2")
    original_story = await get_wire_item(item["guid"])
    assert new_story.version == "2"
    assert new_story.ancestors == ["foo"]
    assert new_story.headline == "bar"
    assert new_story.bookmarks == bookmarks
    assert original_story.nextversion == "foo:2"

    # post the same version of the story, it will update keep ancestors but update the current story
    payload["headline"] = "baz"
    await client.post("/push", json=payload)
    new_story = await get_wire_item("foo:2")
    original_story = await get_wire_item(item["guid"])
    assert new_story.version == "2"
    assert new_story.ancestors == ["foo"]
    assert new_story.headline == "baz"
    assert new_story.bookmarks == bookmarks
    assert original_story.nextversion == "foo:2"
