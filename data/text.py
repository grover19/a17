"""
This module interfaces to our user data.
"""

import data.db_connect as dbc

# fields
KEY = 'key'
TITLE = 'title'
TEXT = 'text'
EMAIL = 'email'

TEXT_COLLECTION = 'text'  # Fixed typo here

TEST_KEY = 'HomePage'
SUBM_KEY = 'SubmissionsPage'
DEL_KEY = 'DeletePage'

text_dict = {
    TEST_KEY: {
        TITLE: 'Home Page',
        TEXT: 'This is a journal about building API servers.',
    },
    SUBM_KEY: {
        TITLE: 'Submissions Page',
        TEXT: 'All submissions must be original work in Word format.',
    },
    DEL_KEY: {
        TITLE: 'Delete Page',
        TEXT: 'This is a text to delete.',
    },
}


def create(key: str, title: str, text: str):
    # Check if an entry with this key already exists in the database.
    if dbc.read_one(TEXT_COLLECTION, {KEY: key}):
        raise KeyError(f"Key '{key}' already exists in the database.")

    # Build the document following our schema.
    document = {KEY: key, TITLE: title, TEXT: text}

    # Insert the document into the collection.
    dbc.create(TEXT_COLLECTION, document)
    return True


def delete(dict_key: str):
    print(f'{KEY=}, {dict_key=}')
    return dbc.delete(TEXT_COLLECTION, {KEY: dict_key})


def update():
    pass


def read() -> dict:
    """
    Our contract:
        - No arguments.
        - Returns a dictionary of text entries keyed on their key.
        - Each key must map to another dictionary containing title and text.
    """
    text_entries = dbc.read_dict(TEXT_COLLECTION, KEY)  # Fetch from MongoDB
    if not text_entries:
        text_entries = text_dict  # Fallback to default dictionary
    print(f'{text_entries=}')  # Debug log
    return text_entries


def read_one(key: str) -> dict:
    """
    Retrieve a single text entry based on the given key.
    If not found, return an empty dictionary.
    """
    result = dbc.read_one(TEXT_COLLECTION, {KEY: key})  # Fetch from MongoDB
    if result:
        return result
    return {}


def main():
    print(read())


if __name__ == '__main__':
    main()
