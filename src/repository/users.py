import logging
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar
from sqlalchemy.orm import joinedload

from src.database.db import get_db
from src.entity.models import User, Role
from src.schemas.user import UserSchema, UserProfileResponse, UserUpdateSchema

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

async def get_user_by_email(email: str, db: AsyncSession):
    """
    The get_user_by_email function returns a user object from the database based on the email address provided.
        If no user is found, None is returned.
    
    :param email: str: Specify the email of the user we want to get
    :param db: AsyncSession: Pass the database session to the function
    :return: A user object
    :doc-author: Trelent
    """
    stmt = select(User).filter_by(email=email)
    result = await db.execute(stmt)
    user = result.scalars().first()
    return user


async def create_user(body: UserSchema, role: Role, db: AsyncSession = Depends(get_db)) -> User:
    """
    The create_user function creates a new user in the database.
        It takes a UserSchema object as input and returns the newly created user.
    
    :param body: UserSchema: Deserialize the request body into a userschema object
    :param db: AsyncSession: Pass in the database session to be used
    :return: A user object, which is then serialized into a json response
    :doc-author: Trelent
    """
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as err:
        print(err)

    new_user = User(
        username=body.username,
        email=body.email,
        password=body.password,
        role=role,
        avatar=avatar
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def update_token(user: User, token: str | None, db: AsyncSession):
    """
    The update_token function updates the user's refresh token in the database.
    
    :param user: User: Get the user object from the database
    :param token: str | None: Set the refresh_token field of the user
    :param db: AsyncSession: Commit the changes to the database
    :return: Nothing, so it should be declared as returning none
    :doc-author: Trelent
    """
    user.refresh_token = token
    await db.commit()


async def confirmed_email(email: str, db: AsyncSession) -> None:
    """
    The confirmed_email function marks a user as confirmed in the database.
    
    :param email: str: Pass the email of the user to be confirmed
    :param db: AsyncSession: Pass the database connection to the function
    :return: None, so the return type is none
    :doc-author: Trelent
    """
    user = await get_user_by_email(email, db)
    user.confirmed = True
    await db.commit()


async def update_avatar_url(email: str, url: str | None, db: AsyncSession) -> User:
    """
    The update_avatar_url function updates the avatar url of a user.
    
    :param email: str: Get the user by email
    :param url: str | None: Specify the new avatar url
    :param db: AsyncSession: Pass the database session to the function
    :return: The updated user object
    :doc-author: Trelent
    """
    user = await get_user_by_email(email, db)
    user.avatar = url
    await db.commit()
    await db.refresh(user)
    return user


async def get_user_by_username(username: str, db: AsyncSession) -> User:
    """
    The get_user_by_username function retrieves a user object from the database based on the username provided.
    
    :param username: str: Specify the username of the user to retrieve
    :param db: AsyncSession: Pass the database session to the function
    :return: A user object or None if not found
    :doc-author: Trelent
    """
    
    logger.info("Fetching user by username: %s", username)
    stmt = select(User).filter_by(username=username)
    result = await db.execute(stmt)
    user = result.scalars().first()
    if user:
        logger.info("User found: %s", user.username)
    else:
        logger.warning("User not found: %s", username)
    return user


async def get_user_profile(username: str, db: AsyncSession) -> UserProfileResponse:
    """
    The get_user_profile function retrieves a user's profile based on the username provided.
    
    :param username: str: Specify the username of the user to retrieve the profile for
    :param db: AsyncSession: Pass the database session to the function
    :return: A UserProfileResponse object or None if the user is not found
    :doc-author: Trelent
    """
    logger.info("Fetching profile for user: %s", username)
    user = await get_user_by_username(username, db)
    if user is None:
        logger.warning("User profile not found: %s", username)
        return None
    photo_count = len(user.photos) if user.photos else 0
    user_profile = UserProfileResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        avatar=user.avatar,
        created_at=user.created_at,
        updated_at=user.updated_at,
        confirmed=user.confirmed,
        role=user.role,
        photo_count=photo_count 
    )
    logger.info("Profile fetched for user: %s", username)
    return user_profile

async def update_own_profile(body: UserUpdateSchema, user: User, db: AsyncSession):
    """
    The update_own_profile function updates the profile of the currently authenticated user.
    
    :param body: UserUpdateSchema: The new profile data
    :param user: User: The current user object
    :param db: AsyncSession: Pass the database session to the function
    :return: A UserProfileResponse object with the updated profile information
    :doc-author: Trelent
    """
    logger.info("Updating profile for user: %s", user.username)
    
    existing_user = await get_user_by_username(user.username, db)
    if existing_user is None:
        logger.warning("User not found for update: %s", user.username)
        return None
    
    try:
        if body.username and body.username != user.username:
            user.username = body.username
        
        if body.password:
            from src.services.auth import auth_service
            user.password = auth_service.get_password_hash(body.password)

        await db.commit()
        await db.refresh(user)
        
        photo_count = len(user.photos) if user.photos else 0
        user_profile = UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            avatar=user.avatar,
            created_at=user.created_at,
            updated_at=user.updated_at,
            confirmed=user.confirmed,
            role=user.role, 
            photo_count=photo_count 
        )
        
        logger.info("Profile updated for user: %s", user.username)
        return user_profile
    
    except Exception as e:
        logger.error("Error updating profile for user: %s, error: %s", user.username, str(e))
        await db.rollback()
        return None