"""
This module interfaces to our user data.
"""

import data.db_connect as dbc

# fields
KEY = 'key'
TITLE = 'title'
TEXT = 'text'
EMAIL = 'email'

TEXT_COLLECT = 'text'

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
    if dbc.read_one(TEXT_COLLECT, {KEY: key}):
        raise KeyError(f"Key '{key}' already exists in the database.")
    
    # Build the document following our schema.
    document = {KEY: key, TITLE: title, TEXT: text}
    
    # Insert the document into the collection.
    dbc.create(TEXT_COLLECT, document)
    return True




def delete(dict_key: str):
    print(f'{KEY=}, {dict_key=}')
    return dbc.delete(TEXT_COLLECT, {KEY: dict_key})


def update():
    pass


def read():
    """
    Our contract:
        - No arguments.
        - Returns a dictionary of users keyed on user email.
        - Each user email must be the key for another dictionary.
    """
    text = text_dict
    return text


def read_one(key: str) -> dict:
    # This should take a key and return the page dictionary
    # for that key. Return an empty dictionary of key not found.
    result = {}
    if key in text_dict:
        result = text_dict[key]
    return result


def main():
    print(read())


if __name__ == '__main__':
    main()
    
def main():
    print(read())


if __name__ == '__main__':
    main()
