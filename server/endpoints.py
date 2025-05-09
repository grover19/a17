"""
This is the file containing all of the endpoints for our flask app.
The endpoint called `endpoints` will return all available endpoints.
"""

from http import HTTPStatus

from flask import Flask, request
from flask_restx import Resource, Api, fields  # Namespace
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token

import werkzeug.exceptions as wz

import data.people as ppl
import data.text as txt
import data.manuscripts.manuscripts as ms
from data.auth import authenticate_user

app = Flask(__name__)

# Setup JWT
app.config['JWT_SECRET_KEY'] = (
    'your-secret-key'  # Change this to a secure secret key in production
)
jwt = JWTManager(app)

CORS(app)
api = Api(app)

# Constants
HELLO_EP = "/hello"
HELLO_RESP = "hello"
ENDPOINT_EP = "/endpoints"
ENDPOINT_RESP = "Available endpoints"

# --- Manuscript Endpoint Constants ---
MANUSCRIPTS_EP = "/manuscripts"
MANUSCRIPTS_CREATE_EP = f"{MANUSCRIPTS_EP}/create"
MANUSCRIPTS_GET_EP = f"{MANUSCRIPTS_EP}/<id>"
MANUSCRIPTS_DEL_EP = f"{MANUSCRIPTS_EP}/<id>"
MANUSCRIPTS_UPDATE_EP = f"{MANUSCRIPTS_EP}/update"
MANUSCRIPTS_RECEIVE_ACTION_EP = f"{MANUSCRIPTS_EP}/receive_action"

MANUSCRIPT_CREATE_FLDS = api.model(
    "CreateManuscript",
    {
        "author": fields.String(required=True),
        "title": fields.String(required=True),
        "text": fields.String(required=True),
    },
)

MANUSCRIPT_UPDATE_FLDS = api.model(
    "UpdateManuscript",
    {
        "id": fields.String(required=True),
        "title": fields.String(required=True),
        "text": fields.String(required=True),
    },
)

MANUSCRIPT_RECEIVE_ACTION_FLDS = api.model(
    "ReceiveActionManuscript",
    {
        "id": fields.String(required=True),
        "action": fields.String(required=True),
        "comment": fields.String(required=False),
    },
)


@api.route(f"{MANUSCRIPTS_CREATE_EP}")
class ManuscriptCreate(Resource):
    """
    Create a new manuscript entry.
    """
    @api.expect(MANUSCRIPT_CREATE_FLDS)
    @api.response(HTTPStatus.CREATED, "Manuscript successfully created")
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
        if not manu:
            raise wz.InternalServerError("Manuscript creation failed.")

        return {
            "_id": str(manu["_id"]),
            "author": manu[ms.AUTHOR_NAME],
            "title": manu[ms.LATEST_VERSION][ms.TITLE],
            "text": manu[ms.LATEST_VERSION][ms.TEXT],
        }, HTTPStatus.CREATED


@api.route(MANUSCRIPTS_UPDATE_EP)
class ManuscriptUpdate(Resource):
    """
    Update a manuscript.
    """
    @api.expect(MANUSCRIPT_UPDATE_FLDS)
    @api.response(HTTPStatus.OK, "Manuscript successfully updated")
    def put(self):
        """
        Update a manuscript's title and text.
        """
        data = request.get_json()
        manuscript_id = data.get("id", "").strip()
        title = data.get("title", "").strip()
        text = data.get("text", "").strip()

        if not manuscript_id or not title or not text:
            raise wz.BadRequest("Missing one or more required fields")

        manu = ms.update_manuscript(manuscript_id, title, text)
        if not manu:
            raise wz.NotFound(f"No manuscript found with id '{manuscript_id}'")

        return {
            "_id": str(manu["_id"]),
            "author": manu[ms.AUTHOR_NAME],
            "title": manu[ms.LATEST_VERSION][ms.TITLE],
            "text": manu[ms.LATEST_VERSION][ms.TEXT],
        }


