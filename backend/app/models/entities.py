from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Enum, ForeignKey, JSON, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class OrderStatus(str, enum.Enum):
    draft = "draft"
    confirmed = "confirmed"
    fulfilled = "fulfilled"
    cancelled = "cancelled"


class UserRole(str, enum.Enum):
    worker = "worker"
    admin = "admin"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(unique=True, index=True)
    name: Mapped[str]
    unit: Mapped[str] = mapped_column(default="шт")

    stock_items: Mapped[list[StockItem]] = relationship(back_populates="product")
    order_lines: Mapped[list[OrderLine]] = relationship(back_populates="product")


class Warehouse(Base):
    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(unique=True, index=True)
    address: Mapped[str | None] = mapped_column(default=None)

    stock_items: Mapped[list[StockItem]] = relationship(back_populates="warehouse")
    orders: Mapped[list[Order]] = relationship(back_populates="warehouse")
    members: Mapped[list["WarehouseMember"]] = relationship(
        back_populates="warehouse",
        cascade="all, delete-orphan",
    )


class StockItem(Base):
    __tablename__ = "stock_items"
    __table_args__ = (UniqueConstraint("warehouse_id", "product_id", name="uq_stock_wh_product"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="CASCADE"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    quantity: Mapped[int] = mapped_column(default=0)

    warehouse: Mapped[Warehouse] = relationship(back_populates="stock_items")
    product: Mapped[Product] = relationship(back_populates="stock_items")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, values_callable=lambda x: [e.value for e in x], native_enum=False),
        default=OrderStatus.draft,
    )
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    warehouse: Mapped[Warehouse] = relationship(back_populates="orders")
    lines: Mapped[list[OrderLine]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )


class OrderLine(Base):
    __tablename__ = "order_lines"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"))
    quantity: Mapped[int]
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))

    order: Mapped[Order] = relationship(back_populates="lines")
    product: Mapped[Product] = relationship(back_populates="order_lines")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(unique=True, index=True)
    password_hash: Mapped[str]
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, values_callable=lambda x: [e.value for e in x], native_enum=False),
        default=UserRole.worker,
    )
    is_active: Mapped[bool] = mapped_column(default=True)

    warehouse_memberships: Mapped[list["WarehouseMember"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class WarehouseMember(Base):
    """Участник склада (назначение сотрудника на площадку)."""

    __tablename__ = "warehouse_members"
    __table_args__ = (UniqueConstraint("warehouse_id", "user_id", name="uq_wh_user"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    warehouse: Mapped[Warehouse] = relationship(back_populates="members")
    user: Mapped[User] = relationship(back_populates="warehouse_memberships")


class AuditLog(Base):
    """Журнал действий для администратора."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, index=True)
    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(index=True)
    entity_type: Mapped[str] = mapped_column(index=True)
    entity_id: Mapped[int | None] = mapped_column(default=None, index=True)
    warehouse_id: Mapped[int | None] = mapped_column(
        ForeignKey("warehouses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    detail: Mapped[dict | None] = mapped_column(JSON, default=None)

    actor: Mapped[User | None] = relationship()
    warehouse: Mapped[Warehouse | None] = relationship()
