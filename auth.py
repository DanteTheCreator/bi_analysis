from sqlalchemy import create_engine, Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    username = Column(String, primary_key=True)
    hashed_password = Column(String, nullable=False)

class SimpleAuth:
    def __init__(self, db_url):
        # Configure passlib context
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        # Set up the database engine
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)

        # Create a session factory bound to this engine
        self.Session = sessionmaker(bind=self.engine)

    # def register_user(self, username, password):
    #     """ Register a new user with a hashed password. """
    #     session = self.Session()
    #     try:
    #         if session.query(User).filter(User.username == username).first():
    #             raise ValueError("Username already exists")

    #         hashed_password = self.pwd_context.hash(password)
    #         new_user = User(username=username, hashed_password=hashed_password)
    #         session.add(new_user)
    #         session.commit()
    #         return True
    #     except:
    #         session.rollback()
    #         raise
    #     finally:
    #         session.close()

    def verify_user(self, username, password):
        """ Verify user's password against the stored hash. """
        session = self.Session()
        try:
            user = session.query(User).filter(User.username == username).first()
            if user is None:
                return False
            return self.pwd_context.verify(password, user.hashed_password)
        finally:
            session.close()
