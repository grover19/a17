from http.client import (
    BAD_REQUEST,
    FORBIDDEN,
    NOT_ACCEPTABLE,
    NOT_FOUND,
    OK,
    SERVICE_UNAVAILABLE,
)

from unittest.mock import patch
from http import HTTPStatus
import pytest

from data.people import NAME
import data.manuscripts.manuscripts as ms

import server.endpoints as ep
from datetime import datetime

from bson.objectid import ObjectId


TEST_CLIENT = ep.app.test_client()


def test_hello():
    resp = TEST_CLIENT.get(ep.HELLO_EP)
    resp_json = resp.get_json()
    assert ep.HELLO_RESP in resp_json


def test_title():
    resp = TEST_CLIENT.get(ep.TITLE_EP)
    print(f"{ep.TITLE_EP=}")
    resp_json = resp.get_json()
    print(f"{resp_json=}")
    assert ep.TITLE_RESP in resp_json
    assert isinstance(resp_json[ep.TITLE_RESP], str)
    assert len(resp_json[ep.TITLE_RESP]) > 0


@patch("data.people.read", autospec=True, return_value={"id": {NAME: "Joe Schmoe"}})
def test_read(mock_read):
    resp = TEST_CLIENT.get(ep.PEOPLE_EP)
    assert resp.status_code == OK
    resp_json = resp.get_json()
    for _id, person in resp_json.items():
        assert isinstance(_id, str)
        assert len(_id) > 0
        assert NAME in person


@patch("data.people.read_one", autospec=True, return_value={NAME: "Joe Schmoe"})
def test_read_one(mock_read):
    resp = TEST_CLIENT.get(f"{ep.PEOPLE_EP}/mock_id")
    assert resp.status_code == OK


@patch("data.people.read_one", autospec=True, return_value=None)
def test_read_one_not_found(mock_read):
    resp = TEST_CLIENT.get(f"{ep.PEOPLE_EP}/mock_id")
    assert resp.status_code == NOT_FOUND


@patch("data.people.create", autospec=True, return_value="testing@nyu.edu")
@patch("data.people.delete", autospec=True, return_value="testing@nyu.edu")
def test_delete_person_success(mock_create, mock_delete):
    test_user = {
        "name": "John Doe",
        "email": "testing@nyu.edu",
        "affiliation": "Columbia",
        "roles": "ED",
    }

    # Create
    resp = TEST_CLIENT.put(f"{ep.PEOPLE_EP}/create", json=test_user)
    assert resp.status_code == OK

    # Delete
    resp = TEST_CLIENT.delete(f'{ep.PEOPLE_EP}/{test_user["email"]}')
    assert resp.status_code == OK

    resp_json = resp.get_json()
    assert resp_json == {"Deleted": test_user["email"]}


@patch(
    "data.text.read_one",
    autospec=True,
    return_value={"title": "Home Page", "text": "Sample content for testing."},
)
def test_text_read_one(mock_read):
    resp = TEST_CLIENT.get(f"/text/HomePage")
    assert resp.status_code == OK
    resp_json = resp.get_json()
    print(resp_json)
    assert "title" in resp_json
    assert "text" in resp_json
    assert resp_json["title"] == "Home Page"
    assert resp_json["text"] == "Sample content for testing."


# ------------------------ endpoint for manuscripts -------------------------

# -------- endpoint for create -----------------

MOCK_MANU_ID = ObjectId()
MOCK_HIS_ID = ObjectId()
MOCK_AUTHOR = "John Doe"
MOCK_TITLE = "this is my manuscript"
MOCK_TEXT = "someText"
MOCK_DATE = datetime.now()
MOCK_STATE = "Submitted"
MOCK_EDITORS_OBJ = {}
MOCK_COMMENTS_OBJ = {}

mock_manuscript = {
    "_id": MOCK_MANU_ID,
    ms.AUTHOR_NAME: MOCK_AUTHOR,
    ms.MANUSCRIPT_CREATED: MOCK_DATE,
    ms.LATEST_VERSION: {
        ms.STATE: MOCK_STATE,
        ms.TEXT: MOCK_TEXT,
        ms.TITLE: MOCK_TITLE,
        ms.EDITORS: MOCK_EDITORS_OBJ,
        ms.EDITOR_COMMENTS: MOCK_COMMENTS_OBJ,
    },
    ms.MANUSCRIPT_HISTORY_FK: MOCK_HIS_ID,
}


