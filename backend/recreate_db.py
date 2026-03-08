from app.database import engine
from app.models import Base

def migrate():
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Recreating all tables with new UUID schema...")
    Base.metadata.create_all(bind=engine)
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
