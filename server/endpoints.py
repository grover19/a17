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

DATE = "2024-09-24"
DATE_RESP = "Date"
EDITOR = "ejc369@nyu.edu"
EDITOR_RESP = "Editor"
ENDPOINT_EP = "/endpoints"
ENDPOINT_RESP = "Available endpoints"
HELLO_EP = "/hello"
HELLO_RESP = "hello"
MESSAGE = "Message"
PUBLISHER = "Palgave"
PUBLISHER_RESP = "Publisher"
RETURN = "return"
TITLE = "The Journal of API Technology"
TITLE_EP = "/title"
TITLE_RESP = "Title"


# --- Manuscript Endpoint Constants ---
MANUSCRIPTS_EP = "/manuscripts"
MANUSCRIPTS_CREATE_EP = f"{MANUSCRIPTS_EP}/create"
MANUSCRIPTS_GET_EP = f"{MANUSCRIPTS_EP}/<id>"
MANUSCRIPTS_DEL_EP = f"{MANUSCRIPTS_EP}/<id>"
MANUSCRIPTS_UPDATE_EP = f"{MANUSCRIPTS_EP}/update"  # for later use


MANUSCRIPT_CREATE_FLDS = api.model(
    "CreateManuscript",
    {
        "author": fields.String(required=True),
        "title": fields.String(required=True),
        "text": fields.String(required=True),
    },
)


@api.route(f"{MANUSCRIPTS_CREATE_EP}")
class ManuscriptCreate(Resource):
    """
    Create a new manuscript entry.
    """

    @api.expect(MANUSCRIPT_CREATE_FLDS)
    @api.response(HTTPStatus.CREATED, "Manuscript successfully created")
    # @api.response(HTTPStatus.BAD_REQUEST,
    #               "Missing required fields or invalid input")
    def put(self):
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
            "text": manu[ms.LATEST_VERSION][ms.TEXT],
        }

@api.route(f"{MANUSCRIPTS_EP}/author/<string:author_name>")
class ManuscriptRetrieveByAuthor(Resource):


    @api.response(HTTPStatus.OK, "Manuscripts retrieved successfully")
    @api.response(HTTPStatus.NOT_FOUND, "No manuscripts found for the given author")
    def get(self, author_name):
        """
        Retrieve all manuscripts for the specified author name.
        """
        manuscripts = ms.read_manuscripts_by_author(author_name)

        if not manuscripts:
            raise wz.NotFound(f"No manuscripts found for author '{author_name}'.")

        return manuscripts


@api.route(MANUSCRIPTS_DEL_EP)
class ManuscriptResource(Resource):
    """
    GET and DELETE /manuscripts/{id}
    """

    @api.response(HTTPStatus.OK, "Manuscript retrieved successfully")
    @api.response(HTTPStatus.BAD_REQUEST, "Missing or invalid manuscript id")
    @api.response(HTTPStatus.NOT_FOUND, "Manuscript not found")
    def get(self, id):
        """
        Retrieve a manuscript by ID.
        """
        id = id.strip()
        manu = ms.read_one_manuscript(id)
        if not manu:
            raise wz.NotFound(f"No manuscript found with id '{id}'.")
        latest_manu = manu["latest_version"]
        return {
            "author": manu[ms.AUTHOR_NAME],
            "title": latest_manu[ms.TITLE],
            "text": latest_manu.get(ms.TEXT),
        }

    @api.response(HTTPStatus.OK, "Manuscript successfully deleted")
    @api.response(HTTPStatus.NOT_FOUND, "Manuscript not found")
    def delete(self, id):
        """
        Delete a manuscript by ID.
        """
        id = id.strip()
        result = ms.delete_manuscript(id)
        if result:
            return {
                "message": (
                    f"Manuscript with ID {id} deleted."
                )
            }, HTTPStatus.OK
        else:
            raise wz.NotFound(f"No manuscript found with ID {id}")


@api.route(MANUSCRIPTS_EP)
class ManuscriptRetrieveAll(Resource):
    """
    Retrieve all manuscript entries
    """

    @api.response(HTTPStatus.OK, "Manuscripts retrieved successfully")
    def get(self):
        """
        Retrieve all manuscripts
        """
        all_manu = ms.read_all_manuscripts()
        return all_manu


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


# ENDPOINTS FOR PEOPLE
PEOPLE_EP = "/people"
PEOPLE_GET_EP = f"{PEOPLE_EP}/<email>"
PEOPLE_CREATE_EP = f"{PEOPLE_EP}/create"
PEOPLE_UPDATE_EP = f"{PEOPLE_EP}/update"


@api.route(PEOPLE_EP)
class People(Resource):
    """
    This class handles creating, reading, updating
    and deleting journal people.
    """

    def get(self):
        """
        Retrieve all journal people.
        """
        return ppl.read()


@api.route(PEOPLE_GET_EP)
class Person(Resource):
    """
    This class handles creating, reading, updating
    and deleting journal people.
    """

    def get(self, email):
        """
        Retrieve a journal person by email.
        """
        person = ppl.read_one(email)
        if person:
            return person
        else:
            raise wz.NotFound(f"No such record: {email}")

    @api.response(HTTPStatus.OK, "Success.")
    @api.response(HTTPStatus.NOT_FOUND, "No such person.")
    def delete(self, email):
        """
        Delete a journal person.
        """
        ret = ppl.delete(email)
        if ret is not None:
            return {"Deleted": ret}  # 200 OK
        else:
            raise wz.NotFound(f"No such person: {email}")  # 404


PEOPLE_CREATE_FLDS = api.model(
    "AddNewPeopleEntry",
    {
        ppl.EMAIL: fields.String(required=True),
        "password": fields.String(required=True),
        ppl.AFFILIATION: fields.String(required=True),
        ppl.ROLES: fields.List(fields.String, required=True),
    },
)