@patch(
    "data.manuscripts.manuscripts.create_manuscript",
    autospec=True,
    return_value={
        "author": MOCK_AUTHOR,
        "latest_version": {"title": MOCK_TITLE, "text": MOCK_TEXT},
    },
)
def test_create_manuscripts(mock_create):
    # mock post payload
    payload = {"author": MOCK_AUTHOR, "title": MOCK_TITLE, "text": MOCK_TEXT}

    # Use the test client
    response = TEST_CLIENT.put("/manuscripts/create", json=payload)

    # Verify that the response status code is as expected.
    assert response.status_code in (HTTPStatus.CREATED, HTTPStatus.OK)

    # Parse the JSON response.
    data = response.get_json()

    # Verify that the returned data matches expectations
    assert data["author"] == MOCK_AUTHOR
    assert data["title"] == MOCK_TITLE
    assert data["text"] == MOCK_TEXT

    # Optionally, print the response for debugging.
    print(data)


# ------------- endpoint for GET -----------------


@patch(
    "data.manuscripts.manuscripts.create_manuscript",
    autospec=True,
    return_value=mock_manuscript,
)
@patch(
    "data.manuscripts.manuscripts.read_one_manuscript",
    autospec=True,
    return_value=mock_manuscript,
)
def test_read_manuscript_(mock_create_manuscript, mock_read_one_manuscript):
    """
    Test that the GET /manuscripts/<id> endpoint returns the correct manuscript data.
    """
    # Use the patched read_one_manuscript's return value to get the manuscript
    # ID.
    manu_mock_id = str(mock_create_manuscript.return_value["_id"])

    # Send a GET request using the test client.
    response = TEST_CLIENT.get(f"/manuscripts/{manu_mock_id}")

    # Assert that the response has the expected HTTP status code.
    assert response.status_code == HTTPStatus.OK

    # Parse the JSON response.
    data = response.get_json()
    print(data)
    print("resp data", data)

    # Verify that the returned data matches our fake manuscript.
    assert data["author"] == MOCK_AUTHOR
    assert data["title"] == MOCK_TITLE
    assert data["text"] == MOCK_TEXT


@patch(
    "data.manuscripts.manuscripts.read_one_manuscript", autospec=True, return_value=None
)
def test_read_manuscript_not_found(mock_read):
    """
    Test that the GET /manuscripts/<id> endpoint returns the correct manuscript data.
    """
    dne_mock_id = ObjectId()

    # Use the test client (assumed to be available as TEST_CLIENT) to send a
    # GET request.
    response = TEST_CLIENT.get(f"/manuscripts/{dne_mock_id}")
    # Assert that the response has the expected HTTP status code.
    assert response.status_code == NOT_FOUND


@patch("data.manuscripts.manuscripts.create_manuscript", autospec=True, return_value=mock_manuscript)
@patch("data.manuscripts.manuscripts.delete_manuscript", autospec=True, return_value=1)
def test_delete_manuscript_success(mock_delete, mock_create):
    mock_id = str(ObjectId())

    response = TEST_CLIENT.delete(ep.MANUSCRIPTS_DEL_EP.replace("<id>", mock_id))
    assert response.status_code == HTTPStatus.OK

    resp_json = response.get_json()
    assert resp_json == {"message": f"Manuscript with ID {mock_id} deleted."}


@patch("data.manuscripts.manuscripts.delete_manuscript", autospec=True, return_value=0)
def test_delete_manuscript_not_found(mock_delete):
    mock_id = str(ObjectId())

    response = TEST_CLIENT.delete(ep.MANUSCRIPTS_DEL_EP.replace("<id>", mock_id))
    assert response.status_code == HTTPStatus.NOT_FOUND

    resp_json = response.get_json()
    assert "No manuscript found with ID" in resp_json["message"]


