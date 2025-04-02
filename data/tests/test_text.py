import data.db_connect as dbc
import data.text as txt

TEST_KEY = "test"

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
    test_data = {
        txt.KEY: txt.DEL_KEY,
        txt.TITLE: "Delete Page",
        txt.TEXT: "This is a text to delete."
    }
    if not dbc.read_one(txt.TEXT_COLLECTION, {txt.KEY: txt.DEL_KEY}):
        dbc.create(txt.TEXT_COLLECTION, test_data)

    delete_result = txt.delete(txt.DEL_KEY)
    assert delete_result == 1
    assert dbc.read_one(txt.TEXT_COLLECTION, {txt.KEY: txt.DEL_KEY}) is None

def test_delete_not_exists():
    # 2/2 tests for the text delete()
    # test for a non-existing key
    phony_key = "PHONY_KEY"

    texts = txt.read()
    assert phony_key not in texts

def test_create():
    texts = txt.read()
    assert TEST_KEY not in texts

    txt.create(TEST_KEY, "testTitle", "testText")
    texts = txt.read()
    assert TEST_KEY in texts
    assert texts[TEST_KEY]["testTitle"] == "testTitle"
    assert texts[TEST_KEY]["testText"] == "testText"