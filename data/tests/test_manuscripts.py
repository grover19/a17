import data.db_connect as dbc
import data.manuscripts.manuscripts as manu
from bson.objectid import ObjectId
import pytest

@pytest.fixture
def sample_manuscript():
    test_manu = manu.create_manuscript(
        author_name="Test Author",
        title="Test Manuscript",
        text="This is a test manuscript."
    )
    yield test_manu
    manu.delete_manuscript(test_manu["_id"])

@pytest.fixture
def fsm_manuscript():
    test_manu = manu.create_manuscript(
        author_name="FSM Path Author",
        title="FSM Path Manuscript",
        text="Testing full FSM success path"
    )
    yield test_manu
    manu.delete_manuscript(test_manu["_id"])

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

def test_transition_manuscript_state(sample_manuscript):
    manu_id = str(sample_manuscript["_id"])
    assert manu.transition_manuscript_state(manu_id, "ARF", ref="ref1") == "REV"

    with pytest.raises(ValueError, match="Invalid action"):
        manu.transition_manuscript_state(manu_id, "BAD_ACTION")

def test_full_success_path(fsm_manuscript):
    manu_id = str(fsm_manuscript["_id"])
    assert manu.transition_manuscript_state(manu_id, "ARF", ref="ref1") == "REV"
    assert manu.transition_manuscript_state(manu_id, "ACCWITHREV") == "AUTHREVISION"
    assert manu.transition_manuscript_state(manu_id, "DON") == "EDREV"
    assert manu.transition_manuscript_state(manu_id, "ACC") == "CED"
    assert manu.transition_manuscript_state(manu_id, "DON") == "AUR"
    assert manu.transition_manuscript_state(manu_id, "DON") == "FORM"
    assert manu.transition_manuscript_state(manu_id, "DON") == "PUB"
