"""
This module interfaces to our user data.
"""
import re
from bson import ObjectId

import data.db_connect as dbc
import data.roles as rls
from data.auth import hash_password
from data.models import (
    NAME, EMAIL, ROLES, AFFILIATION, PASSWORD,
    TEST_EMAIL, DEL_EMAIL
)

PEOPLE_COLLECT = 'people'

# test commit message
MIN_USER_NAME_LEN = 2

client = dbc.connect_db()
print(f'{client=}')

CHAR_OR_DIGIT = '[A-Za-z0-9]'
VALID_CHARS = '[A-Za-z0-9_.]'


def is_valid_email(email):
    return re.fullmatch(f"{VALID_CHARS}+@{CHAR_OR_DIGIT}+"
                        + "\\."
                        + f"{CHAR_OR_DIGIT}"
                        + "{2,3}", email)


def read(include_id=False):
    """
    Our contract:
        - Optional include_id parameter to include MongoDB ObjectID in response
        - Returns a dictionary of users keyed on user email.
        - Each user email must be the key for another dictionary.
        - Excludes password hashes from the response.
    """
    people = dbc.read_dict(PEOPLE_COLLECT, EMAIL, no_id=not include_id)
    # Remove password field from each person's data
    for person in people.values():
        if PASSWORD in person:
            del person[PASSWORD]
    print(f'{people=}')
    return people


def read_one(email, include_password=False):
    """
    Return a person record if email present in DB,
    else None.
    Args:
        email: The email to look up
        include_password: Whether to include the password hash in the response
    """
    person = dbc.read_one(PEOPLE_COLLECT, {EMAIL: email})
    if person and not include_password:
        if PASSWORD in person:
            del person[PASSWORD]
    return person


def exists(email):
    return read_one(email) is not None


def delete(email):
    print(f'{EMAIL=}, {email=}')
    deleted_count = dbc.delete(PEOPLE_COLLECT, {EMAIL: email})
    if deleted_count == 1:
        return email
    else:
        return None


def is_valid_person(name, affiliation, email, role = None, roles = None):
    if not is_valid_email(email):
        raise ValueError(f'Invalid email: {email}')

    if role:
        if not rls.is_valid(role):
            raise ValueError(f'Invalid role: {role}')

    elif roles:
        for role in roles:
            if not rls.is_valid(role):
                raise ValueError(f'Invalid role: {role}')
    return True


def create(name, affiliation, email, role, password):
    """
    Create a new person with the given details.
    Password is required and will be hashed before storage.
    Returns the created person object including ObjectId.
    """
    if exists(email):
        raise ValueError(f'Adding duplicate {email=}')
    if not password:
        raise ValueError('Password is required')
    if is_valid_person(name, affiliation, email, role=role):
        roles = []
        if role:
            roles.append(role)
        
        # Hash password and decode to string for storage
        password_hash = hash_password(password)
        if isinstance(password_hash, bytes):
            password_hash = password_hash.decode('utf-8')
            
        person = {
            NAME: name,
            AFFILIATION: affiliation,
            EMAIL: email,
            ROLES: roles,
            PASSWORD: password_hash
        }
        dbc.create(PEOPLE_COLLECT, person)
        # Return the full person object including ObjectId
        return read_one(email)


def update(name, affiliation, email, roles):
    if not exists(email):
        raise ValueError(f'Updating non-existent person: {email=}')
    if is_valid_person(name, affiliation, email, roles=roles):
        ret = dbc.update(PEOPLE_COLLECT,
                         {EMAIL: email},
                         {NAME: name, AFFILIATION: affiliation,
                          EMAIL: email, ROLES: roles})
        print(f'{ret=}')
        return email


def has_role(person, role):
    if role in person.get(ROLES):
        return True
    return False


MH_FIELDS = [NAME, AFFILIATION]


def get_mh_fields(journal_code=None):
    return MH_FIELDS


def create_mh_rec(person):
    mh_rec = {}
    for field in get_mh_fields():
        mh_rec[field] = person.get(field, '')
    return mh_rec


def get_masthead():
    masthead = {}
    mh_roles = rls.get_masthead_roles()
    for mh_role, text in mh_roles.items():
        people_w_role = []
        people = read()
        for _id, person in people.items():
            if has_role(person, mh_role):
                rec = create_mh_rec(person)
                people_w_role.append(rec)
        masthead[text] = people_w_role
    return masthead


def main():
    print(get_masthead())


def read_one_by_id(id_str):
    """
    Return a person record if ObjectId is present in DB,
    else None.
    """
    try:
        obj_id = ObjectId(id_str)
        return dbc.read_one(PEOPLE_COLLECT, {'_id': obj_id})
    except:
        return None


def update_by_id(id_str, name, affiliation, email, roles):
    """
    Update a person by their ObjectId.
    Returns the updated person record.
    """
    try:
        obj_id = ObjectId(id_str)
        if not dbc.read_one(PEOPLE_COLLECT, {'_id': obj_id}):
            raise ValueError(f'Updating non-existent person with id: {id_str}')
        
        if is_valid_person(name, affiliation, email, roles=roles):
            ret = dbc.update(PEOPLE_COLLECT,
                           {'_id': obj_id},
                           {NAME: name, AFFILIATION: affiliation,
                            EMAIL: email, ROLES: roles})
            print(f'{ret=}')
            return read_one_by_id(id_str)
    except Exception as e:
        raise ValueError(f'Error updating person: {str(e)}')


def delete_by_id(id_str):
    """
    Delete a person by their ObjectId.
    Returns the id of the deleted person if successful, None otherwise.
    """
    try:
        obj_id = ObjectId(id_str)
        deleted_count = dbc.delete(PEOPLE_COLLECT, {'_id': obj_id})
        if deleted_count == 1:
            return id_str
        else:
            return None
    except:
        return None


def replace_document(id_str, new_data):
    """
    Replace an entire person document with new data.
    Returns the updated person record.
    """
    try:
        obj_id = ObjectId(id_str)
        
        # Validate the new data
        if is_valid_person(
            new_data.get(NAME),
            new_data.get(AFFILIATION),
            new_data.get(EMAIL),
            roles=new_data.get(ROLES)
        ):
            # Create update document (excluding _id if present)
            update_data = {k: v for k, v in new_data.items() if k != '_id'}
            
            # Update the document
            ret = dbc.update(
                PEOPLE_COLLECT,
                {'_id': obj_id},
                update_data
            )
            
            if ret and ret.modified_count > 0:
                # Return the updated document
                updated_doc = read_one_by_id(id_str)
                if updated_doc and PASSWORD in updated_doc:
                    del updated_doc[PASSWORD]
                return updated_doc
            return None
            
    except Exception as e:
        raise ValueError(f'Error updating person: {str(e)}')


if __name__ == '__main__':
    main()
