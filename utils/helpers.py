# utils/helpers.py
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def generate_uuid():
    """Generate a UUID string"""
    return str(uuid.uuid4())

def format_datetime(dt, format='%Y-%m-%d %H:%M:%S'):
    """Format a datetime object as string"""
    if not dt:
        return None
    return dt.strftime(format)

def parse_datetime(dt_str, format='%Y-%m-%d %H:%M:%S'):
    """Parse a datetime string into a datetime object"""
    if not dt_str:
        return None
    try:
        return datetime.strptime(dt_str, format)
    except ValueError:
        logger.error(f"Error parsing datetime string: {dt_str}")
        return None

def format_currency(value, currency='$', decimals=2):
    """Format a number as currency"""
    if value is None:
        return f"{currency}0.00"
    
    # Handle different precision based on magnitude
    if abs(value) >= 1000:
        return f"{currency}{value:,.{decimals}f}"
    elif abs(value) >= 1:
        return f"{currency}{value:,.{decimals+2}f}"
    else:
        return f"{currency}{value:,.{decimals+4}f}"
