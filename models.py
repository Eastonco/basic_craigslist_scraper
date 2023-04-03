from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import Optional

# SQLAlchemy imports
from sqlalchemy.orm import MappedAsDataclass
from sqlalchemy import Column, Float, String, DateTime, Integer
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from sqlalchemy import select


@dataclass_json
@dataclass
class Craigslist_Result_Card:
    link: str
    title: str
    cl_id: str
    screenshot_path: str
    time_posted: str
    location: str
    time_scraped: str


@dataclass
class Config():
    urls: list[str]
    send_email_alerts: bool
    src_email: str
    dst_emails: str
    email_key: str
    send_sms_alerts: bool
    src_phone_number: str
    dst_phone_numbers: str
    twilio_account_sid: str
    twilio_auth_token: str
    db_user: str
    db_password: str



# format is postgresql://username:password@host:port/database
def get_engine(user: str = 'postgres', password: str = 'password', host: str = 'localhost', port: str = '5432', database: str = 'craigslist', echo: bool = False):
    SQLALCHEMY_DATABASE_URL = f'postgresql://{user}:{password}@{host}:{port}/{database}'
    engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=echo)
    return engine

class Base(MappedAsDataclass, DeclarativeBase):
    pass

def get_db(table_name: str):
    class db_listing_entry(Base):
        __tablename__ = f'cl_table_{table_name}'
        id: Mapped[int] = mapped_column(Integer,init=False,  primary_key=True)
        link: Mapped[str] = mapped_column(String)
        title: Mapped[str] = mapped_column(String)
        cl_id: Mapped[str] = mapped_column(String)
        screenshot_path: Mapped[Optional[str]] = mapped_column(String)
        time_posted: Mapped[str] = mapped_column(String)
        location: Mapped[str] = mapped_column(String)
        time_scraped: Mapped[str] = mapped_column(String)

        def __repr__(self):
            return f'link: {self.link}\ntitle: {self.title}\nid: {self.cl_id}\nscreenshot_path: {self.screenshot_path}\ntime_posted: {self.time_posted}\nlocation: {self.location}\ntime_scraped: {self.time_scraped}'

    return db_listing_entry
