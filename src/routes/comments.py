from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.database.db import get_db
from src.entity.models import Comment, Photo, User
from src.schemas.comment import CommentCreate, CommentUpdate, CommentResponse
from src.services.auth import auth_service


router = APIRouter(prefix="/comments", tags=["comments"])


@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    photo_id: int,
    body: CommentCreate,
    user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    The create_comment function creates a new comment for a photo.

    :param photo_id: int: The ID of the photo to comment on
    :param body: CommentCreate: The content of the comment
    :param user: User: The current user creating the comment
    :param db: AsyncSession: The database session to use for the operation
    :return: The newly created comment object
    :doc-author: Trelent
    """
    try:
        photo = await db.get(Photo, photo_id)
        if not photo:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
        comment = Comment(content=body.content, user_id=user.id, photo_id=photo.id)
        db.add(comment)
        await db.commit()
        await db.refresh(comment)
        return comment
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: int,
    body: CommentUpdate,
    user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    The update_comment function updates an existing comment.

    :param comment_id: int: The ID of the comment to update
    :param body: CommentUpdate: The new content of the comment
    :param user: User: The current user updating the comment
    :param db: AsyncSession: The database session to use for the operation
    :return: The updated comment object
    :doc-author: Trelent
    """
    try:
        comment = await db.get(Comment, comment_id)
        if not comment or comment.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found or forbidden")
        comment.content = body.content
        await db.commit()
        await db.refresh(comment)
        return comment
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    The delete_comment function deletes an existing comment.

    :param comment_id: int: The ID of the comment to delete
    :param user: User: The current user deleting the comment
    :param db: AsyncSession: The database session to use for the operation
    :return: None
    :doc-author: Trelent
    """
    try:
        comment = await db.get(Comment, comment_id)
        if not comment or comment.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found or forbidden")
        await db.delete(comment)
        await db.commit()
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/photo/{photo_id}", response_model=list[CommentResponse])
async def get_comments_by_photo(
    photo_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    The get_comments_by_photo function retrieves all comments for a given photo.

    :param photo_id: int: The ID of the photo to retrieve comments for
    :param db: AsyncSession: The database session to use for the operation
    :return: A list of comment objects
    :doc-author: Trelent
    """
    comments = await db.execute(select(Comment).filter_by(photo_id=photo_id))
    return comments.scalars().all()
