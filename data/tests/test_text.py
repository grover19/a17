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
