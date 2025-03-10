"""
This is the file containing all of the endpoints for our flask app.
The endpoint called `endpoints` will return all available endpoints.
"""

from http import HTTPStatus

from flask import Flask, request
from flask_restx import Resource, Api, fields  # Namespace
from flask_cors import CORS

import werkzeug.exceptions as wz

import data.people as ppl
import data.text as txt
import data.manuscripts.manuscripts as manuscripts


app = Flask(__name__)
CORS(app)
api = Api(app)

DATE = '2024-09-24'
DATE_RESP = 'Date'
EDITOR = 'ejc369@nyu.edu'
EDITOR_RESP = 'Editor'
ENDPOINT_EP = '/endpoints'
ENDPOINT_RESP = 'Available endpoints'
HELLO_EP = '/hello'
HELLO_RESP = 'hello'
MESSAGE = 'Message'
PEOPLE_EP = '/people'
PUBLISHER = 'Palgave'
PUBLISHER_RESP = 'Publisher'
RETURN = 'return'
TITLE = 'The Journal of API Technology'
TITLE_EP = '/title'
TITLE_RESP = 'Title'

# ENDPOINTS FOR TEXT
TEXT_DELETE_EP = '/text/delete'
TEXT_DELETE_RESP = 'Text Deleted'
TEXT_CREATE_EP = '/text/create'
TEXT_COLLECTION = 'text'

# --- Manuscript Endpoint Constants ---
MANUSCRIPTS_EP = '/manuscripts'
MANUSCRIPTS_CREATE_EP = f'{MANUSCRIPTS_EP}/create'


MANUSCRIPT_CREATE_FLDS = api.model('CreateManuscript', {
    'author': fields.String(
        required=True,
    ),
    'title': fields.String(
        required=True,
    ),
    'text': fields.String(
        required=True,
    ),
})


@api.route(MANUSCRIPTS_CREATE_EP)
class ManuscriptCreate(Resource):
    """
    This class handles creating new manuscript entries.
    """
    @api.expect(MANUSCRIPT_CREATE_FLDS)
    @api.response(HTTPStatus.CREATED, 'Manuscript successfully created')
    @api.response(HTTPStatus.BAD_REQUEST, 'Missing required fields')
    def put(self):
        """
        Create a new manuscript.
        """
        try:
            # Use the provided author or default to the value in the model
            author = request.json.get('author')
            title = request.json.get('title')
            text = request.json.get('text')

            if not all([title, text]):
                raise wz.BadRequest(
                    "Missing required field(s): 'title' or 'text'.")

            # Call the manuscript creation function from data.manuscripts.
            manuscript_id = manuscripts.create_manuscript(
                            author,
                            title,
                            text)
            if not manuscript_id:
                raise wz.InternalServerError("Manuscript creation failed.")

            return {
                'message': 'Manuscript created successfully',
                'manuscript_id': str(manuscript_id)
            }, HTTPStatus.CREATED
        except Exception as err:
            raise wz.InternalServerError(f"Error creating manuscript: {err}")


@api.route(HELLO_EP)
class HelloWorld(Resource):
    """
    The purpose of the HelloWorld class is to have a simple test to see if the
    app is working at all.
    """
    def get(self):
        """
        A trivial endpoint to see if the server is running.
        """
        return {HELLO_RESP: HELLO_RESP}


@api.route(ENDPOINT_EP)
class Endpoints(Resource):
    """
    This class will serve as live, fetchable documentation of what endpoints
    are available in the system.
    """
    def get(self):
        """
        The `get()` method will return a sorted list of available endpoints.
        """
        endpoints = sorted(rule.rule for rule in api.app.url_map.iter_rules())
        return {ENDPOINT_RESP: endpoints}


@api.route(TITLE_EP)
class JournalTitle(Resource):
    """
    This class handles creating, reading, updating
    and deleting the journal title.
    """
    def get(self):
        """
        Retrieve the journal title.
        """
        return {
            TITLE_RESP: TITLE,
            EDITOR_RESP: EDITOR,
            DATE_RESP: DATE,
            PUBLISHER_RESP: PUBLISHER,
        }


@api.route(PEOPLE_EP)
class People(Resource):
    """
    This class handles creating, reading, updating
    and deleting journal people.
    """
    def get(self):
        """
        Retrieve the journal people.
        """
        return ppl.read()


@api.route(f'{PEOPLE_EP}/<email>')
class Person(Resource):
    """
    This class handles creating, reading, updating
    and deleting journal people.
    """
    def get(self, email):
        """
        Retrieve a journal person.
        """
        person = ppl.read_one(email)
        if person:
            return person
        else:
            raise wz.NotFound(f'No such record: {email}')

    @api.response(HTTPStatus.OK, 'Success.')
    @api.response(HTTPStatus.NOT_FOUND, 'No such person.')
    def delete(self, email):
        ret = ppl.delete(email)
        if ret is not None:
            return {'Deleted': ret}
        else:
            raise wz.NotFound(f'No such person: {email}')


PEOPLE_CREATE_FLDS = api.model('AddNewPeopleEntry', {
    ppl.NAME: fields.String,
    ppl.EMAIL: fields.String,
    ppl.AFFILIATION: fields.String,
    ppl.ROLES: fields.String,
})


@api.route(f'{PEOPLE_EP}/create')
class PeopleCreate(Resource):
    """
    Add a person to the journal db.
    """
    @api.response(HTTPStatus.OK, 'Success')
    @api.response(HTTPStatus.NOT_ACCEPTABLE, 'Not acceptable')
    @api.expect(PEOPLE_CREATE_FLDS)
    def put(self):
        """
        Add a person
        """
        try:
            name = request.json.get(ppl.NAME)
            affiliation = request.json.get(ppl.AFFILIATION)
            email = request.json.get(ppl.EMAIL)
            role = request.json.get(ppl.ROLES)
            ret = ppl.create(name, affiliation, email, role)
        except Exception as err:
            raise wz.NotAcceptable(f'Could not add person: {err=}')
        return {MESSAGE: 'Person added!', RETURN: ret}


@api.route('/text/<string:key>')
class TextOneResource(Resource):
    """
    This class handles retrieving a single text entry.
    """
    def get(self, key):
        """
        Retrieve a single text entry by key.
        """
        entry = txt.read_one(key)
        if entry:
            return entry, HTTPStatus.OK
        else:
            raise wz.NotFound(f'No text entry found for key: {key}')


@api.route(TEXT_CREATE_EP)
class TextCreate(Resource):
    """
    This class handles creating text entries.
    """
    @api.expect(api.model('CreateText', {
        'key': fields.String,
        'title': fields.String,
        'text': fields.String,
    }))
    def put(self):
        """
        Create a new text entry.
        """
        data = request.json
        return txt.create(data['key'], data['title'], data['text'])


@api.route(TEXT_DELETE_EP)
class TextDelete(Resource):
    """
    This class handles deleting text entries.
    """
    def delete(self, key):
        """
        Delete a text entry.
        """
        return txt.delete(key)


if __name__ == '__main__':
    app.run(debug=True)
