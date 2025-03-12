import data.db_connect as dbc
from datetime import datetime
import  data.manuscripts.states as states  
import data.people as ppl 
from bson.objectid import ObjectId
from copy import deepcopy



# --- Collection Names ---
MANUSCRIPTS_COLLECT = 'manuscripts'
MANUSCRIPT_HISTORY_COLLECT = 'manuscript_history'


# --- MANUSCRIPTS COLLECT --- # 
AUTHOR_FK = "author_fk"
AUTHOR_NAME = 'author'  # reference to a PERSON document
MANUSCRIPT_CREATED = 'manuscript_created'
MANUSCRIPT_HISTORY_FK = 'manuscript_history_fk' 
LATEST_VERSION = 'latest_version'  # array of version objects
STATE = 'state'
TITLE = 'title'
VERSION = 'version'
TEXT = 'text'
EDITORS = 'editors' 
EDITOR_COMMENTS = 'editor_comments'


# --- EDITORS --- #
EDITOR_FK = 'editor_fk' 
EDITOR_NAME = 'editor_name'
EDITOR_ROLE = 'role'
EDITOR_COMMENTS = 'comments'

# --- MANUSCRIPT HISTORY COLLECT  --- # 
MANUSCRIPT_FK = 'manuscript_id_fk'
HISTORY = 'history'


# --- ADDITIONAL KEY --- # 
PEOPLE_FK = 'person'
MONGO_ID = '_id'

# ---  DATABASE COMMANDS ----  #
PUSH = '$push'
SET = '$set'


# establishing a mongodb connection 
dbc.connect_db() 

def get_est_time():
    return datetime.now()


def create_mongo_id_object(doc_identifier): 
    if type(doc_identifier) == ObjectId: 
        return doc_identifier

    """
    takes in a type string and converts it to type ObjectId
    
    """
    return ObjectId(doc_identifier)


# ------ HELPER FUNCTIONS ------------ 

def create_manuscript_history(manu_id): 

    his_template = {
        MANUSCRIPT_FK: create_mongo_id_object(manu_id),
        HISTORY: []
    }

    his_insert = dbc.create(MANUSCRIPT_HISTORY_COLLECT, his_template)

    if not his_insert:
        raise Exception("Failed to create manuscript history document.")
    
    return dbc.read_one(MANUSCRIPT_HISTORY_COLLECT, {MONGO_ID: his_insert.inserted_id})
    

def create_simple_manuscript(author_name,  title, text): 


    manu_template = {
    AUTHOR_NAME: author_name, 
    MANUSCRIPT_CREATED: get_est_time(),
    LATEST_VERSION: 
        {
            STATE: states.DEFAULT_STATE,  # initial state can be 'Draft'
            TITLE: title, 
            VERSION: states.DEFAULT_VERSION,
            TEXT: text,
            EDITORS: {}, 
            EDITOR_COMMENTS: {}
        }
    }

    
    manu_insert = dbc.create(MANUSCRIPTS_COLLECT, manu_template)

    if  not manu_insert.acknowledged: 
        raise Exception("Failed to create manuscript document.")
    
    return manu_insert 



def create_manuscript(author_name, title, text): 
    manu_insert = create_simple_manuscript(author_name, title, text)
    manu_id = manu_insert.inserted_id

    his = create_manuscript_history(manu_id) 
    his_id = create_mongo_id_object(his[MONGO_ID]) 

    # mongoDB automatically creates a new field "manuscript_history"
    # if it doesn't already exist  

    filters = { 
        MONGO_ID: manu_id
    }

    update_dict = {
        MANUSCRIPT_HISTORY_FK: his_id
    }

    manu_updated = dbc.update(
        MANUSCRIPTS_COLLECT, 
        filters, 
        update_dict
    )

    if  not manu_updated.acknowledged: 
        raise Exception("Failed to create manuscript document.")

    return dbc.read_one(MANUSCRIPTS_COLLECT, {MONGO_ID: manu_id})


def read_one_manuscript(manu_id) :
    manu_obj_id = ObjectId(manu_id)
    return dbc.read_one(MANUSCRIPTS_COLLECT, {MONGO_ID: manu_obj_id})


def delete_manuscript_history(his_id):
    his_id = ObjectId(his_id)
    return dbc.delete(MANUSCRIPT_HISTORY_COLLECT, {MONGO_ID: his_id})


def delete_manuscript(manu_id):

    # MUST ALSO DELETE IT'S ASSOCIATED HISTORY!!
    manu_id = ObjectId(manu_id)
    manu = dbc.read_one(MANUSCRIPTS_COLLECT, {MONGO_ID: manu_id })

    # If manuscript doesn't exist, return 0
    if not manu:
        return 0

    his_id = manu[MANUSCRIPT_HISTORY_FK]

    # trigger 
    his_delete = delete_manuscript_history(his_id)

    manu_delete = dbc.delete(MANUSCRIPTS_COLLECT, {MONGO_ID: manu_id}) 
                                  
    return manu_delete


def read_one_manuscript_history(his_id) -> dict:
    his_obj_id = create_mongo_id_object(his_obj_id)
    return dbc.read_one(MANUSCRIPT_HISTORY_COLLECT, {MONGO_ID: his_obj_id})
