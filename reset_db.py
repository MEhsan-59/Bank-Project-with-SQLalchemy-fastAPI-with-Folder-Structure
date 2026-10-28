from core.database import Base, engine
import models

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
print("Database reset ho gaya")