from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.entities import User, UserRole


def get_by_username(db: Session, username: str) -> User | None:
    return db.scalars(select(User).where(User.username == username)).first()


def ensure_default_users(db: Session) -> None:
    if db.scalar(select(func.count()).select_from(User)):
        return
    db.add_all(
        [
            User(
                username="admin",
                password_hash=get_password_hash("admin123"),
                role=UserRole.admin,
            ),
            User(
                username="worker",
                password_hash=get_password_hash("worker123"),
                role=UserRole.worker,
            ),
        ]
    )
    db.commit()
