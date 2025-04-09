from sqlalchemy.exc import ProgrammingError

from app.db.session import engine, Base
from app.models.message import Message
from app.models.user import User

def init_db():
    """Initialize the database with required tables."""
    # Create tables
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.") 