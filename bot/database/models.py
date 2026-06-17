from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from bot.database.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True)  # telegram_id
    telegram_username_input = Column(String, nullable=True)
    twitter_username = Column(String, nullable=True)  # reused for website username
    wallet_address = Column(String, nullable=True)
    balance = Column(Float, default=0.0)
    referral_balance = Column(Float, default=0.0)
    referral_count = Column(Integer, default=0)
    total_balance = Column(Float, default=0.0)
    registration_date = Column(DateTime, default=datetime.utcnow)
    completed_tasks = Column(Boolean, default=False)
    banned = Column(Boolean, default=False)

    referrer_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    referrals = relationship("User", backref="referrer", remote_side=[id])

    def update_total_balance(self):
        self.total_balance = self.balance + self.referral_balance


class Withdrawal(Base):
    __tablename__ = "withdrawals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"))
    wallet = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, default="pending")  # pending, approved, rejected
    request_time = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="withdrawals")


class BotSettings(Base):
    __tablename__ = "bot_settings"

    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)