@api.route(PEOPLE_CREATE_EP)
class PeopleCreate(Resource):
    """
    Add a person to the journal db.
    """

    @api.response(HTTPStatus.CREATED, "Person successfully created")
    @api.response(HTTPStatus.BAD_REQUEST, "Invalid request data")
    @api.response(HTTPStatus.NOT_ACCEPTABLE, "Not acceptable")
    @api.expect(PEOPLE_CREATE_FLDS)
    def post(self):
        """
        Add a journal person
        """
        try:
            data = request.get_json()
            email = data.get(ppl.EMAIL, "").strip()
            affiliation = data.get(ppl.AFFILIATION, "").strip()
            roles = data.get(ppl.ROLES, [])
            
            # For now, we'll use email as the name since it's not provided in frontend
            # You may want to extract name from email or modify frontend to send name
            name = email
            
            # Convert roles list to string (since backend expects a single role)
            # You may want to modify the backend to handle multiple roles instead
            role = roles[0] if roles else None
            
            ret = ppl.create(name, affiliation, email, role)
            return {MESSAGE: "Person added!", RETURN: ret}, HTTPStatus.CREATED
        except Exception as err:
            raise wz.NotAcceptable(f"Could not add person: {err=}")


@api.route(PEOPLE_UPDATE_EP)
class PeopleUpdate(Resource):
    """
    Update a person's information in the journal database.
    """

    @api.response(HTTPStatus.OK, "Person updated successfully")
    @api.response(HTTPStatus.NOT_FOUND, "No such person exists")
    @api.response(HTTPStatus.BAD_REQUEST, "Invalid request data")
    @api.expect(api.model(
        "UpdatePeopleEntry",
        {
            ppl.NAME: fields.String(required=True),
            ppl.AFFILIATION: fields.String(required=True),
            ppl.EMAIL: fields.String(required=True),
            ppl.ROLES: fields.List(fields.String, required=True),
        },
    ))
    def post(self):
        """
        Update a journal person
        """
        data = request.get_json()

        # Extract fields
        name = data.get(ppl.NAME)
        affiliation = data.get(ppl.AFFILIATION)
        email = data.get(ppl.EMAIL)
        roles = data.get(ppl.ROLES)

        # Validate input
        if not (name and affiliation and email and isinstance(roles, list)):
            raise wz.BadRequest("Invalid request: Missing or incorrect fields")

        try:
            updated_email = ppl.update(name, affiliation, email, roles)
            return {
                "message": "Person updated successfully",
                "email": updated_email
            }, HTTPStatus.OK
        except ValueError as err:
            raise wz.NotFound(str(err))


# ENDPOINTS FOR TEXT
TEXT_EP = "/text"
TEXT_GET_EP = f"{TEXT_EP}/<string:key>"
TEXT_CREATE_EP = f"{TEXT_EP}/create"
TEXT_UPDATE_EP = f"{TEXT_EP}/update"


@api.route(TEXT_EP)
class TextRetrieveAll(Resource):
    """
    Retrieve all texts entries
    """
    @api.response(HTTPStatus.OK, "Texts retrieved successfully")
    def get(self):
        """
        Retrieve all texts entries
        """
        all_text = txt.read_all_texts()
        # Simply return the list of texts, even if it's empty.
        return all_text


@api.route(TEXT_GET_EP)
class TextResource(Resource):
    """
    GET and DELETE /text/{key}
    """

    @api.response(HTTPStatus.OK, "Text retrieved successfully")
    @api.response(HTTPStatus.NOT_FOUND, "Text not found")
    def get(self, key):
        """
        Retrieve a text entry by key.
        """
        test_doc = txt.read_one(key)
        if test_doc:
            return {
                "title": test_doc["title"],
                "text": test_doc["text"]
            }, HTTPStatus.OK
        else:
            raise wz.NotFound(f"No text entry found for key: {key}")

    @api.response(HTTPStatus.OK, "Text entry deleted successfully")
    @api.response(HTTPStatus.NOT_FOUND, "Text entry not found")
    def delete(self, key):
        """
        Delete a text entry by key.
        """
        try:
            deleted_key = txt.delete(key)
            return {
                "message": (
                    f'Text entry with key "{deleted_key}" deleted successfully'
                )
            }, HTTPStatus.OK
        except ValueError as e:
            return {'error': str(e)}, HTTPStatus.NOT_FOUND
        except Exception as e:
            return {'error': str(e)}, HTTPStatus.INTERNAL_SERVER_ERROR


@api.route(TEXT_CREATE_EP)
class TextCreate(Resource):
    """
    This class handles creating text entries.
    """

    @api.expect(
        api.model(
            "CreateText",
            {
                "key": fields.String,
                "title": fields.String,
                "text": fields.String,
            },
        )
    )
    def put(self):
        """
        Create a new text entry.
        """
        data = request.json
        text_doc = txt.create(data["key"], data["title"], data["text"])
        return {
            "key": text_doc["key"],
            "title": text_doc["title"],
            "text": text_doc["text"],
        }


@api.route(TEXT_UPDATE_EP)
class TextUpdate(Resource):
    @api.expect(api.model(
        "UpdateText",
        {
            "key": fields.String(required=True),
            "title": fields.String(required=True),
            "text": fields.String(required=True),
        },
    ))
    def post(self):
        """
        Update a text entry.
        """
        data = request.get_json()
        try:
            txt.update(data["key"], data["title"], data["text"])
            return {
                "message": "Text updated successfully",
                "key": data["key"]
            }, HTTPStatus.OK
        except ValueError as e:
            raise wz.NotFound(str(e))


if __name__ == "__main__":
    app.run(debug=True)
