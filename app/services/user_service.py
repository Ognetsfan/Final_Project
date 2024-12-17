from builtins import Exception, bool, classmethod, int, str
from datetime import datetime, timezone
from typing import Optional, Dict, List
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError
from app.models.user_model import User, UserRole
from app.schemas.user_schemas import UserCreate, UserUpdate
from app.utils.security import hash_password, verify_password
from app.utils.nickname_gen import generate_nickname
from app.utils.security import generate_verification_token
import logging

logger = logging.getLogger(__name__)


class UserService:
    @classmethod
    async def _execute_query(cls, session: AsyncSession, query):
        try:
            result = await session.execute(query)
            await session.commit()
            return result
        except SQLAlchemyError as e:
            logger.error(f"Database error: {e}")
            await session.rollback()
            return None

    @classmethod
    async def _fetch_user(cls, session: AsyncSession, **filters) -> Optional[User]:
        query = select(User).filter_by(**filters)
        result = await cls._execute_query(session, query)
        return result.scalars().first() if result else None

    @classmethod
    async def get_by_id(cls, session: AsyncSession, user_id: int) -> Optional[User]:
        return await cls._fetch_user(session, id=user_id)

    @classmethod
    async def create_user(cls, session: AsyncSession, user_data: UserCreate) -> Optional[User]:
        try:
            hashed_password = hash_password(user_data.password)
            new_user = User(
                email=user_data.email,
                hashed_password=hashed_password,
                github_link=user_data.github_link,
                linkedin_link=user_data.linkedin_link,
                profile_photo_url=user_data.profile_photo_url,
                role=UserRole.USER,  # Default role
                verification_token=generate_verification_token(),
                nickname=generate_nickname()
            )

            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            return new_user
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None

    @classmethod
    async def update_user_profile(cls, session: AsyncSession, user_id: int, user_update: UserUpdate) -> Optional[User]:
        try:
            db_user = await cls.get_by_id(session, user_id)
            if db_user:
                db_user.github_link = user_update.github_link or db_user.github_link
                db_user.linkedin_link = user_update.linkedin_link or db_user.linkedin_link
                db_user.profile_photo_url = user_update.profile_photo_url or db_user.profile_photo_url
                await session.commit()
                await session.refresh(db_user)
                return db_user
            else:
                logger.error(f"User with ID {user_id} not found.")
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
        return None

    @classmethod
    async def upgrade_user_to_pro(cls, session: AsyncSession, user_id: int) -> Optional[User]:
        try:
            db_user = await cls.get_by_id(session, user_id)
            if db_user:
                db_user.is_pro = True
                await session.commit()
                await session.refresh(db_user)
                logger.info(f"User {user_id} upgraded to PRO status.")
                return db_user
            else:
                logger.error(f"User with ID {user_id} not found.")
        except Exception as e:
            logger.error(f"Error upgrading user to PRO: {e}")
        return None
