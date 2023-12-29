"""This file contains a UserRepo class to work with users"""
import hashlib
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from connection_mongo import database
import uuid

# --------------------------------------------------------------------------
USER_COLLECTION = 'user'


# --------------------------------------------------------------------------

class User(BaseModel):
    """This class represents a main user model to retrieve and create users"""
    id: str = Field(default='', include=True)
    name: str = Field(default='', include=True)
    role: str = Field(default='user', include=True)
    telegram_id: Optional[int] = Field(default=-1, include=True)
    date_next_call: Optional[datetime] = Field(default=None, include=True)
    created_at: Optional[datetime] = Field(default=None, include=True)
    updated_at: Optional[datetime] = Field(default=None, include=True)


# --------------------------------------------------------------------------

class UserRepo:
    """The UserRepo class provides methods to work with MongoDB database"""

    @staticmethod
    async def get_all(params: dict | None = None) -> list[dict]:
        """This method returns all users from the database
        :param params: a dict representing the query parameters to filter the
        results
        :return: a list of dicts representing the users
        """
        if not params:
            params = {}
        params.update({'is_deleted': False})
        _items = database.get_collection(USER_COLLECTION).find(params)
        _list_items = []
        async for book in _items:
            book['id'] = str(book.pop('_id'))
            _list_items.append(book)
        return _list_items

    @staticmethod
    async def get_all_ids() -> list[str]:
        """This method returns all user ids from the database
        :return: a list of str representing the user ids
        """
        _items = database.get_collection(USER_COLLECTION).find()
        _list_items = []
        async for book in _items:
            book.pop("password")
            book.pop("avatar")
            _list_items.append(book['_id'])
        return _list_items

    @staticmethod
    async def update_query(user_id: str, user: dict) -> None:
        """This method updates a user in the database
        :param user_id: a str representing the user id to find the user by
        :param user: a dict representing the updated user data
        """
        user['updated_at'] = datetime.utcnow()
        return await database.get_collection("user").update_one(
            {"_id": user_id}, {"$set": user})

    @staticmethod
    async def update(user: User) -> None:
        """This method updates a user in the database
        :param user: a User object representing the updated user data
        """
        user.updated_at = datetime.utcnow()
        _user= user.model_dump()
        _user.pop("id")
        await database.get_collection(USER_COLLECTION).update_one(
            {"_id": user.id}, {"$set":_user})

    @staticmethod
    async def update_complete_registration(user: User) -> None:
        """This method updates a user in the database during complete
        registration process
        :param user: a User object representing the updated user data
        """
        _user = await database.get_collection(USER_COLLECTION).find_one(
            {"email": user.email})
        user.updated_at = datetime.utcnow()
        await database.get_collection("user").update_one(
            {"_id": user.id}, {"$set": _user})

    @staticmethod
    async def reset_password(id: str, password: str) -> None:
        """This method serves to reset user password
        :param id: a str representing the user id
        :param password: a str representing the new password
        """
        await database.get_collection(USER_COLLECTION).update_one({"_id": id}, {
            "$set": {"password": password, "updated_at": datetime.utcnow()}})

    @staticmethod
    async def find_one(id: int) -> User | None:
        """This method serves to find a user by id
        :param id: a str representing the user id
        :return: a User object or None if not found
        """
        _user_model = await database.get_collection(USER_COLLECTION).find_one(
            {"_id": id})
        if _user_model is None:
            return None
        _user = User.model_validate(_user_model)
        _user.id = _user_model['_id']
        return _user

    @staticmethod
    async def find_by_tg_id(tg_id: int) -> User | None:
        """This method serves to find a user by email
        :param tg_id: a str representing the user tg_id
        :return: a User object or None if not found
        """
        _user_model = await database.get_collection(USER_COLLECTION).find_one(
            {"telegram_id": tg_id})
        if _user_model is None:
            return None
        _user = User.model_validate(_user_model)
        _user.id = _user_model['_id']
        return _user

    @staticmethod
    async def find_by_name(name: str) -> User | None:
        """This method serves to find a user by email
        :param name: a str representing the user name
        :return: a User object or None if not found
        """
        _user_model = await database.get_collection(USER_COLLECTION).find_one(
            {"name": name})
        if _user_model is None:
            return None
        _user = User.model_validate(_user_model)
        _user.id = _user_model['_id']
        return _user

    @staticmethod
    async def auth(email: str, password: str) -> dict:
        """This method serves to authenticate a user by email and password
        :param email: a str representing the user email
        :param password: a str representing the user password
        :return: a dict representing the user or None if not found
        """
        password_hash_object = hashlib.sha256(password.encode())
        password_hex_dig = password_hash_object.hexdigest()

        user = await database.get_collection(USER_COLLECTION).find_one(
            {"email": email, "password": password_hex_dig, "is_deleted": False})
        if user:
            user['id'] = user['_id']
            user.pop('password')
        return user

    @staticmethod
    async def check_password(password: str) -> bool:
        """This method serves to check if a password is correct
        :param password: a str representing the user password
        :return: a bool representing if the password is correct or not
        """
        user = await database.get_collection(USER_COLLECTION).find_one(
            {"password": password})
        if user:
            return True
        return False

    @staticmethod
    async def get_locked_flags(email: str) -> dict | None:
        """This method serves to get locked flags for a user found by email
        :param email: a str representing the user email
        :return: a dict representing the locked flags or None if not found
        """
        user = await database.get_collection(USER_COLLECTION).find_one(
            {"email": email})
        if user:
            return user['locked_flags']
        else:
            return None

    @staticmethod
    async def insert(user: User) -> User:
        """This method serves to insert a new user to the database
        :param user: a User object representing the new user data
        :return: a User object representing the new user
        """
        user.id = str(uuid.uuid4())
        user.created_at = datetime.utcnow()
        user.updated_at = datetime.utcnow()
        _user = user.model_dump(exclude={})
        _user['_id'] = user.id
        _user.pop('id', None)
        await database.get_collection(USER_COLLECTION).insert_one(_user)

        return user

    @staticmethod
    async def delete_one(name: str) -> None:
        """This method serves to delete a user from the database
        :param name: a str representing the user id to delete user by
        """
        await database.get_collection(USER_COLLECTION).delete_one({"name": name})
