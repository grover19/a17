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
import data.manuscripts.manuscripts as ms


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

# --- Manuscript Endpoint Constants ---


# --- Manuscript Endpoint Constants ---
MANUSCRIPTS_EP = "/manuscripts"
MANUSCRIPTS_CREATE_EP = f"{MANUSCRIPTS_EP}/create"
MANUSCRIPTS_GET_EP = f"{MANUSCRIPTS_EP}/<id>"
MANUSCRIPTS_DEL_EP = f"{MANUSCRIPTS_EP}/<id>"


MANUSCRIPT_CREATE_FLDS = api.model("CreateManuscript", {
    "author": fields.String(required=True),
    "title": fields.String(required=True),
    "text": fields.String(required=True),
})


@api.route(f'{MANUSCRIPTS_CREATE_EP}')
class ManuscriptCreate(Resource):
    """
    Create a new manuscript entry.
    """
    @api.expect(MANUSCRIPT_CREATE_FLDS)
    @api.response(HTTPStatus.CREATED, "Manuscript successfully created")
    # @api.response(HTTPStatus.BAD_REQUEST,
    #               "Missing required fields or invalid input")
    def post(self):
        """
        Create a manuscript.
        """
        data = request.get_json()
        author = data.get("author", "").strip()
        title = data.get("title", "").strip()
        text = data.get("text", "").strip()

        if not author or not title or not text:
            raise wz.BadRequest("Missing one or more required fields")

        manu = ms.create_manuscript(author, title, text)
        print(manu)
        if not manu:
            raise wz.InternalServerError("Manuscript creation failed.")

        return {
            "author": manu[ms.AUTHOR_NAME],
            "title": manu[ms.LATEST_VERSION][ms.TITLE],
            "text":  manu[ms.LATEST_VERSION][ms.TEXT]
        }


@api.route(MANUSCRIPTS_DEL_EP)
class ManuscriptDelete(Resource):
    """
    Delete a manuscript entry by its manuscript id.
    """
    def delete(self, id):
        """
        Delete a manuscript by its manuscript id.
        """
        id = id.strip()
        return ms.delete_manuscript(id)


@api.route(MANUSCRIPTS_GET_EP)
class ManuscriptRetrieve(Resource):
    """
    Retrieve a manuscript entry by its manuscript id.
    """
    @api.response(HTTPStatus.OK, "Manuscript retrieved successfully")
    @api.response(HTTPStatus.BAD_REQUEST, "Missing or invalid manuscript id")
    @api.response(HTTPStatus.NOT_FOUND, "Manuscript not found")
    def get(self, id):
        """
        Retrieve a manuscript by manuscript id.
        """
        id = id.strip()
        # Optionally validate the manuscript_id as a MongoDB ObjectId.

        manu = ms.read_one_manuscript(id)
        if not manu:
            raise wz.NotFound(f"No manuscript found with id '{id}'.")

        # Assume the latest version is stored under ms.LATEST_VERSION.
        latest_manu = manu['latest_version']
        return {
            "author": manu[ms.AUTHOR_NAME],
            "title": latest_manu[ms.TITLE],
            "text": latest_manu.get(ms.TEXT),
        }


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
        """
        Delete a journal person.
        """
        ret = ppl.delete(email)
        if ret is not None:
            return {'Deleted': ret}     # 200 OK
        else:
            raise wz.NotFound(f'No such person: {email}')  # 404


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


# ENDPOINTS FOR TEXT
TEXT_DELETE_EP = '/text/delete'
TEXT_CREATE_EP = '/text/create'
TEXT_GET = '/text/<string:key>'


@api.route(TEXT_GET)
class TextOneResource(Resource):
    """
    This class handles retrieving a single text entry.
    """
    def get(self, key):
        """
        Retrieve a single text entry by key.
        """
        test_doc = txt.read_one(key)
        if test_doc:
            return {
                "title": test_doc['title'],
                "text": test_doc['text']}, HTTPStatus.OK
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
        text_doc = txt.create(data['key'], data['title'], data['text'])
        return {
            "key": text_doc['key'],
            "title": text_doc['title'],
            'text': text_doc['text']
        }


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
