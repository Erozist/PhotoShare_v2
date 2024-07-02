import io
import logging
import qrcode
from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from src.entity.models import Photo, Tag, User
from src.schemas.photo import PhotoCreate, PhotoUpdate


logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


async def create_photo(photo_data: PhotoCreate, user: User, db: AsyncSession):
    """
    The create_photo function creates a new photo in the database.

    :param photo_data: PhotoCreate: The data for creating a new photo
    :param user: User: The user who is creating the photo
    :param db: AsyncSession: The database session to use for the operation
    :return: The newly created photo object
    """
    new_photo = Photo(
        url=photo_data.url,
        description=photo_data.description,
        user_id=user.id
    )
    if photo_data.tags:
        tags = await get_or_create_tags(photo_data.tags, db)
        new_photo.tags.extend(tags)

    db.add(new_photo)
    await db.commit()
    await db.refresh(new_photo)
    logger.debug("Photo created successfully with ID: %d for user: %d", new_photo.id, user.id)
    return new_photo


async def update_photo(photo_id: int, photo_data: PhotoUpdate, user: User, db: AsyncSession):
    """
    The update_photo function updates an existing photo's description in the database.

    :param photo_id: int: The ID of the photo to update
    :param photo_data: PhotoUpdate: The new data for the photo
    :param user: User: The user who owns the photo
    :param db: AsyncSession: The database session to use for the operation
    :return: The updated photo object
    """
    stmt = select(Photo).filter_by(id=photo_id, user_id=user.id).options(joinedload(Photo.tags))
    result = await db.execute(stmt)
    photo = result.unique().scalar_one_or_none()
    if photo:
        photo.description = photo_data.description
        await db.commit()
        await db.refresh(photo)
    return photo


async def delete_photo(photo_id: int, user: User, db: AsyncSession):
    """
    The delete_photo function deletes an existing photo from the database.

    :param photo_id: int: The ID of the photo to delete
    :param user: User: The user who owns the photo
    :param db: AsyncSession: The database session to use for the operation
    :return: The deleted photo object
    """
    stmt = select(Photo).filter_by(id=photo_id, user_id=user.id).options(joinedload(Photo.tags))
    result = await db.execute(stmt)
    photo = result.unique().scalar_one_or_none()
    if photo:
        await db.delete(photo)
        await db.commit()
    return photo


async def get_photo(photo_id: int, db: AsyncSession):
    """
    The get_photo function retrieves a photo by its ID from the database.

    :param photo_id: int: The ID of the photo to retrieve
    :param db: AsyncSession: The database session to use for the operation
    :return: The photo object or None if not found
    """
    stmt = select(Photo).filter_by(id=photo_id).options(joinedload(Photo.tags))
    result = await db.execute(stmt)
    photo = result.unique().scalar_one_or_none()
    return photo


async def get_photos(user: User, db: AsyncSession):
    """
    The get_photos function retrieves all photos for a given user from the database.

    :param user: User: The user whose photos are to be retrieved
    :param db: AsyncSession: The database session to use for the operation
    :return: A list of photo objects
    """
    stmt = select(Photo).filter_by(user_id=user.id).options(joinedload(Photo.tags))
    result = await db.execute(stmt)
    photos = result.unique().scalars().all()
    return photos


async def add_tags_to_photo(photo_id: int, tags: List[str], user: User, db: AsyncSession):
    """
    The add_tags_to_photo function adds tags to an existing photo in the database.

    :param photo_id: int: The ID of the photo to add tags to
    :param tags: List[str]: The list of tags to add
    :param user: User: The user who owns the photo
    :param db: AsyncSession: The database session to use for the operation
    :return: The updated photo object or None if the photo is not found
    """
    logger.debug("Received request to add tags to photo with ID: %d for user: %d", photo_id, user.id)
    stmt = select(Photo).filter_by(id=photo_id, user_id=user.id).options(joinedload(Photo.tags))
    result = await db.execute(stmt)
    photo = result.unique().scalar_one_or_none()
    if not photo:
        logger.error("Photo with ID: %d not found for user: %d", photo_id, user.id)
        return None

    try:
        unique_new_tags = await validate_tags(photo, tags)
    except ValueError as e:
        logger.error(f"Validation error for photo ID {photo_id}: {e}")
        raise e

    tags = await get_or_create_tags(unique_new_tags, db)
    photo.tags.extend(tags)
    await db.commit()
    await db.refresh(photo)
    logger.debug("Tags added successfully to photo ID: %d for user: %d", photo_id, user.id)
    return photo


