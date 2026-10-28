from core.database import Base, engine

def create_tables():    
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")
