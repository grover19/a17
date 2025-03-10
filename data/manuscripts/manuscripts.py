import data.db_connect as dbc
client = dbc.connect_db()
from datetime import datetime
import  data.manuscripts.states as states  
import data.people as ppl 

# --- Collection Names ---
MANUSCRIPTS_COLLECT = 'manuscripts'
MANUSCRIPT_HISTORY_COLLECT = 'manuscript_history'



# --- Field Names for Manuscripts --- # 

AUTHOR = 'author'  # reference to a PERSON document
TITLE = 'title'
MANUSCRIPT_CREATION = 'manuscript_creation'
 # reference to a history object document
MANUSCRIPT_HISTORY_FK = 'manuscript_history' 
STATE = 'state'
VERSION = 'version'  # array of version objects


# --- Fields within a Version Object ---
VERSION_CREATION = 'version_created'
TEXT = 'text'


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
    TITLE: title,
    MANUSCRIPT_CREATION: get_est_time(),
    STATE: states.DEFAULT_STATE,  # initial state can be 'Draft'
    VERSION: [
    {
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


def create_manuscript(author, title, text): 
    manuscriptId = create_simple_manuscript(author, title, text)
    manuscript_historyId = create_manuscript_history(manuscriptId) 
    
    updated_manuscript = dbc.update(
        MANUSCRIPTS_COLLECT, 
        {"_id": manuscriptId}, 
        {MANUSCRIPT_HISTORY_FK: manuscript_historyId}
    )
    
    if not updated_manuscript.modified_count:
        raise Exception("Failed to update manuscript with manuscript_history_fk.")
    
    # Return both IDs for further processing
    return {
        "manuscript_id": manuscriptId,
        "manuscript_history_id": manuscript_historyId
    }






















