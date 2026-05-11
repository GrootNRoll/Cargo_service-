from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.entities import User, UserRole, WarehouseMember


def _admin_count(db: Session) -> int:
    return int(db.scalar(select(func.count()).select_from(User).where(User.role == UserRole.admin)) or 0)


def _active_admin_count(db: Session) -> int:
    return int(
        db.scalar(
            select(func.count()).select_from(User).where(
                User.role == UserRole.admin,
                User.is_active.is_(True),
            )
        )
        or 0,
    )


def list_users_admin(db: Session, *, active_only: bool = False) -> list[User]:
    stmt = select(User).order_by(User.username)
    if active_only:
        stmt = stmt.where(User.is_active.is_(True))
    return list(db.scalars(stmt).all())


def create_user(db: Session, *, username: str, password: str, role: UserRole) -> User:
    if get_by_username(db, username) is not None:
        raise ValueError("username_taken")
    user = User(
        username=username,
        password_hash=get_password_hash(password),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def list_active_users(db: Session) -> list[User]:
    return list_users_admin(db, active_only=True)


def deactivate_user(db: Session, user_id: int) -> None:
    user = db.get(User, user_id)
    if user is None:
        raise ValueError("not_found")
    if not user.is_active:
        raise ValueError("already_inactive")
    if user.role == UserRole.admin and _active_admin_count(db) <= 1:
        raise ValueError("sole_admin")
    user.is_active = False
    db.execute(delete(WarehouseMember).where(WarehouseMember.user_id == user_id))
    db.commit()


def activate_user(db: Session, user_id: int) -> None:
    user = db.get(User, user_id)
    if user is None:
        raise ValueError("not_found")
    if user.is_active:
        raise ValueError("already_active")
    user.is_active = True
    db.commit()


def delete_user_permanent(db: Session, user_id: int) -> None:
    user = db.get(User, user_id)
    if user is None:
        raise ValueError("not_found")
    if user.role == UserRole.admin and _admin_count(db) <= 1:
        raise ValueError("sole_admin")
    db.delete(user)
    db.commit()


def get_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


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
