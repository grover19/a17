import data.db_connect as dbc
client = dbc.connect_db()
from datetime import datetime
import  data.manuscripts.states as states  
import data.people as ppl 
from bson.objectid import ObjectId


# --- Collection Names ---
MANUSCRIPTS_COLLECT = 'manuscripts'
MANUSCRIPT_HISTORY_COLLECT = 'manuscript_history'
MONGO_ID = '_id'



# --- Field Names for Manuscripts --- # 

AUTHOR = 'author'  # reference to a PERSON document
MANUSCRIPT_CREATION = 'manuscript_creation'
 # reference to a history object document
MANUSCRIPT_HISTORY_FK = 'manuscript_history' 
VERSION = 'version'  # array of version objects


# --- Fields within a Version Object ---
VERSION_CREATION = 'version_created'
TEXT = 'text'
TITLE = 'title'
STATE = 'state'



# --- Fields within a Revision Object ---
EDITORS = 'editors'

# --- Fields within an Editor Object --- #
EDITOR_PERSON = 'person'  # reference to a PERSON document
EDITOR_ROLE = 'role'
COMMENTS_OBJECT = 'comments'  # optional list of comment objects


# --- Fields names for Manuscript_History Collection --- # 
HISTORY = 'history'
MANUSCRIPT_FK = 'manuscript_id'


# establishing a mongodb connection 
dbc.connect_db() 

def get_est_time():
    return datetime.now()


# ------ HELPER FUNCTIONS ------------ 



def create_manuscript_history(manuscriptId):

    new_manuscript_history = {
        MANUSCRIPT_FK: manuscriptId,
        HISTORY: []
    }
    result = dbc.create(MANUSCRIPT_HISTORY_COLLECT, new_manuscript_history)

    if not result.acknowledged:
        raise Exception("Failed to create manuscript history document.")
    manuscript_historyId = result.inserted_id
    return manuscript_historyId



def create_simple_manuscript(author, title, text): 
    # this is a slightly modified version right now ; ill see if the ideal version works 

    new_manuscript = {
    AUTHOR: author, 
    MANUSCRIPT_CREATION: get_est_time(),
    VERSION: [
    {
        STATE: states.DEFAULT_STATE,  # initial state can be 'Draft'
        TITLE: title, 
        VERSION_CREATION: MANUSCRIPT_CREATION,
        VERSION: states.DEFAULT_VERSION,
        TEXT: text,
        EDITORS: []
    }]
    }

    # Insert manuscript
    result = dbc.create(MANUSCRIPTS_COLLECT, new_manuscript)
    if  not result.acknowledged: 
        raise Exception("Failed to create manuscript document.")
    
    manuscriptId = result.inserted_id
    return manuscriptId 


def create(author, title, text): 
    manuscriptId = create_simple_manuscript(author, title, text)
    manuscript_historyId = create_manuscript_history(manuscriptId) 

    updated_manuscript = dbc.update(
        MANUSCRIPTS_COLLECT, 
        {MONGO_ID: manuscriptId}, 
        {MANUSCRIPT_HISTORY_FK: manuscript_historyId}
    )

    str_manuscript_id = dbc.convert_mongo_id(MANUSCRIPTS_COLLECT)
    str_manuscript_historyId = dbc.convert_mongo_id(MANUSCRIPT_HISTORY_COLLECT)

    if not updated_manuscript.modified_count:
        raise Exception("Failed to update manuscript with manuscript_history_fk.")

    # Return both IDs for further processing
    return {
        "manuscript_id": str_manuscript_id,
        "manuscript_history_id": str_manuscript_historyId
    }


def read_one_manuscript(manuscript_id) -> dict:
    object_id = ObjectId(manuscript_id)

    return dbc.read_one(MANUSCRIPTS_COLLECT, {MONGO_ID: object_id})

def read(manuscript_id) -> list:
    object_id = ObjectId(manuscript_id)

    return dbc.read(MANUSCRIPTS_COLLECT, {MONGO_ID: object_id})


def delete_manuscript(manuscript_id):
    manuscript_id = ObjectId(manuscript_id)
    return dbc.delete(MANUSCRIPTS_COLLECT, {MONGO_ID: manuscript_id}) 

