# app/repositories/user_repository.py

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.logging import logger
from app.domain.user import User
from app.schemas.user_schema import UserUpdate


class UserRepository:
    @staticmethod
    def get_by_login(db: Session, login: str) -> User | None:
        return db.query(User).filter(User.login == login).first()

    @staticmethod
    def get_by_email(db: Session, email: str) -> User | None:
        logger.debug("Searching for user with email=%s", email)
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_by_login_or_email(db: Session, identifier: str) -> User | None:
        logger.debug("Searching for user with identifier=%s", identifier)
        return (
            db.query(User)
            .filter(or_(User.login == identifier, User.email == identifier))
            .first()
        )

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> User | None:
        return db.query(User).filter(User.cod_usuario == user_id).first()

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
        return db.query(User).offset(skip).limit(limit).all()

    @staticmethod
    def create(db: Session, user: User) -> User:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update(db: Session, user: User, update_data: UserUpdate) -> User:
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)

        db.commit()
        db.refresh(user)
        return user
