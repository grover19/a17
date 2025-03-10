# -- ALLOWED STATES -- # 

SUBMITTED = "Submitted"
DEFAULT_STATE = SUBMITTED 
DEFAULT_VERSION = 1
REFEREE_REVIEW = "Referee Review"
EDITOR_REVIEW = "Editor Review"
COPY_EDIT = "Copy Edit"
AUTHOR_REVISIONS = "Author Revisions"
AUTHOR_REVIEW = "AUTHOR REVIEW"

FORMATTING = "Formatting"
PUBLISHED =  "Published"
REJECTED =  "Rejected"
WITHDRAWN = "Withdrawn"

possible_states = [
    SUBMITTED, 
    EDITOR_REVIEW, 
    COPY_EDIT, 
    AUTHOR_REVIEW, 
    FORMATTING, 
    PUBLISHED, 
    REJECTED, 
    WITHDRAWN
]

# --- Allowed state transitions ---

allowed_transitions = {
    SUBMITTED: [REFEREE_REVIEW, WITHDRAWN],
    REFEREE_REVIEW: [AUTHOR_REVISIONS, COPY_EDIT, REJECTED], 
    AUTHOR_REVISIONS: [EDITOR_REVIEW, WITHDRAWN], 
    EDITOR_REVIEW:  [COPY_EDIT, WITHDRAWN], 
    COPY_EDIT: [AUTHOR_REVIEW, WITHDRAWN], 
    FORMATTING: [PUBLISHED, WITHDRAWN], 
    REJECTED: [WITHDRAWN],  # im not sure how this works, what if it got rejected, but the author wants it checked again with NEW authors?  should he create a new manuscript? 
    WITHDRAWN: []
} 


