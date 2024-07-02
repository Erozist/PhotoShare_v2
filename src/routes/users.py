import pickle
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.entity.models import User,Role
from src.schemas.user import UserResponse, UserProfileResponse,UserUpdateSchema
from src.services.auth import auth_service
from src.services.cloudinary import upload_image
from src.repository import users as repositories_users
from src.services.roles import RoleAccess


router = APIRouter(prefix="/users", tags=["users"])

access_to_route_all = RoleAccess([Role.admin, Role.moderator])
access_to_route_admin = RoleAccess([Role.admin])


@router.get(
    "/me",
    response_model=UserResponse,
    dependencies=[Depends(RateLimiter(times=1, seconds=60))],
)
async def get_current_user(user: User = Depends(auth_service.get_current_user)):
    """
    The get_current_user function is a dependency that will be injected into the
        get_current_user endpoint. It uses the auth_service to retrieve the current user,
        and returns it if found.
    
    :param user: User: Get the user object from the auth_service
    :return: The current user
    :doc-author: Trelent
    """
    return user


@router.patch("/avatar", response_model=UserResponse, dependencies=[Depends(RateLimiter(times=1, seconds=60))],)
async def update_avatar(file: UploadFile = File(), user: User = Depends(auth_service.get_current_user),
                        db: AsyncSession = Depends(get_db)):
    """
    The update_avatar function is used to update the avatar of a user.
        The function takes in an UploadFile object, which contains the file that will be uploaded to Cloudinary.
        It also takes in a User object, which is obtained from auth_service's get_current_user function. This ensures that only authenticated users can access this endpoint and change their own avatar image.
        Finally, it takes in an AsyncSession object for database access.
    
    :param file: UploadFile: Get the file from the request
    :param user: User: Get the current user
    :param db: AsyncSession: Get the database session
    :return: A user object
    :doc-author: Trelent
    """
    res_url = upload_image(file.file)
    user = await repositories_users.update_avatar_url(user.email, res_url, db)
    auth_service.cache.set(user.email, pickle.dumps(user))
    auth_service.cache.expire(user.email, 300)
    return user


@router.get("/profile/{username}", response_model=UserProfileResponse)
async def get_user_profile(username: str, db: AsyncSession = Depends(get_db),current_user: User = Depends(auth_service.get_current_user)):
    """
    The get_user_profile function retrieves a user's profile based on the username provided.
    
    :param username: str: Specify the username of the user to retrieve the profile for
    :param db: AsyncSession: Pass the database session to the function
    :param current_user: User: Get the current user making the request
    :return: A UserProfileResponse object or None if the user is not found
    :doc-author: Trelent
    """
    user_profile =  await repositories_users.get_user_profile(username, db)
    if user_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user_profile


@router.put("/profile/me", response_model=UserProfileResponse)
async def update_own_profile(body: UserUpdateSchema,user: User = Depends(auth_service.get_current_user),db: AsyncSession = Depends(get_db)):
    """
    The update_own_profile function updates the profile of the currently authenticated user.
    
    :param body: UserUpdateSchema: The new profile data
    :param user: User: The current user object
    :param db: AsyncSession: Pass the database session to the function
    :return: A UserProfileResponse object with the updated profile information
    :doc-author: Trelent
    """
    user_profile =  await repositories_users.update_own_profile(body,user, db,)
    if user_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user_profile


@router.put("/admin/ban/{user_id}",dependencies=[Depends(access_to_route_all)],response_model=dict)
async def ban_user(user_id: int, user: User = Depends(auth_service.get_current_user), db: AsyncSession = Depends(get_db)):
    """
    The ban_user function deactivates a user by setting their is_active status to False.
    
    :param user_id: int: The ID of the user to be banned
    :param user: User: Get the current user
    :param db: AsyncSession: Pass the database session to the function
    :return: A dictionary with a message indicating the user has been banned or None if the user is not found
    :doc-author: Trelent
    """
    user_in_db =  await repositories_users.ban_user( user_id , db)
   
    if user_in_db is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user_in_db
