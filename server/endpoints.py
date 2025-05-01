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
from data.manuscripts import query
from security import security as sec


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
PEOPLE_EP = "/people"
PUBLISHER = "Palgave"
PUBLISHER_RESP = "Publisher"
RETURN = "return"
TITLE = "The Journal of API Technology"
TITLE_EP = "/title"
TITLE_RESP = "Title"

# --- Manuscript Endpoint Constants ---


# --- Manuscript Endpoint Constants ---
MANUSCRIPTS_EP = "/manuscripts"
MANUSCRIPTS_CREATE_EP = f"{MANUSCRIPTS_EP}/create"
MANUSCRIPTS_GET_EP = f"{MANUSCRIPTS_EP}/<id>"
MANUSCRIPTS_DEL_EP = f"{MANUSCRIPTS_EP}/<id>"
MANUSCRIPTS_UPDATE_EP = f"{MANUSCRIPTS_EP}/update"
MANUSCRIPTS_RECEIVE_ACTION_EP = f"{MANUSCRIPTS_EP}/receive_action"
MANUSCRIPTS_VALID_ACTIONS_EP = f"{MANUSCRIPTS_EP}/<id>/valid_actions"


MANUSCRIPT_UPDATE_FLDS = api.model(
    "UpdateManuscript",
    {
        "id": fields.String(required=True),
        "title": fields.String(required=True),
        "text": fields.String(required=True),
    },
)


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


@api.route(MANUSCRIPTS_GET_EP)
class ManuscriptRetrieve(Resource):
    """
    Handles retrieving and deleting a manuscript by ID.
    """

    @api.response(HTTPStatus.OK, "Manuscript retrieved successfully")
    def get(self, id):
        id = id.strip()
        manu = ms.read_one_manuscript(id)
        if not manu:
            raise wz.NotFound(f"No manuscript found with id '{id}'.")
        latest_manu = manu[ms.LATEST_VERSION]
        return {
            "author": manu[ms.AUTHOR_NAME],
            "title": latest_manu[ms.TITLE],
            "text": latest_manu.get(ms.TEXT),
        }

    @api.response(HTTPStatus.OK, "Manuscript deleted")
    @api.response(HTTPStatus.NOT_FOUND, "Manuscript not found")
    def delete(self, id):
        id = id.strip()
        result = ms.delete_manuscript(id)
        if not result:
            raise wz.NotFound(f"No manuscript found with ID '{id}'")
        return {"message": f"Manuscript with ID {id} deleted."}


@api.route(MANUSCRIPTS_EP)
class ManuscriptRetrieveAll(Resource):
    """
    Retrieve all manuscript enties
    """
    @api.response(HTTPStatus.OK, "Manuscripts retrieved successfully")
    @api.response(HTTPStatus.NOT_FOUND, "No manuscripts found")
    def get(self):
        """
        Retrieve all manuscripts.
        """
        all_manu = ms.read_all_manuscripts()
        if not all_manu:
            raise wz.NotFound("No manuscripts found.")

        return all_manu, HTTPStatus.OK


@api.route(MANUSCRIPTS_UPDATE_EP)
class ManuscriptUpdate(Resource):
    """
    Update a manuscript's title and text.
    """

    @api.expect(MANUSCRIPT_UPDATE_FLDS)
    @api.response(HTTPStatus.OK, "Manuscript updated successfully")
    @api.response(HTTPStatus.NOT_FOUND, "Manuscript not found")
    @api.response(HTTPStatus.BAD_REQUEST, "Invalid input")
    def post(self):
        """
        Update a manuscript's title and text by ID.
        """
        data = request.get_json()
        manuscript_id = data.get("id", "").strip()
        title = data.get("title", "").strip()
        text = data.get("text", "").strip()

        if not manuscript_id or not title or not text:
            raise wz.BadRequest("Missing required fields")

        try:
            updated = ms.update_manuscript(manuscript_id, title, text)
            if not updated:
                raise wz.NotFound(
                    "No manuscript found with id "
                    f"'{manuscript_id}'."
                )
            return {
                "message": "Manuscript updated successfully",
                "id": manuscript_id,
                "title": title,
                "text": text
            }, HTTPStatus.OK
        except Exception as e:
            raise wz.InternalServerError(str(e))


