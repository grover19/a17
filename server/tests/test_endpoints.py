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
def test_delete_person_success(mock_create, mock_delete):
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


# ------------------------ endpoint for manuscripts -------------------------

# -------- endpoint for create -----------------

# Define the expected values
MOCK_AUTHOR = "John Doe"
MOCK_TITLE = "this is my manuscript"
MOCK_TEXT = "someText"

# This is the fake payload document that our patched create_manuscript will return.
fake_manuscript = {
    "author": MOCK_AUTHOR,
    "latest_version": {
        "title": MOCK_TITLE,
        "text": MOCK_TEXT
    }
}

@patch('data.manuscripts.manuscripts.create_manuscript', autospec=True, return_value=fake_manuscript)
def test_create_manuscripts(mock_create):
    # Build the test payload that simulates the JSON data sent by a client.
    payload = {
        "author": MOCK_AUTHOR,
        "title": MOCK_TITLE,
        "text": MOCK_TEXT
    }

    # Use the test client (assume TEST_CLIENT is your Flask test client) to send a POST request
    response = TEST_CLIENT.post("/manuscripts/create", json=payload)

    # Verify that the response status code is as expected.
    # Depending on your framework settings, this might be HTTPStatus.CREATED (201) or OK (200).
    # Adjust the assertion if needed.
    assert response.status_code in (HTTPStatus.CREATED, HTTPStatus.OK)

    # Parse the JSON response.
    data = response.get_json()

    # Verify that the returned data matches what we expect based on our fake_manuscript.
    assert data["author"] == MOCK_AUTHOR
    assert data["title"] == MOCK_TITLE
    assert data["text"] == MOCK_TEXT

    # Optionally, print the response for debugging.
    print(data)


# ------------- endpoint for GET -----------------
# create a mock db entry 

def create_mock_manuscript(author, title, text):
    return ms.create_manuscript(author, title, text)

def clean_mock_manuscript(mock_manu_id): 
    return ms.delete_manuscript(mock_manu_id)

# Fake manuscript document matching the structure of 
# read_one_maniscript
manu_mock_read = create_mock_manuscript(MOCK_AUTHOR, MOCK_TITLE, MOCK_TEXT)
@patch('data.manuscripts.manuscripts.read_one_manuscript', autospec=True, return_value = manu_mock_read)
def test_read_manuscript_(mock_read):
    """
    Test that the GET /manuscripts/GET/<id> endpoint returns the correct manuscript data.
    """
    manu_mock_id = manu_mock_read['_id']
    
    # Use the test client (assumed to be available as TEST_CLIENT) to send a GET request.
    response = TEST_CLIENT.get(f"/manuscripts/{manu_mock_id}")
    # Assert that the response has the expected HTTP status code.
    assert response.status_code == HTTPStatus.OK
    
    # Parse the JSON response.
    data = response.get_json()
    print('resp data', data)
    
    # Verify that the returned data matches our fake manuscript.
    assert data["author"] == MOCK_AUTHOR
    assert data["title"] == MOCK_TITLE
    assert data["text"] == MOCK_TEXT

    clean_mock_manuscript(manu_mock_id)


# @patch('data.manuscripts.manuscripts.read_one_manuscript', autospec=True, return_value = None)
# def test_read_manuscript_not_found(mock_read):
#     """
#     Test that the GET /manuscripts/GET/<id> endpoint returns the correct manuscript data.
#     """
#     dne_mock_id = ObjectId()
    
#     # Use the test client (assumed to be available as TEST_CLIENT) to send a GET request.
#     response = TEST_CLIENT.get(f"/manuscripts/{dne_mock_id}")
#     # Assert that the response has the expected HTTP status code.
#     assert response.status_code == NOT_FOUND
    
#     # Parse the JSON response.
#     data = response.get_json()
#     print('resp data', data)
    
#     # Verify that the returned data matches our fake manuscript.
#     assert data["author"] == MOCK_AUTHOR
#     assert data["title"] == MOCK_TITLE
#     assert data["text"] == MOCK_TEXT

#     clean_mock_manuscript(manu_mock_id)






