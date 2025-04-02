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
    # Test data
    test_data = {
        "author_name": "Test Author",
        "title": "Test Manuscript",
        "text": "This is a test manuscript."
    }

    # Create manuscript
    created = manu.create_manuscript(**test_data)
    assert created and "_id" in created, "Manuscript creation failed"

    manu_id = created["_id"]

    # Retrieve manuscript
    retrieved = manu.read_one_manuscript(manu_id)
    assert retrieved, "Manuscript not found in database"
    
    # Validate fields
    assert retrieved.get("author") == test_data["author_name"], "Author mismatch"
    assert retrieved.get("latest_version", {}).get("title") == test_data["title"], "Title mismatch"
    assert retrieved.get("latest_version", {}).get("text") == test_data["text"], "Text mismatch"

    # Cleanup
    assert manu.delete_manuscript(manu_id) == 1, "Failed to delete manuscript"
    assert manu.read_one_manuscript(manu_id) is None, "Manuscript was not deleted"