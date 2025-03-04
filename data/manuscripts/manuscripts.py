import sys
import os
from datetime import datetime, timezone
from bson import ObjectId

# this is because db_connect.py is located one directory above 
# yes, you could also just do ../data 
hey = sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
print(hey)
import data.db_connect as dbc

# Collection names for the normalized data
COLLECTION_MANUSCRIPTS = "manuscripts"
COLLECTION_REVISIONS = "manuscript_revisions"
COLLECTION_HISTORY = "manuscript_history"
COLLECTION_REFEREES = "manuscript_referees"




# OPINION NEEDED... 
# it might also be helpful to do something like 
# define a global variable: 

# SUBMITTED_STATE = "SUBMITTED"
# REVIEW_STATE = "Review"
# ... 
# then : 

# ALLOWED_TRANSITION = {
#     SUBMITTED_STATE: ["Referee Review", "Rejected", "Withdrawn"],
#     ... 
# }
 
ALLOWED_TRANSITIONS = {
   "Submitted": ["Referee Review", "Rejected", "Withdrawn"],
   "Referee Review": ["Author Revisions", "Rejected", "Withdrawn"],
   "Author Revisions": ["Editor Review", "Withdrawn"],
   "Editor Review": ["Copy Edit", "Withdrawn"],
   "Copy Edit": ["Author Review", "Withdrawn"],
   "Author Review": ["Formatting", "Withdrawn"],
   "Formatting": ["Published", "Withdrawn"],
   "Published": [],
   "Rejected": [],
   "Withdrawn": []
}


def create_manuscript(title, author, author_email, text, abstract):
   """
   Create a new manuscript:
     - Insert a document in manuscripts.
     - Insert an initial revision.
     - Insert an initial history record.
   """
   client = dbc.connect_db()
   db = client[dbc.SE_DB]
   now = datetime.now(timezone.utc)

   # Set the initial state as "Submitted"
   manuscript_doc = {
       "title": title,
       "author": author,
       "author_email": author_email,
       "state": "Submitted",
       "editor": None,
       "latest_version": 1,
       "created_at": now,
       "updated_at": now
   }

   ms_result = db[COLLECTION_MANUSCRIPTS].insert_one(manuscript_doc)
   ms_id = ms_result.inserted_id

   # Insert initial revision document
   revision_doc = {
       "manuscript_id": ms_id,
       "version": 1,
       "text": text,
       "abstract": abstract,
       "timestamp": now,
       "review_round": 0,
       "referee_comments": [],
       "author_response": None
   }
   db[COLLECTION_REVISIONS].insert_one(revision_doc)

   # Insert initial history record (no previous state)
   history_entry = {
       "manuscript_id": ms_id,
       "from_state": None,
       "to_state": "Submitted",
       "timestamp": now,
       "actor": author_email
   }
   db[COLLECTION_HISTORY].insert_one(history_entry)

   client.close()

   # this is for testing purposes only! 
   return str(ms_id)

