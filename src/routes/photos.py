import logging
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from src.database.db import get_db
from src.entity.models import User, Role
from src.schemas.photo import PhotoCreate, PhotoUpdate, PhotoResponse2, PhotoBase, PhotoResponse, TransformationParams
from src.services.auth import auth_service
from src.services.cloudinary import upload_image, transform_image
from src.repository.photos import create_photo, update_photo, delete_photo, get_photo, get_photos, add_tags_to_photo, remove_tags_from_photo, generate_qr_code


router = APIRouter(prefix='/photos', tags=['photos'])

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


@router.post("/", response_model=PhotoBase, status_code=status.HTTP_201_CREATED)
async def upload_photo(
    description: Optional[str] = None,
    file: UploadFile = File(...),
    tags: List[str] = [],
    user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    The upload_photo function uploads a new photo with an optional description and tags.

    :param description: Optional[str]: The description of the photo
    :param file: UploadFile: The file object of the photo to be uploaded
    :param tags: List[str]: A list of tags associated with the photo
    :param user: User: The current user uploading the photo
    :param db: AsyncSession: The database session to use for the operation
    :return: The newly created photo object
    :doc-author: Trelent
    """
    url = upload_image(file.file)
    photo_data = PhotoCreate(url=url, description=description, tags=tags)
    return await create_photo(photo_data, user, db)


@router.put("/{photo_id}", response_model=PhotoResponse2)
async def update_photo_description(
    photo_id: int,
    photo_data: PhotoUpdate,
    user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    The update_photo_description function updates the description of an existing photo.

    :param photo_id: int: The ID of the photo to update
    :param photo_data: PhotoUpdate: The new data for the photo
    :param user: User: The current user updating the photo
    :param db: AsyncSession: The database session to use for the operation
    :return: The updated photo object
    :doc-author: Trelent
    """
    updated_photo = await update_photo(photo_id, photo_data, user, db)
    if not updated_photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    return updated_photo


@router.delete("/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delet_photo(
    photo_id: int,
    user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    The delete_photo function deletes an existing photo.

    :param photo_id: int: The ID of the photo to delete
    :param user: User: The current user deleting the photo
    :param db: AsyncSession: The database session to use for the operation
    :return: None
    :doc-author: Trelent
    """
    if user.role != Role.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    
    deleted_photo = await delete_photo(photo_id, user, db)
    if not deleted_photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    return None


@router.get("/{photo_id}", response_model=PhotoResponse2)
async def get_photo_details(
    photo_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    The get_photo_details function retrieves the details of a photo by its ID.

    :param photo_id: int: The ID of the photo to retrieve
    :param db: AsyncSession: The database session to use for the operation
    :return: The photo object with its details
    :doc-author: Trelent
    """
    photo = await get_photo(photo_id, db)
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    return photo


@router.get("/", response_model=list[PhotoResponse2])
async def list_all_photos(
    user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    The list_all_photos function retrieves all photos uploaded by the current user.

    :param user: User: The current user
    :param db: AsyncSession: The database session to use for the operation
    :return: A list of photo objects
    :doc-author: Trelent
    """
    photos = await get_photos(user, db)
    return photos


@router.post("/{photo_id}/tags", response_model=PhotoResponse, status_code=status.HTTP_200_OK)
async def add_tags(photo_id: int,
                   tags: List[str],
                   user: User = Depends(auth_service.get_current_user),
                   db: AsyncSession = Depends(get_db)):
    """
    The add_tags function adds tags to an existing photo.

    :param photo_id: int: The ID of the photo to add tags to
    :param tags: List[str]: The list of tags to add
    :param user: User: The current user adding tags to the photo
    :param db: AsyncSession: The database session to use for the operation
    :return: The updated photo object with the new tags
    :doc-author: Trelent
    """
    logger.debug("Received request to add tags to photo with ID: %d", photo_id)
    try:
        photo = await add_tags_to_photo(photo_id, tags, user, db)
    except ValueError as e:
        logger.error(f"Error adding tags to photo ID {photo_id}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not photo:
        logger.debug("Photo with ID: %d not found for user: %d", photo_id, user.id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    return photo


@router.delete("/{photo_id}/tags", response_model=PhotoResponse, status_code=status.HTTP_200_OK)
async def remove_tags(photo_id: int,
                      tags: List[str],
                      user: User = Depends(auth_service.get_current_user),
                      db: AsyncSession = Depends(get_db)):
    """
    The remove_tags function removes tags from an existing photo.

    :param photo_id: int: The ID of the photo to remove tags from
    :param tags: List[str]: The list of tags to remove
    :param user: User: The current user removing tags from the photo
    :param db: AsyncSession: The database session to use for the operation
    :return: The updated photo object with the tags removed
    :doc-author: Trelent
    """
    if user.role != Role.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    logger.debug("Received request to remove tags from photo with ID: %d", photo_id)
    try:
        photo = await remove_tags_from_photo(photo_id, tags, user, db)
    except ValueError as e:
        logger.error(f"Error removing tags from photo ID {photo_id}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not photo:
        logger.debug("Photo with ID: %d not found for user: %d", photo_id, user.id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    return photo


@router.post("/{photo_id}/transform", response_model=str, status_code=status.HTTP_200_OK)
async def transform_photo(
    photo_id: int,
    transformation_params: TransformationParams,
    user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    The transform_photo function applies transformations to an existing photo.

    :param photo_id: int: The ID of the photo to transform
    :param transformation_params: TransformationParams: The transformation parameters
    :param user: User: The current user transforming the photo
    :param db: AsyncSession: The database session to use for the operation
    :return:  URL of the transformed photo
    :doc-author: Trelent
    """
    photo = await get_photo(photo_id, db)
    if not photo or photo.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found or access denied")

    transformed_url = transform_image(photo.url, transformation_params.model_dump(exclude_unset=True))
    if transformed_url == photo.url:
        logger.error(f"Transformation did not change the URL: {transformed_url}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Transformation failed")

    return transformed_url


@router.post("/qr-code", response_model=str, status_code=status.HTTP_201_CREATED)
async def create_qr_code(
    photo_id: int,
    user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    The create_qr_code function generates a QR code for an existing photo.

    :param photo_id: int: The ID of the photo to generate a QR code for
    :param user: User: The current user generating the QR code
    :param db: AsyncSession: The database session to use for the operation
    :return: A streaming response containing the QR code image
    :doc-author: Trelent
    """
    photo = await get_photo(photo_id, db)
    if not photo or photo.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found or access denied")
    
    qr_code_image = generate_qr_code(photo.url)
    return StreamingResponse(qr_code_image, media_type="image/jpg")
