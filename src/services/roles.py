from fastapi import Request, Depends, HTTPException, status

from src.entity.models import Role, User
from src.services.auth import auth_service


class RoleAccess:
    def __init__(self, allowed_roles: list[Role]):
        """
        The RoleAccess class is used to restrict access to endpoints based on user roles.
        
        :param allowed_roles: list[Role]: A list of roles that are allowed to access the endpoint
        :doc-author: Trelent
        """
        self.allowed_roles = allowed_roles


    async def __call__(self, request: Request, user: User = Depends(auth_service.get_current_user)):
        if user.role not in self.allowed_roles:
            """
        The __call__ method is used to check if the current user's role is in the list of allowed roles.
        If the user's role is not allowed, an HTTPException with status code 403 (FORBIDDEN) is raised.
        
        :param request: Request: The incoming HTTP request
        :param user: User: The current authenticated user
        :return: None
        :raises HTTPException: If the user's role is not allowed to access the endpoint
        :doc-author: Trelent
        """
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="FORBIDDEN"
            )
