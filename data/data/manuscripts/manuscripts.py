"""
This module handles manuscript operations.
"""
from bson import ObjectId
from datetime import datetime
import data.db_connect as dbc

MANUSCRIPTS_COLLECT = 'manuscripts'
AUTHOR_NAME = 'author'
TITLE = 'title'
TEXT = 'text'
LATEST_VERSION = 'latest_version'
STATUS = 'status'
COMMENT = 'comment'
ACTION_DATE = 'action_date'

# Valid manuscript statuses
STATUS_PENDING = 'pending'
STATUS_ACCEPTED = 'accept'
STATUS_REJECTED = 'reject'
STATUS_REVISE = 'revise'

def process_manuscript_action(manuscript_id: str, action: str, comment: str = None) -> dict:
    """
    Process an action (accept/reject/revise) on a manuscript.
    
    Args:
        manuscript_id: The ID of the manuscript
        action: The action to take (accept/reject/revise)
        comment: Optional comment about the action
    
    Returns:
        The updated manuscript document
    """
    try:
        # Convert string ID to ObjectId
        manu_obj_id = ObjectId(manuscript_id)
        
        # Get the current manuscript
        manuscript = read_one_manuscript(manuscript_id)
        if not manuscript:
            return None
            
        # Update the manuscript with new status and comment
        update_data = {
            'status': action,
            'comment': comment if comment else '',
            'action_date': datetime.utcnow()
        }
        
        # Update the manuscript in the database
        dbc.update(MANUSCRIPTS_COLLECT, 
                  {'_id': manu_obj_id},
                  {'$set': update_data})
        
        # Return the updated manuscript
        return read_one_manuscript(manuscript_id)
        
    except Exception as e:
        print(f"Error processing manuscript action: {str(e)}")
        return None

// ... existing code ... 