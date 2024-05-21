from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from sqlalchemy.orm import declarative_base
Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    username = Column(String, primary_key=True)
    hashed_password = Column(String, nullable=False)
    permissions = Column(String, nullable=False)


class SimpleAuth:
    def __init__(self, db_url):
        # Configure passlib context
        self.pwd_context = CryptContext(
            schemes=["pbkdf2_sha256"], deprecated="auto")

        # Set up the database engine
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)

        # Create a session factory bound to this engine
        self.Session = sessionmaker(bind=self.engine)

    def verify_user(self, username, password):
        """ Verify user's password against the stored hash. """
        session = self.Session()
        try:
            user = session.query(User).filter(
                User.username == username).first()
            if user is None:
                return False
            return self.pwd_context.verify(password, user.hashed_password)
        finally:
            session.close()

    def add_user(self):

        users = [
            {"username": "kaxa", "password": "pass", "permissions": "admin"},
        ]

        # Insert users into the database with hashed passwords
        for user in users:
            with self.Session() as session:
                hashed_password = self.pwd_context.hash(user["password"])
                new_user = User(username=user["username"],
                                hashed_password=hashed_password,
                                permissions=user['permissions'])
                session.add(new_user)
                session.commit()
                session.close()
                print("Users added successfully.")


# auth = SimpleAuth('postgresql://postgres:postgres@10.4.21.11:5432/postgres')
# auth.add_user()
