from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.config.db_conf import Base




class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    nickname: Mapped[str] = mapped_column(String(50), default=None, nullable=True)
    avatar: Mapped[str] = mapped_column(String(255), default="https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg")
    gender: Mapped[str] = mapped_column(String(10), default=None, nullable=True)
    bio: Mapped[str] = mapped_column(String(200), default="这个人很懒，什么都没留下")
    phone: Mapped[str] = mapped_column(String(20), default=None, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class UserToken(Base):
    __tablename__ = "user_token"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False)
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expired_at: Mapped[datetime] = mapped_column(DateTime, default=None, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
