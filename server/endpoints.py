"""
This is the file containing all of the endpoints for our flask app.
The endpoint called `endpoints` will return all available endpoints.
"""

from http import HTTPStatus

from flask import Flask, request
from flask_restx import Resource, Api, fields  # Namespace
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

import werkzeug.exceptions as wz

import data.people as ppl
import data.text as txt
import data.manuscripts.manuscripts as ms
from data.auth import authenticate_user
from data.people import sanitize_user  # Import sanitize_user from people module

app = Flask(__name__)

# Setup JWT
app.config['JWT_SECRET_KEY'] = 'your-secret-key'  # Change this to a secure secret key in production
jwt = JWTManager(app)

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
MANUSCRIPTS_UPDATE_EP = f"{MANUSCRIPTS_EP}/update"
MANUSCRIPTS_ACTION_EP = f"{MANUSCRIPTS_EP}/receive_action"

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
    @jwt_required()
    @api.expect(MANUSCRIPT_CREATE_FLDS)
    @api.response(HTTPStatus.CREATED, "Manuscript successfully created")
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
        if not manu:
            raise wz.InternalServerError("Manuscript creation failed.")

        return {
            "author": manu[ms.AUTHOR_NAME],
            "title": manu[ms.LATEST_VERSION][ms.TITLE],
            "text": manu[ms.LATEST_VERSION][ms.TEXT],
        }

@api.route(f"{MANUSCRIPTS_EP}/author/<string:author_name>")
class ManuscriptRetrieveByAuthor(Resource):
    @jwt_required()
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

@api.route(MANUSCRIPTS_GET_EP)
class ManuscriptResource(Resource):
    """
    GET and DELETE /manuscripts/{id}
    """
    @jwt_required()
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

    @jwt_required()
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
    @jwt_required()
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

@api.route(MANUSCRIPTS_UPDATE_EP)
class ManuscriptUpdate(Resource):
    """
    Update a manuscript's content
    """
    @jwt_required()
    @api.expect(api.model(
        "UpdateManuscript",
        {
            "id": fields.String(required=True),
            "title": fields.String(required=True),
            "text": fields.String(required=True),
        },
    ))
    @api.response(HTTPStatus.OK, "Manuscript updated successfully")
    @api.response(HTTPStatus.NOT_FOUND, "Manuscript not found")
    @api.response(HTTPStatus.BAD_REQUEST, "Invalid request data")
    def put(self):
        """
        Update a manuscript's title and text
        """
        data = request.get_json()
        manuscript_id = data.get("id", "").strip()
        title = data.get("title", "").strip()
        text = data.get("text", "").strip()

        if not manuscript_id or not title or not text:
            raise wz.BadRequest("Missing required fields")

        result = ms.update_manuscript(manuscript_id, title, text)
        if not result:
            raise wz.NotFound(f"No manuscript found with ID {manuscript_id}")

        # Format the response to ensure JSON serialization
        formatted_result = {
            "author": result[ms.AUTHOR_NAME],
            "title": result[ms.LATEST_VERSION][ms.TITLE],
            "text": result[ms.LATEST_VERSION][ms.TEXT],
            "version": result[ms.LATEST_VERSION][ms.VERSION],
            "state": result[ms.LATEST_VERSION][ms.STATE],
            "created": result[ms.MANUSCRIPT_CREATED].isoformat() if result[ms.MANUSCRIPT_CREATED] else None
        }
        
        return formatted_result

# ENDPOINTS FOR PEOPLE
PEOPLE_EP = "/people"
PEOPLE_GET_EP = f"{PEOPLE_EP}/<id>"
PEOPLE_CREATE_EP = f"{PEOPLE_EP}/create"
PEOPLE_UPDATE_EP = f"{PEOPLE_EP}/update"

@api.route(PEOPLE_EP)
class People(Resource):
    """
    This class handles creating, reading, updating
    and deleting journal people.
    """
    @jwt_required()
    def get(self):
        """
        The `get()` method returns all people in the database.
        """
        people = ppl.read(include_id=True)
        # Sanitize each user's data to remove sensitive information
        sanitized_people = {email: ppl.sanitize_user(user) for email, user in people.items()}
        return {RETURN: sanitized_people}

