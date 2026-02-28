from sqlalchemy import Column, Integer, String
from database import Base

class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    specialization = Column(String, index=True)
    hospital = Column(String)
    phone_number = Column(String)
    location = Column(String)
    consultation_fee = Column(String)
    wait_time = Column(String)
    city = Column(String, index=True)
    category = Column(String, index=True)
