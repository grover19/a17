import data.db_connect as dbc
import data.manuscripts.manuscripts as manu
from bson.objectid import ObjectId

def test_delete_exists():
    # Create a test manuscript
    test_manuscript = manu.create_manuscript(
        author_name="Test Author",
        title="Test Manuscript",
        text="This is a test manuscript."
    )

    manu_id = test_manuscript["_id"]

    # Ensure the manuscript exists
    assert manu.read_one_manuscript(manu_id) is not None

    # Attempt to delete the manuscript
    delete_result = manu.delete_manuscript(manu_id)
    assert delete_result == 1

    # Ensure the manuscript no longer exists
    assert manu.read_one_manuscript(manu_id) is None

def test_delete_not_exists():
    # Generate a non-existent manuscript ID
    fake_manu_id = ObjectId()

    # Attempt to delete a non-existent manuscript
    delete_result = manu.delete_manuscript(fake_manu_id)
    assert delete_result == 0

def test_create_manuscript():
    # Create a new manuscript
    test_data = {
        "author_name": "Test Author",
        "title": "Test Manuscript",
        "text": "This is a test manuscript."
    }
    
    created_manuscript = manu.create_manuscript(**test_data)
    
    # Ensure manuscript creation was successful
    assert created_manuscript is not None
    assert "_id" in created_manuscript

    manu_id = created_manuscript["_id"]
    
   