async def get_or_create_tags(tag_names: List[str], db: AsyncSession):
    """
    The get_or_create_tags function retrieves or creates tags based on the given list of tag names.

    :param tag_names: List[str]: The list of tag names to retrieve or create
    :param db: AsyncSession: The database session to use for the operation
    :return: A list of tag objects
    """
    tags = []
    for tag_name in tag_names:
        logger.debug("Processing tag: %s", tag_name)
        tag = await db.execute(select(Tag).filter_by(name=tag_name))
        existing_tag = tag.scalar_one_or_none()
        if existing_tag:
            logger.debug("Existing tag found: %s", tag_name)
            tags.append(existing_tag)
        else:
            logger.debug("Creating new tag: %s", tag_name)
            new_tag = Tag(name=tag_name)
            db.add(new_tag)
            await db.flush()
            tags.append(new_tag)
            logger.debug("New tag created: %s", tag_name)
    return tags


async def validate_tags(photo: Photo, new_tags: List[str]):
    """
    The validate_tags function validates and filters new tags for a photo.

    :param photo: Photo: The photo object to validate tags for
    :param new_tags: List[str]: The list of new tags to validate
    :return: A list of unique new tags
    :raises ValueError: If the total number of tags exceeds the allowed limit or if all tags already exist
    """
    existing_tags = {tag.name for tag in photo.tags}
    unique_new_tags = [tag for tag in new_tags if tag not in existing_tags]
    if len(photo.tags) + len(unique_new_tags) > 5:
        logger.error("Cannot add more than 5 tags to photo with ID: %d", photo.id)
        raise ValueError("Cannot add more than 5 tags to a photo")

    if not unique_new_tags:
        logger.debug("All tags already exist for photo ID: %d", photo.id)
        raise ValueError("All tags already exist for this photo")

    return unique_new_tags


async def remove_tags_from_photo(photo_id: int, tags: List[str], user: User, db: AsyncSession):
    """
    The remove_tags_from_photo function removes tags from an existing photo in the database.

    :param photo_id: int: The ID of the photo to remove tags from
    :param tags: List[str]: The list of tags to remove
    :param user: User: The user who owns the photo
    :param db: AsyncSession: The database session to use for the operation
    :return: The updated photo object or None if the photo is not found
    :raises ValueError: If no matching tags are found on the photo
    """
    logger.debug("Received request to remove tags from photo with ID: %d for user: %d", photo_id, user.id)
    stmt = select(Photo).filter_by(id=photo_id, user_id=user.id).options(joinedload(Photo.tags))
    result = await db.execute(stmt)
    photo = result.unique().scalar_one_or_none()
    if not photo:
        logger.error("Photo with ID: %d not found for user: %d", photo_id, user.id)
        return None

    tags_to_remove = [tag for tag in photo.tags if tag.name in tags]
    if not tags_to_remove:
        logger.error("No matching tags found for photo ID: %d", photo_id)
        raise ValueError("No matching tags found for this photo")
    
    for tag in tags_to_remove:
        photo.tags.remove(tag)
    
    await db.commit()
    await db.refresh(photo)
    logger.debug("Tags removed successfully from photo ID: %d for user: %d", photo_id, user.id)
    return photo


def generate_qr_code(data: str):
    """
    The generate_qr_code function generates a QR code image from the provided data.

    :param data: str: The data to encode in the QR code
    :return: An io.BytesIO object containing the QR code image
    """
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')
    buffer = io.BytesIO()
    img.save(buffer)
    buffer.seek(0)
    return buffer
