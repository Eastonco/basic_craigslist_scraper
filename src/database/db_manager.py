"""
Database operations module for managing Craigslist listings.
Handles database connections, queries, and CRUD operations.
"""

import logging
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from exceptions import DatabaseError


class DatabaseManager:
    """Manages database operations for Craigslist listings."""
    
    def __init__(self, engine, db_model_class, logger: Optional[logging.Logger] = None):
        """
        Initialize the database manager.
        
        Args:
            engine: SQLAlchemy engine instance
            db_model_class: Database model class for listings
            logger: Optional logger instance
        """
        self.engine = engine
        self.db_model = db_model_class
        self.logger = logger or logging.getLogger(__name__)
    
    def create_tables(self) -> None:
        """
        Create database tables if they don't exist.
        
        Raises:
            DatabaseError: If table creation fails
        """
        try:
            self.logger.info("Creating database tables")
            self.db_model.metadata.create_all(self.engine)
            self.logger.success("Database tables created successfully")
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to create database tables: {e}")
    
    def save_new_listings(self, listings: List) -> int:
        """
        Save new listings to the database, avoiding duplicates.
        
        Args:
            listings: List of listing objects to save
            
        Returns:
            Number of new listings saved
            
        Raises:
            DatabaseError: If database operation fails
        """
        if not listings:
            self.logger.info("No listings to save")
            return 0
        
        try:
            new_items_count = 0
            
            with Session(self.engine) as session:
                for listing in listings:
                    # Check if listing already exists
                    existing_query = select(self.db_model).where(
                        self.db_model.cl_id == listing.cl_id
                    )
                    existing_listing = session.scalars(existing_query).first()
                    
                    if not existing_listing:
                        self.logger.debug(f"Adding new listing: {listing.title}")
                        session.add(listing)
                        new_items_count += 1
                    else:
                        self.logger.debug(f"Skipping duplicate listing: {listing.title}")
                
                if new_items_count > 0:
                    self.logger.info(f"Committing {new_items_count} new items to database")
                    session.commit()
                    self.logger.success(f"Successfully saved {new_items_count} new listings")
                else:
                    self.logger.info("No new listings to commit")
            
            return new_items_count
            
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to save listings to database: {e}")
        except Exception as e:
            raise DatabaseError(f"Unexpected error saving listings: {e}")
    
    def get_new_listings_for_alerts(
        self, 
        timestamp: str, 
        filter_conditions: List
    ) -> List:
        """
        Get new listings from the current scrape that match alert criteria.
        
        Args:
            timestamp: Timestamp of the current scrape
            filter_conditions: List of SQLAlchemy filter conditions to exclude
            
        Returns:
            List of listings that should trigger alerts
            
        Raises:
            DatabaseError: If database query fails
        """
        try:
            with Session(self.engine) as session:
                # Query for listings from current scrape that don't match filters
                from sqlalchemy import or_
                
                query = select(self.db_model).where(
                    self.db_model.time_scraped == timestamp,
                    ~or_(*filter_conditions) if filter_conditions else True
                )
                
                listings = list(session.scalars(query))
                
                self.logger.info(f"Found {len(listings)} new listings for alerts")
                return listings
                
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to query new listings: {e}")
        except Exception as e:
            raise DatabaseError(f"Unexpected error querying listings: {e}")
    
    def get_listing_count(self) -> int:
        """
        Get the total count of listings in the database.
        
        Returns:
            Total number of listings
            
        Raises:
            DatabaseError: If database query fails
        """
        try:
            with Session(self.engine) as session:
                count = session.query(self.db_model).count()
                return count
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get listing count: {e}")
    
    def cleanup_old_listings(self, days_to_keep: int = 30) -> int:
        """
        Remove listings older than specified number of days.
        
        Args:
            days_to_keep: Number of days to keep listings
            
        Returns:
            Number of listings removed
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            from datetime import datetime, timedelta
            
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            cutoff_str = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')
            
            with Session(self.engine) as session:
                # Delete old listings
                deleted_count = session.query(self.db_model).filter(
                    self.db_model.time_scraped < cutoff_str
                ).delete()
                
                session.commit()
                
                self.logger.info(f"Cleaned up {deleted_count} old listings")
                return deleted_count
                
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to cleanup old listings: {e}")
        except Exception as e:
            raise DatabaseError(f"Unexpected error during cleanup: {e}")