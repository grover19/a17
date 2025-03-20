"""
This module interfaces to our user data.
"""

# import data.db_connect as dbc
# fields
import data.db_connect as dbc

KEY = 'key'
TITLE = 'title'
TEXT = 'text'
EMAIL = 'email'

TEST_KEY = 'HomePage'
SUBM_KEY = 'SubmissionsPage'
DEL_KEY = 'DeletePage'
TEXT_COLLECTION = 'text'


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

# set up db client
dbc.connect_db()


def create(key, title, text):
    document = {KEY: key, TITLE: title, TEXT: text}
    try:
        # check if key already exists
        if dbc.read_one(TEXT_COLLECTION, {KEY: key}):
            raise KeyError(f'{key} already exists')

        dbc.create(TEXT_COLLECTION, document)

        return dbc.read_one(TEXT_COLLECTION, {KEY: key})

    except Exception as e:
        print(f"Create Text Error {str(e)}")


def delete(key):
    text_collect = dbc.read_one(TEXT_COLLECTION, {KEY: key})
    if not text_collect:
        return 0
    return dbc.delete(TEXT_COLLECTION, {KEY: key})


def update(key: str, title: str, text: str):
    """
    Update an existing page in text_dict.

    Arguments:
        key (str): The key identifying the page.
        title (str): The new title of the page.
        text (str): The new text content of the page.

    Returns:
        str: The key of the updated page.

    Raises:
        ValueError: If the key does not exist in text_dict.
    """
    existing = dbc.read_one(TEXT_COLLECTION, {KEY: key})
    if not existing:
        raise ValueError(f"Updating non-existent page: key='{key}'")

    result = dbc.update_one(
        TEXT_COLLECTION,
        {KEY: key},
        {"$set": {TITLE: title, TEXT: text}}
    )

    if result.matched_count == 0:
        raise ValueError(f"Failed to update: key='{key}' not found")
    return key


def read():
    """
    Our contract:
        - No arguments.
        - Returns a dictionary of users keyed on user email.
        - Each user email must be the key for another dictionary.
    """
    text = text_dict
    return text


def read_all_texts():
    return dbc.read(TEXT_COLLECTION, dbc.SE_DB, False)


def read_one(key: str) -> dict:
    # This should take a key and return the page dictionary
    # for that key. Return an empty dictionary of key not found.
    text_doc = dbc.read_one(TEXT_COLLECTION, {KEY: key})
    if not text_doc:
        return {}
    return text_doc


def main():
    print(read())


if __name__ == '__main__':
    main()
