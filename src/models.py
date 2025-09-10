import os
from typing import List, Optional

from pydantic import BaseModel, EmailStr, HttpUrl, validator
from sqlalchemy import String, Integer, create_engine
from sqlalchemy.orm import Session, Mapped, mapped_column, DeclarativeBase, MappedAsDataclass

from constants import (
    DEFAULT_DB_HOST, DEFAULT_DB_PORT, DEFAULT_DB_USER, 
    DEFAULT_DB_PASSWORD, DEFAULT_DB_NAME
)
from exceptions import ConfigurationError


class Config(BaseModel):
    """Configuration model with validation using Pydantic."""
    
    # Scraping configuration
    urls: List[HttpUrl]
    filters: List[str] = []
    
    # Alert configuration
    send_email_alerts: bool = False
    send_sms_alerts: bool = False
    send_discord_alerts: bool = False
    combine_texts: bool = False
    
    # Email settings
    src_email: Optional[EmailStr] = None
    dst_emails: List[EmailStr] = []
    email_key: Optional[str] = None
    
    # SMS settings
    src_phone_number: Optional[str] = None
    dst_phone_numbers: List[str] = []
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    
    # Discord settings
    discord_webhook_url: Optional[HttpUrl] = None
    
    # Database settings
    db_user: str = DEFAULT_DB_USER
    db_password: str = DEFAULT_DB_PASSWORD
    db_host: str = DEFAULT_DB_HOST
    db_port: str = DEFAULT_DB_PORT
    db_name: str = DEFAULT_DB_NAME
    
    @validator('urls')
    def validate_urls(cls, v):
        """Ensure at least one URL is provided."""
        if not v:
            raise ValueError('At least one URL must be provided')
        return v
    
    @validator('src_email', 'dst_emails', 'email_key')
    def validate_email_config(cls, v, values, field):
        """Validate email configuration when email alerts are enabled."""
        if values.get('send_email_alerts', False):
            if field.name == 'src_email' and not v:
                raise ValueError('src_email is required when send_email_alerts is True')
            if field.name == 'dst_emails' and not v:
                raise ValueError('dst_emails is required when send_email_alerts is True')
            if field.name == 'email_key' and not v:
                raise ValueError('email_key is required when send_email_alerts is True')
        return v
    
    @validator('twilio_account_sid', 'twilio_auth_token', 'src_phone_number', 'dst_phone_numbers')
    def validate_sms_config(cls, v, values, field):
        """Validate SMS configuration when SMS alerts are enabled."""
        if values.get('send_sms_alerts', False):
            if not v:
                raise ValueError(f'{field.name} is required when send_sms_alerts is True')
        return v
    
    @validator('discord_webhook_url')
    def validate_discord_config(cls, v, values):
        """Validate Discord configuration when Discord alerts are enabled."""
        if values.get('send_discord_alerts', False) and not v:
            raise ValueError('discord_webhook_url is required when send_discord_alerts is True')
        return v


def get_engine(
    user: str = DEFAULT_DB_USER,
    password: str = DEFAULT_DB_PASSWORD,
    host: str = DEFAULT_DB_HOST,
    port: str = DEFAULT_DB_PORT,
    database: str = DEFAULT_DB_NAME,
    echo: bool = False,
):
    """
    Create and return a SQLAlchemy engine with environment variable overrides.
    
    Args:
        user: Database username
        password: Database password
        host: Database host
        port: Database port
        database: Database name
        echo: Whether to echo SQL statements
    
    Returns:
        SQLAlchemy engine instance
        
    Raises:
        DatabaseError: If engine creation fails
    """
    try:
        # Override with environment variables if available
        user = os.getenv('DB_USER', user)
        password = os.getenv('DB_PASSWORD', password)
        host = os.getenv('DB_HOST', host)
        port = os.getenv('DB_PORT', port)
        database = os.getenv('DB_NAME', database)

        SQLALCHEMY_DATABASE_URL = f'postgresql://{user}:{password}@{host}:{port}/{database}'
        engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=echo)
        return engine
    except Exception as e:
        raise ConfigurationError(f"Failed to create database engine: {e}")


class Base(MappedAsDataclass, DeclarativeBase):
    pass


def get_db(table_name: str):
    """
    Create a database model class for Craigslist listings.
    
    Args:
        table_name: Name for the database table
        
    Returns:
        SQLAlchemy model class for listings
    """
    class CraigslistListing(Base):
        __tablename__ = f'cl_table_{table_name}'
        
        id: Mapped[int] = mapped_column(Integer, init=False, primary_key=True)
        link: Mapped[str] = mapped_column(String, nullable=False)
        title: Mapped[str] = mapped_column(String, nullable=False)
        cl_id: Mapped[str] = mapped_column(String, nullable=False, unique=True)
        time_posted: Mapped[str] = mapped_column(String, nullable=False)
        location: Mapped[str] = mapped_column(String, nullable=False)
        time_scraped: Mapped[str] = mapped_column(String, nullable=False)

        def __repr__(self) -> str:
            return (
                f'CraigslistListing('
                f'id={self.cl_id}, '
                f'title="{self.title}", '
                f'location="{self.location}", '
                f'posted={self.time_posted}, '
                f'scraped={self.time_scraped}'
                f')'
            )
        
        def __str__(self) -> str:
            return (
                f'Title: {self.title}\n'
                f'Link: {self.link}\n'
                f'ID: {self.cl_id}\n'
                f'Posted: {self.time_posted}\n'
                f'Location: {self.location}\n'
                f'Scraped: {self.time_scraped}'
            )

    return CraigslistListing
