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
    """
    people = dbc.read_dict(PEOPLE_COLLECT, EMAIL, no_id=not include_id)
    print(f'{people=}')
    return people


def read_one(email):
    """
    Return a person record if email present in DB,
    else None.
    """
    return dbc.read_one(PEOPLE_COLLECT, {EMAIL: email})


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
        person = {
            NAME: name,
            AFFILIATION: affiliation,
            EMAIL: email,
            ROLES: roles,
            PASSWORD: hash_password(password)
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


if __name__ == '__main__':
    main()
