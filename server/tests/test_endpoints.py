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
    print(f'{ep.TITLE_EP=}')
    resp_json = resp.get_json()
    print(f'{resp_json=}')
    assert ep.TITLE_RESP in resp_json
    assert isinstance(resp_json[ep.TITLE_RESP], str)
    assert len(resp_json[ep.TITLE_RESP]) > 0


# ------------------------ endpoint for manuscripts -------------------------

# -------- endpoint for create -----------------

MOCK_MANU_ID = ObjectId()
MOCK_HIS_ID = ObjectId()
MOCK_AUTHOR = "John Doe"
MOCK_TITLE = "this is my manuscript"
MOCK_TEXT = "someText"
MOCK_DATE = datetime.now()
MOCK_STATE = 'Submitted'
MOCK_EDITORS_OBJ = {}
MOCK_COMMENTS_OBJ = {}

mock_manuscript = {
    '_id': MOCK_MANU_ID, 
    ms.AUTHOR_NAME: MOCK_AUTHOR, 
    ms.MANUSCRIPT_CREATED: MOCK_DATE, 
    ms.LATEST_VERSION: {
        ms.STATE: MOCK_STATE, 
        ms.TEXT: MOCK_TEXT, 
        ms.TITLE: MOCK_TITLE, 
        ms.EDITORS: MOCK_EDITORS_OBJ, 
        ms.EDITOR_COMMENTS: MOCK_COMMENTS_OBJ
    }, 
    ms.MANUSCRIPT_HISTORY_FK: MOCK_HIS_ID

}


@patch('data.manuscripts.manuscripts.create_manuscript', autospec=True, 
        return_value= {
            "author": MOCK_AUTHOR,
            "latest_version": {
                "title": MOCK_TITLE,
                "text": MOCK_TEXT
             }
        }
)
def test_create_manuscripts(mock_create):
    
    # mock post payload 
    payload = {
        "author": MOCK_AUTHOR,
        "title": MOCK_TITLE,
        "text": MOCK_TEXT
    }

    # Use the test client 
    response = TEST_CLIENT.post("/manuscripts/create", json=payload)

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

@patch('data.manuscripts.manuscripts.create_manuscript', autospec=True, return_value = mock_manuscript)
@patch('data.manuscripts.manuscripts.read_one_manuscript', autospec=True, return_value = mock_manuscript)
def test_read_manuscript_(mock_create_manuscript, mock_read_one_manuscript):
    """
    Test that the GET /manuscripts/<id> endpoint returns the correct manuscript data.
    """
    # Use the patched read_one_manuscript's return value to get the manuscript ID.
    manu_mock_id = str(mock_create_manuscript.return_value['_id'])

    
    # Send a GET request using the test client.
    response = TEST_CLIENT.get(f"/manuscripts/{manu_mock_id}")
    
    # Assert that the response has the expected HTTP status code.
    assert response.status_code == HTTPStatus.OK
    
    # Parse the JSON response.
    data = response.get_json()
    print(data)
    print('resp data', data)
    
    # Verify that the returned data matches our fake manuscript.
    assert data["author"] == MOCK_AUTHOR
    assert data["title"] == MOCK_TITLE
    assert data["text"] == MOCK_TEXT


@patch('data.manuscripts.manuscripts.read_one_manuscript', autospec=True, return_value = None)
def test_read_manuscript_not_found(mock_read):
    """
    Test that the GET /manuscripts/<id> endpoint returns the correct manuscript data.
    """
    dne_mock_id = ObjectId()
    
    # Use the test client (assumed to be available as TEST_CLIENT) to send a GET request.
    response = TEST_CLIENT.get(f"/manuscripts/{dne_mock_id}")
    # Assert that the response has the expected HTTP status code.
    assert response.status_code == NOT_FOUND


@patch('data.manuscripts.manuscripts.create_manuscript', autospec=True, return_value=mock_manuscript)
@patch('data.manuscripts.manuscripts.delete_manuscript', autospec=True, return_value=1)
def test_delete_manuscript_endpoint(mock_delete_manuscript, mock_create_manuscript):

    # Use the create_manuscript patch to retrieve a known manuscript id.
    manuscript = mock_create_manuscript.return_value
    manuscript_id = str(manuscript['_id'])
    
    # Send a DELETE request 
    response = TEST_CLIENT.delete(f"/manuscripts/delete/{manuscript_id}")
    
    # Assert that the response status is HTTP OK.
    assert response.status_code == HTTPStatus.OK
    
    data = response.get_json()
    assert data is not None 
    data = int(data)
    
    # Check that the deletion function indicated success (non-zero value).
    assert data !=0 

