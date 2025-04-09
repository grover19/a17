import data.db_connect as dbc
import data.text as txt

CTEST_KEY = "create_test"
UTEST_KEY = "update_test"

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
    assert txt.read_one(CTEST_KEY) == {}

    txt.create(CTEST_KEY, "testTitle", "testText")
    text = txt.read_one(CTEST_KEY)

    assert text[txt.TITLE] == 'testTitle'
    assert text[txt.TEXT] == 'testText'

    delete_result = txt.delete(CTEST_KEY)    

    assert delete_result == 1
    assert txt.read_one(CTEST_KEY) == {}

# def test_update():
#     txt.create(UTEST_KEY, "updateTitle", "updateText")
#     texts = txt.read()

#     assert UTEST_KEY in texts
#     txt.update(UTEST_KEY, "UPDATEDTitle", "updateText")
#     texts = txt.read()
#     assert texts[CTEST_KEY][txt.TITLE] == "UPDATEDTitle"
#     assert texts[CTEST_KEY][txt.TEXT] == "updateText"