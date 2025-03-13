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


@patch('data.people.delete', autospec=True, return_value='deleted')
def test_delete_person_success():
    test_user = {
        "name": "John Doe",
        "email": "testing@nyu.com",
        "affiliation": "Columbia",
        "roles": "ED"
    }

    # Create
    resp = TEST_CLIENT.put(f'{ep.PEOPLE_EP}/create', json=test_user)
    assert resp.status_code == OK

    # Delete
    resp = TEST_CLIENT.delete(f'{ep.PEOPLE_EP}/{test_user["email"]}')
    assert resp.status_code == OK

    # Check JSON
    resp_json = resp.get_json()
    # Should return the actual email now, e.g. {'Deleted': 'testing@nyu.com'}
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

# ------------------------- endpoint for create ------------------------------- 
MOCK_AUTHOR = 'John Doe' 
MOCK_TITLE = 'this is my manuscript'
MOCK_TEXT = 'someText'


@patch('data.manuscripts.manuscripts.read_one_manuscript', autospec=False, return_value={
    "author": MOCK_AUTHOR, 
    "title": MOCK_TITLE, 
    "text": MOCK_TEXT
}) 

def test_create_manuscripts(mock_read): 
    test_manu_create_payload = {
        'author' : MOCK_AUTHOR, 
        'title' : MOCK_TITLE, 
        'text' : MOCK_TEXT
    }
    resp = TEST_CLIENT.post(ep.MANUSCRIPTS_CREATE_EP, json = test_manu_create_payload)
    assert resp.status_code == OK

    resp_json = resp.get_json()

    # assert 'manuscript_id' in resp_json
    print(resp_json)
    # assert 'author' in resp_json
    # assert 'text' in resp_json 
    # assert 'title' in resp_json 

    assert resp_json['author'] == MOCK_AUTHOR 
    assert resp_json['title'] == MOCK_TITLE
    assert resp_json['text'] == MOCK_TEXT

    print(resp_json)