@patch('data.manuscripts.manuscripts.delete_manuscript', autospec=True, return_value= 0)
def test_delete_manuscript_endpoint_not_found(mock_create_manuscript):

    # Use the create_manuscript patch to retrieve a known manuscript id.
    dne_id = ObjectId()
    
    # Send a DELETE request 
    response = TEST_CLIENT.delete(f"/manuscripts/delete/{dne_id}")
    
    # Assert that the response status is HTTP OK.
    assert response.status_code == HTTPStatus.OK
    
    data = response.get_json()
    assert data is not None 
    data = int(data)
    
    # Check that the deletion function indicated success (non-zero value).
    assert data == 0 


# ------------------------ endpoint for people -------------------------
@patch('data.people.read', autospec=True,
       return_value={'id': {NAME: 'Joe Schmoe'}})
def test_read(mock_read):
    resp = TEST_CLIENT.get(ep.PEOPLE_EP)
    assert resp.status_code == OK
    resp_json = resp.get_json()
    for _id, person in resp_json.items():
        assert isinstance(_id, str)
        assert len(_id) > 0
        assert NAME in person


@patch('data.people.read_one', autospec=True,
       return_value={NAME: 'Joe Schmoe'})
def test_read_one(mock_read):
    resp = TEST_CLIENT.get(f'{ep.PEOPLE_EP}/mock_id')
    assert resp.status_code == OK


@patch('data.people.read_one', autospec=True, return_value=None)
def test_read_one_not_found(mock_read):
    resp = TEST_CLIENT.get(f'{ep.PEOPLE_EP}/mock_id')
    assert resp.status_code == NOT_FOUND


@patch('data.people.create', autospec=True,
       return_value='testing@nyu.edu')
@patch('data.people.delete', autospec=True,
       return_value='testing@nyu.edu')
def test_delete_person(mock_create, mock_delete):
    test_user = {
        "name": "John Doe",
        "email": "testing@nyu.edu",
        "affiliation": "Columbia",
        "roles": "ED"
    }

    # Create
    resp = TEST_CLIENT.put(f'{ep.PEOPLE_EP}/create', json=test_user)
    assert resp.status_code == OK

    # Delete
    resp = TEST_CLIENT.delete(f'{ep.PEOPLE_EP}/{test_user["email"]}')
    assert resp.status_code == OK

    resp_json = resp.get_json()
    assert resp_json == {'Deleted': test_user["email"]}




# --------------------- endpoint for TEXT _______________________
@patch('data.text.create', autospec=True)
def test_text_create(mock_create):
    """
    Test the PUT endpoint to create a text entry.
    """
    # Input payload for creation.
    payload = {
        "key": "testkey",
        "title": "Test Title",
        "text": "Test text"
    }
    
    # Configure the mock to return the same payload.
    mock_create.return_value = {
        "key": payload["key"],
        "title": payload["title"],
        "text": payload["text"]
    }
    
    # Send PUT request to the TEXT_CREATE_EP endpoint.
    resp = TEST_CLIENT.put(ep.TEXT_CREATE_EP, json=payload)
    
    # Expect a 200 OK (or HTTPStatus.OK) response.
    assert resp.status_code == HTTPStatus.OK
    
    # Parse the JSON response.
    data = resp.get_json()
    assert data["key"] == payload["key"]
    assert data["title"] == payload["title"]
    assert data["text"] == payload["text"]


@patch('data.text.read_one', autospec=True, return_value={
    'title': 'Home Page',
    'text': 'Sample content for testing.'
})
def test_text_read_one(mock_read):
    resp = TEST_CLIENT.get(f'/text/HomePage')
    assert resp.status_code == OK
    resp_json = resp.get_json()
    print(resp_json)
    assert 'title' in resp_json
    assert 'text' in resp_json
    assert resp_json['title'] == 'Home Page'
    assert resp_json['text'] == 'Sample content for testing.'
    pass