@api.route(MANUSCRIPTS_RECEIVE_ACTION_EP)
class ManuscriptReceiveAction(Resource):
    """
    Handle manuscript actions (accept/reject/revise).
    """
    @api.expect(MANUSCRIPT_RECEIVE_ACTION_FLDS)
    @api.response(HTTPStatus.OK, "Action processed successfully")
    def put(self):
        """
        Process an action on a manuscript.
        """
        data = request.get_json()
        manuscript_id = data.get("id", "").strip()
        action = data.get("action", "").strip().lower()
        comment = data.get("comment", "").strip()

        if not manuscript_id or not action:
            raise wz.BadRequest("Missing manuscript ID or action")

        if action not in ["accept", "reject", "revise"]:
            raise wz.BadRequest(
                "Invalid action. Must be 'accept', 'reject', or 'revise'")

        manu = ms.process_manuscript_action(manuscript_id, action, comment)
        if not manu:
            raise wz.NotFound(f"No manuscript found with id '{manuscript_id}'")

        return {
            "_id": str(manu["_id"]),
            "author": manu[ms.AUTHOR_NAME],
            "title": manu[ms.LATEST_VERSION][ms.TITLE],
            "text": manu[ms.LATEST_VERSION][ms.TEXT],
            "status": manu.get("status", "pending"),
            "comment": manu.get("comment", "")
        }


@api.route(f"{MANUSCRIPTS_EP}/author/<string:author_name>")
class ManuscriptRetrieveByAuthor(Resource):
    @api.response(HTTPStatus.OK, "Manuscripts retrieved successfully")
    @api.response(
        HTTPStatus.NOT_FOUND,
        "No manuscripts found for the given author"
    )
    def get(self, author_name):
        """
        Retrieve all manuscripts for the specified author name.
        """
        manuscripts = ms.read_manuscripts_by_author(author_name)

        if not manuscripts:
            raise wz.NotFound(
                f"No manuscripts found for author '{author_name}'"
            )

        return manuscripts


@api.route(MANUSCRIPTS_DEL_EP)
class ManuscriptResource(Resource):
    """
    GET and DELETE /manuscripts/{id}
    """
    @api.response(HTTPStatus.OK, "Manuscript retrieved successfully")
    @api.response(
        HTTPStatus.BAD_REQUEST,
        "Missing or invalid manuscript id"
    )
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
            "_id": str(manu["_id"]),
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
                "message": f"Manuscript with ID {id} deleted."
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
        try:
            all_manu = ms.read_all_manuscripts()
            return all_manu
        except Exception as e:
            return {'error': str(e)}, HTTPStatus.INTERNAL_SERVER_ERROR


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


# ENDPOINTS FOR PEOPLE
PEOPLE_EP = "/people"
PEOPLE_GET_EP = f"{PEOPLE_EP}/<id>"
PEOPLE_CREATE_EP = f"{PEOPLE_EP}/create"


@api.route(PEOPLE_EP)
class People(Resource):
    """
    This class handles creating, reading, updating
    and deleting journal people.
    """
    @api.response(HTTPStatus.OK, "Retrieved all people successfully")
    def get(self):
        """
        Retrieve all journal people.
        """
        try:
            people = ppl.read(include_id=True)
            print(f"People data from database: {people}")  # Debug print

            if not people:
                print("No people found in database")  # Debug print
                return {}

            return people

        except Exception as e:
            print(f"Error in /people endpoint: {str(e)}")  # Debug print
            return {'error': str(e)}, HTTPStatus.INTERNAL_SERVER_ERROR


