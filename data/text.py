"""
This module interfaces to our user data.
"""
# fields
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


def create():
    pass


def delete():
    print(f'{KEY=}, {dict_key=}')
    return dbc.delete(TEXT_COLLECTION, {KEY: dict_key})


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
    if key not in text_dict:
        raise ValueError(f'Updating non-existent page: {key=}')

    text_dict[key] = {TITLE: title, TEXT: text}
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
