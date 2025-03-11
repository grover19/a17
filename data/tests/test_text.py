import data.db_connect as dbc
import data.text as txt

def test_read():
    texts = txt.read()
    assert isinstance(texts, dict)
    for key in texts:
        assert isinstance(key, str)

def test_read_one():
    # Ensure test data exists in MongoDB
    test_data = {
        txt.KEY: txt.TEST_KEY,
        txt.TITLE: "Home Page",
        txt.TEXT: "Sample content for testing."
    }

    if not dbc.read_one(txt.TEXT_COLLECTION, {txt.KEY: txt.TEST_KEY}):
        dbc.create(txt.TEXT_COLLECTION, test_data)

    result = txt.read_one(txt.TEST_KEY)
    print(f"DEBUG: test_read_one fetched: {result}")

    assert len(result) > 0

def test_read_one_not_found():
    assert txt.read_one('Not a page key!') == {}

def test_delete_exists():
    # 1/2 tests for the text delete()
    # test for an existing key
    # check if deletion key exists in data.text
    texts = txt.read()
    assert txt.DEL_KEY in texts

    #attempt to delete the text instance
    final_val = txt.delete(txt.DEL_KEY)

    assert txt.DEL_KEY not in final_val

def test_delete_not_exists():
    # 2/2 tests for the text delete()
    # test for a non-existing key
    phony_key = "PHONY_KEY"

    texts = txt.read()
    assert phony_key not in texts