@patch("data.manuscripts.manuscripts.transition_manuscript_state", autospec=True, return_value="REV")
def test_receive_action_success(mock_transition):
    payload = {
        "id": str(ObjectId()),
        "action": "ARF",
        "ref": "reviewer@example.com"
    }

    resp = TEST_CLIENT.post("/manuscripts/receive_action", json=payload)
    assert resp.status_code == HTTPStatus.OK

    resp_json = resp.get_json()
    assert resp_json["state"] == "REV"
    assert f"Manuscript transitioned to {resp_json['state']}" in resp_json["message"]
    mock_transition.assert_called_once_with(
        payload["id"],
        payload["action"],
        ref=payload["ref"],
        target_state=None
    )

@patch("data.manuscripts.manuscripts.transition_manuscript_state", autospec=True, return_value="PUB")
def test_editor_move_action_success(mock_transition):
    payload = {
        "id": str(ObjectId()),
        "action": "EDITOR_MOVE",
        "target_state": "PUB"
    }

    resp = TEST_CLIENT.post("/manuscripts/receive_action", json=payload)
    assert resp.status_code == HTTPStatus.OK

    data = resp.get_json()
    assert "state" in data
    assert data["state"] == "PUB"
    assert f"Manuscript transitioned to {data['state']}" in data["message"]

    mock_transition.assert_called_once_with(payload["id"], payload["action"], ref=None, target_state="PUB")


@patch("data.text.update", autospec=True)
def test_update_text(mock_update):
    payload = {
        "key": "HomePage",
        "title": "Updated Home Page",
        "text": "Updated content here."
    }

    resp = TEST_CLIENT.post("/text/update", json=payload)
    assert resp.status_code == HTTPStatus.OK

    resp_json = resp.get_json()
    assert resp_json == {
        "message": "Text updated successfully",
        "key": payload["key"]
    }

    mock_update.assert_called_once_with(payload["key"], payload["title"], payload["text"])


@patch("data.manuscripts.manuscripts.create_manuscript", autospec=True)
@patch("data.manuscripts.manuscripts.read_one_manuscript", autospec=True)
def test_get_valid_actions(mock_read, mock_create):
    mock_id = ObjectId()
    mock_manu = {
        "_id": mock_id,
        "author": "Tester",
        "latest_version": {
            "state": "SUB",
            "title": "Valid Actions Test",
            "text": "Some text",
            "referees": [],
            "editors": {},
            "comments": {}
        },
        "manuscript_created": "2025-04-30 00:00:00",
        "manuscript_history_fk": ObjectId()
    }

    mock_read.return_value = mock_manu
    mock_create.return_value = mock_manu
    manu_id = str(mock_id)

    resp = TEST_CLIENT.get(f"/manuscripts/{manu_id}/valid_actions")
    assert resp.status_code == HTTPStatus.OK

    data = resp.get_json()
    assert "current_state" in data
    assert "valid_actions" in data
    assert isinstance(data["valid_actions"], list)


@patch("security.security.read", autospec=True, return_value={"people": {"create": {}}})
def test_read_security_settings(mock_read):
    response = TEST_CLIENT.get("/security")
    assert response.status_code == HTTPStatus.OK

    resp_json = response.get_json()
    assert "people" in resp_json
    assert "create" in resp_json["people"]


@patch("security.security.is_permitted", autospec=True, return_value=True)
def test_security_permission_check_allowed(mock_is_permitted):
    payload = {
        "feature_name": "people",
        "action": "create",
        "user_id": "ejc369@nyu.edu"
    }
    response = TEST_CLIENT.post("/security/check", json=payload)
    assert response.status_code == HTTPStatus.OK
    resp_json = response.get_json()
    assert resp_json["message"] == "User has permission."


@patch("security.security.is_permitted", autospec=True, return_value=False)
def test_security_permission_check_denied(mock_is_permitted):
    payload = {
        "feature_name": "people",
        "action": "create",
        "user_id": "unauthorized_user@nyu.edu"
    }
    response = TEST_CLIENT.post("/security/check", json=payload)
    assert response.status_code == HTTPStatus.FORBIDDEN
    resp_json = response.get_json()
    assert resp_json["message"] == "User does not have permission."