@api.route(MANUSCRIPTS_RECEIVE_ACTION_EP)
class ManuscriptReceiveAction(Resource):
    @api.expect(api.model(
        "ManuscriptTransition",
        {
            "id": fields.String(required=True),
            "action": fields.String(required=True),
            "ref": fields.String(required=False),
            "target_state": fields.String(required=False),
        }
    ))
    def post(self):
        """
        Receive an action and transition a manuscript's state
        """
        data = request.json
        manu_id = data.get("id")
        action = data.get("action")
        ref = data.get("ref")
        target_state = data.get("target_state")
        try:
            new_state = ms.transition_manuscript_state(
                manu_id,
                action,
                ref=ref,
                target_state=target_state
            )
            return {
                "message": f"Manuscript transitioned to {new_state}",
                "state": new_state
            }, HTTPStatus.OK
        except Exception as e:
            raise wz.BadRequest(str(e))


@api.route(MANUSCRIPTS_VALID_ACTIONS_EP)
class ManuscriptValidActions(Resource):
    """
    Get valid actions for the current state of a manuscript.
    """

    @api.response(HTTPStatus.OK, "List of valid actions")
    @api.response(HTTPStatus.NOT_FOUND, "Manuscript not found")
    def get(self, id):
        """
        Retrieve the valid actions for a manuscript
        """
        try:
            id = id.strip()
            manu = ms.read_one_manuscript(id)
            if not manu:
                raise wz.NotFound(f"No manuscript found with ID {id}")

            curr_state = manu[ms.LATEST_VERSION][ms.STATE]
            curr_state_code = query.STATE_NAME_TO_CODE.get(
                curr_state,
                curr_state
            )
            valid_actions = list(ms.get_valid_actions(curr_state_code))
            return {
                "current_state": curr_state,
                "valid_actions": valid_actions
            }, HTTPStatus.OK

        except Exception as e:
            raise wz.InternalServerError(str(e))


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


@api.route(f"{PEOPLE_EP}/<email>")
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
        ppl.NAME: fields.String,
        ppl.EMAIL: fields.String,
        ppl.AFFILIATION: fields.String,
        ppl.ROLES: fields.String,
    },
)


@api.route(f"{PEOPLE_EP}/create")
class PeopleCreate(Resource):
    """
    Add a person to the journal db.
    """

    @api.response(HTTPStatus.OK, "Success")
    @api.response(HTTPStatus.NOT_ACCEPTABLE, "Not acceptable")
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
            raise wz.NotAcceptable(f"Could not add person: {err=}")
        return {MESSAGE: "Person added!", RETURN: ret}


@api.route(f"{PEOPLE_EP}/update")
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
        Update an existing person's details.
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
TEXT_DELETE_EP = "/text/delete"
TEXT_CREATE_EP = "/text/create"
TEXT_GET = "/text/<string:key>"
TEXT_UPDATE_EP = "/text/update"


@api.route(TEXT_EP)
class TextRetrieveAll(Resource):
    """
    Retrieve all texts
    """
    @api.response(HTTPStatus.OK, "Texts retrieved successfully")
    def get(self):
        """
        Retrieve all texts
        """
        all_text = txt.read_all_texts()
        # Simply return the list of texts, even if it's empty.
        return all_text


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
            return ({"title": test_doc["title"], "text": test_doc["text"]},)
            HTTPStatus.OK
        else:
            raise wz.NotFound(f"No text entry found for key: {key}")


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


@api.route("/security")
class SecurityRetrieve(Resource):
    """
    Retrieve the current security settings.
    """

    @api.response(HTTPStatus.OK, "Security settings retrieved successfully")
    def get(self):
        """
        Retrieve security settings
        """
        settings = sec.read()
        if not settings:
            raise wz.NotFound("No security settings found.")
        return settings


@api.route("/security/check")
class SecurityPermissionCheck(Resource):
    """
    Check if a user has permission to perform an action on a feature.
    """

    @api.expect(api.model(
        "SecurityPermissionCheck",
        {
            "feature_name": fields.String(required=True),
            "action": fields.String(required=True),
            "user_id": fields.String(required=True),
        }
    ))
    @api.response(HTTPStatus.OK, "Permission check completed successfully")
    @api.response(HTTPStatus.FORBIDDEN, "User does not have permission")
    def post(self):
        """
        Check if exisitng person has permission
        """
        data = request.get_json()
        feature_name = data.get("feature_name")
        action = data.get("action")
        user_id = data.get("user_id")

        if sec.is_permitted(feature_name, action, user_id):
            return {"message": "User has permission."}, HTTPStatus.OK
        else:
            return {
                "message": "User does not have permission."
            }, HTTPStatus.FORBIDDEN


if __name__ == "__main__":
    app.run(debug=True)