@api.route(PEOPLE_GET_EP)
class Person(Resource):
    """
    This class handles reading, updating and deleting individual people.
    """
    @api.response(HTTPStatus.OK, "Person retrieved successfully")
    @api.response(HTTPStatus.NOT_FOUND, "Person not found")
    def get(self, id):
        """
        Retrieve a journal person by id.
        """
        person = ppl.read_one(id)
        if person:
            return person
        else:
            raise wz.NotFound(f"No such record: {id}")

    @api.response(HTTPStatus.OK, "Person updated successfully")
    @api.response(HTTPStatus.NOT_FOUND, "Person not found")
    @api.response(HTTPStatus.BAD_REQUEST, "Invalid request data")
    def put(self, id):
        """
        Update a journal person by id.
        """
        data = request.get_json()
        if not data:
            raise wz.BadRequest("No data provided")

        try:
            # Convert roles to array if it's a string
            if 'roles' in data and isinstance(data['roles'], str):
                data['roles'] = data['roles'].split(', ')
            
            # Validate the data has required fields
            if not all(key in data for key in ['name', 'email', 'affiliation', 'roles']):
                raise wz.BadRequest("Missing required fields")
            
            # Update the document with the new data
            updated_person = ppl.replace_document(id, data)
            if updated_person:
                return {"message": "Person updated successfully", "person": updated_person}
            raise wz.NotFound(f"No such person: {id}")
        except ValueError as e:
            raise wz.BadRequest(str(e))

    @api.response(HTTPStatus.OK, "Success")
    @api.response(HTTPStatus.NOT_FOUND, "No such person")
    def delete(self, id):
        """
        Delete a journal person by id.
        """
        ret = ppl.delete(id)
        if ret is not None:
            return {"Deleted": ret}
        else:
            raise wz.NotFound(f"No such person: {id}")


PEOPLE_CREATE_FLDS = api.model(
    "AddNewPeopleEntry",
    {
        ppl.NAME: fields.String(required=True),
        ppl.EMAIL: fields.String(required=True),
        ppl.AFFILIATION: fields.String(required=True),
        ppl.ROLES: fields.List(fields.String, required=True),
        "password": fields.String(
            required=True,
            description="User's password - will be hashed before storage"
        )
    }
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
            name = data.get(ppl.NAME, "").strip()
            email = data.get(ppl.EMAIL, "").strip()
            affiliation = data.get(ppl.AFFILIATION, "").strip()
            password = data.get("password", "").strip()
            roles = data.get(ppl.ROLES, [])

            # Convert roles list to string
            # (since backend expects a single role)
            role = roles[0] if roles else None

            person = ppl.create(name, affiliation, email, role, password)

            # Remove password from response
            if person and 'password' in person:
                del person['password']

            return {
                "message": "Person added!",
                "person": person
            }, HTTPStatus.CREATED
        except ValueError as e:
            raise wz.NotAcceptable(str(e))


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
                "message": f' "{deleted_key}" deleted successfully'
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


# AUTH ENDPOINTS
AUTH_EP = "/auth"
AUTH_LOGIN_EP = f"{AUTH_EP}/login"

LOGIN_FIELDS = api.model(
    "Login",
    {
        "email": fields.String(required=True),
        "password": fields.String(required=True),
    }
)


@api.route(AUTH_LOGIN_EP)
class Login(Resource):
    """
    Handle user login and token generation
    """
    @api.expect(LOGIN_FIELDS)
    @api.response(HTTPStatus.OK, "Login successful")
    @api.response(HTTPStatus.UNAUTHORIZED, "Invalid credentials")
    def post(self):
        """
        Authenticate user and return JWT token
        """
        data = request.get_json()
        email = data.get("email", "").strip()
        password = data.get("password", "").strip()

        if not email or not password:
            raise wz.BadRequest("Email and password are required")

        user = authenticate_user(email, password)
        if not user:
            raise wz.Unauthorized("Invalid email or password")

        # Create access token
        access_token = create_access_token(identity=email)
        return {"token": access_token}, HTTPStatus.OK


if __name__ == "__main__":
    app.run(debug=True)
