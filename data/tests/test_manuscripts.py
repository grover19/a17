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

def test_transition_manuscript_state():
    test_manu = manu.create_manuscript(
        author_name="State Test Author",
        title="Transition Test Manuscript",
        text="Testing state transitions."
    )
    manu_id = str(test_manu["_id"])

    new_state = manu.transition_manuscript_state(manu_id, "REJ")
    assert new_state == "REJ"

    try:
        manu.transition_manuscript_state(manu_id, "REJ")
        assert False
    except ValueError as e:
        assert "Invalid action" in str(e)

    assert manu.delete_manuscript(manu_id) == 1

def test_full_success_path():
    test_manu = manu.create_manuscript(
        author_name="FSM Path Author",
        title="FSM Path Manuscript",
        text="Testing full FSM success path"
    )
    manu_id = str(test_manu["_id"])

    # manually move state to REV since im skipping ARF/referee logic
    dbc.update(manu.MANUSCRIPTS_COLLECT, {manu.MONGO_ID: ObjectId(manu_id)}, {
        f"{manu.LATEST_VERSION}.{manu.STATE}": "REV"
    })

    assert manu.transition_manuscript_state(manu_id, "ACCWITHREV") == "AUTHREVISION"
    assert manu.transition_manuscript_state(manu_id, "DON") == "EDREV"
    assert manu.transition_manuscript_state(manu_id, "ACC") == "CED"
    assert manu.transition_manuscript_state(manu_id, "DON") == "AUR"
    assert manu.transition_manuscript_state(manu_id, "DON") == "FORM"
    assert manu.transition_manuscript_state(manu_id, "DON") == "PUB"
    assert manu.delete_manuscript(manu_id) == 1
