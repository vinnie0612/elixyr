from datetime import datetime

import bcrypt
from sqlalchemy import (Column, DateTime, ForeignKey, Integer, String,
                        create_engine)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

# Create the SQLAlchemy engine
engine = create_engine('sqlite:///db/elixyr.db')
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()


# Define the User model
class User(Base):
    __tablename__ = 'users'

    user_id = Column(String, primary_key=True)
    username = Column(String(50), unique=True)
    registered_at = Column(DateTime, default=datetime.now)
    password_hash = Column(String(60))  # Store the hashed password
    images = relationship("Image", backref="user")  # Relationship to Image model

    def set_password(self, password):
        # Hash the password and store the hash
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        self.password_hash = password_hash.decode('utf-8')

    def check_password(self, password):
        # Check if the provided password matches the stored hash
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))


# Define the Image model
class Image(Base):
    __tablename__ = 'images'

    image_id = Column(String, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    upload_time = Column(DateTime, default=datetime.now)


# Create the users and images tables in the database
Base.metadata.create_all(engine)


# User registration function
def register(username, password, user_id):
    user = User(username=username, user_id=user_id)
    user.set_password(password)  # Set the hashed password
    session.add(user)
    session.commit()


# User login function
def login(username, password):
    user = session.query(User).filter_by(username=username).first()
    if user and user.check_password(password):  # Check the password
        return user
    else:
        return None


# Image upload function
def add_image(image_id, user_id):
    image = Image(user_id=user_id, image_id=image_id)
    session.add(image)
    session.commit()


def delete_image(image_id, user_id):
    image = session.query(Image).filter_by(image_id=image_id, user_id=user_id).first()
    if image:
        session.delete(image)
        session.commit()
        return True
    else:
        return False


def get_images(user_id):
    images = session.query(Image).filter_by(user_id=user_id).all()
    return [f'{image.image_id}' for image in images]
