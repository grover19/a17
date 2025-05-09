"""
This module handles authentication-related functionality.
"""
import bcrypt
import data.db_connect as dbc
from data.models import EMAIL, ROLES, PASSWORD

PEOPLE_COLLECT = 'people'
SALT_ROUNDS = 12  # Number of rounds for bcrypt

def hash_password(password: str) -> bytes:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(SALT_ROUNDS))

def verify_password(password: str, hashed: bytes) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def authenticate_user(email: str, password: str) -> dict:
    """
    Authenticate a user with email and password.
    Returns user data if authentication successful, None otherwise.
    """
    # Get user with password hash included
    user = dbc.read_one(PEOPLE_COLLECT, {EMAIL: email})
    if not user:
        return None
    
    stored_hash = user.get(PASSWORD)
    if not stored_hash:
        return None
    
    # Convert stored_hash to bytes if it's a string
    if isinstance(stored_hash, str):
        stored_hash = stored_hash.encode('utf-8')
        
    if verify_password(password, stored_hash):
        # Don't include the password hash in the return value
        return {
            EMAIL: user[EMAIL],
            ROLES: user.get(ROLES, [])  # Use get() with default empty list
        }
    
    return None 