@api.route(PEOPLE_GET_EP)
class Person(Resource):
    """
    This class handles creating, reading, updating
    and deleting journal people.
    """
    @jwt_required()
    def get(self, id):
        """
        Retrieve a journal person by ID.
        """
        person = ppl.read_one_by_id(id)
        if person:
            return ppl.sanitize_user(person)
        else:
            raise wz.NotFound(f"No such record with ID: {id}")

    @jwt_required()
    @api.response(HTTPStatus.OK, "Success.")
    @api.response(HTTPStatus.NOT_FOUND, "No such person.")
    def delete(self, id):
        """
        Delete a journal person by ID.
        """
        ret = ppl.delete_by_id(id)
        if ret is not None:
            return {"Deleted": ret}  # 200 OK
        else:
            raise wz.NotFound(f"No such person with ID: {id}")  # 404

    @jwt_required()
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
    def put(self, id):
        """
        Update a journal person by ID
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
            updated_person = ppl.update_by_id(id, name, affiliation, email, roles)
            return {
                "message": "Person updated successfully",
                "person": ppl.sanitize_user(updated_person)
            }, HTTPStatus.OK
        except ValueError as err:
            raise wz.NotFound(str(err))

PEOPLE_CREATE_FLDS = api.model(
    "AddNewPeopleEntry",
    {
        ppl.NAME: fields.String(required=True),
        ppl.EMAIL: fields.String(required=True),
        ppl.AFFILIATION: fields.String(required=True),
        ppl.ROLES: fields.List(fields.String, required=True),
        "password": fields.String(required=True, description="User's password - will be hashed before storage")
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
            
            # Convert roles list to string (since backend expects a single role)
            role = roles[0] if roles else None
            
            if not name or not email or not affiliation or not password or not role:
                raise wz.BadRequest("Missing required fields")
            
            ret = ppl.create(name, affiliation, email, role, password)
            # Sanitize the user data before returning
            sanitized_user = ppl.sanitize_user(ret)
            return {MESSAGE: "Person added!", RETURN: sanitized_user}, HTTPStatus.CREATED
        except ValueError as err:
            raise wz.BadRequest(str(err))
        except Exception as err:
            raise wz.NotAcceptable(f"Could not add person: {err=}")

@api.route(PEOPLE_UPDATE_EP)
class PeopleUpdate(Resource):
    """
    Update a person's information in the journal database.
    """
    @jwt_required()
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

@api.route('/people/email/<string:email>')
class PersonByEmail(Resource):
    @jwt_required()
    def get(self, email):
        """
        Retrieve a journal person by email.
        """
        user = ppl.read_one(email)
        if user:
            return ppl.sanitize_user(user)
        else:
            raise wz.NotFound(f"No user found with email: {email}")

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
        Authenticate user and return JWT token and user data
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
        
        # Return both token and sanitized user data
        return {
            "token": access_token,
            "user": sanitize_user(user)
        }, HTTPStatus.OK

@api.route(MANUSCRIPTS_ACTION_EP)
class ManuscriptAction(Resource):
    """
    Process an action on a manuscript
    """
    @jwt_required()
    @api.expect(api.model(
        "ManuscriptAction",
        {
            "id": fields.String(required=True),
            "action": fields.String(required=True),
            "comment": fields.String(required=False),
        },
    ))
    @api.response(HTTPStatus.OK, "Action processed successfully")
    @api.response(HTTPStatus.NOT_FOUND, "Manuscript not found")
    @api.response(HTTPStatus.BAD_REQUEST, "Invalid action or missing fields")
    def put(self):
        """
        Process an action (accept/reject/revise) on a manuscript
        """
        data = request.get_json()
        manuscript_id = data.get("id", "").strip()
        action = data.get("action", "").strip().lower()
        comment = data.get("comment", "").strip()

        if not manuscript_id or not action:
            raise wz.BadRequest("Missing manuscript ID or action")

        if action not in ["accept", "reject", "revise"]:
            raise wz.BadRequest("Invalid action. Must be one of: accept, reject, revise")

        result = ms.process_manuscript_action(manuscript_id, action, comment)
        if not result:
            raise wz.NotFound(f"No manuscript found with ID {manuscript_id}")

        return result

if __name__ == "__main__":
    app.run(debug=True) 