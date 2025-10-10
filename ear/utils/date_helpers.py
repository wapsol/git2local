"""Date and time period helper utilities."""

from datetime import datetime, timedelta
from typing import Tuple


def calculate_date_range(period: str) -> Tuple[str, str, str]:
    """
    Calculate date range based on period code.

    Args:
        period: Period code (7d, week, lastweek, month, lastmonth, quarter, year)

    Returns:
        Tuple of (start_date, end_date, period_label)
    """
    now = datetime.now()
    today = now.date()

    if period == '7d':
        start_date = today - timedelta(days=7)
        return (start_date.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'), 'Past 7 Days')

    elif period == 'week':
        # This week (Monday to today)
        monday = today - timedelta(days=today.weekday())
        return (monday.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'), 'This Week')

    elif period == 'lastweek':
        # Last week (previous Monday to Sunday)
        days_since_monday = today.weekday()
        this_monday = today - timedelta(days=days_since_monday)
        last_sunday = this_monday - timedelta(days=1)
        last_monday = last_sunday - timedelta(days=6)
        return (last_monday.strftime('%Y-%m-%d'), last_sunday.strftime('%Y-%m-%d'), 'Last Week')

    elif period == '14d':
        start_date = today - timedelta(days=14)
        return (start_date.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'), 'Past 14 Days')

    elif period == 'month':
        # This month (1st to today)
        start_date = today.replace(day=1)
        return (start_date.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'), 'This Month')

    elif period == 'lastmonth':
        # Last month (entire previous month)
        first_of_this_month = today.replace(day=1)
        last_month_end = first_of_this_month - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        return (last_month_start.strftime('%Y-%m-%d'), last_month_end.strftime('%Y-%m-%d'), 'Last Month')

    elif period == 'quarter':
        # This quarter (Q1-Q4 start to today)
        quarter = (now.month - 1) // 3
        quarter_start_month = quarter * 3 + 1
        start_date = today.replace(month=quarter_start_month, day=1)
        quarter_num = quarter + 1
        return (start_date.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'), f'This Quarter (Q{quarter_num})')

    elif period == 'year':
        # This year (Jan 1 to today)
        start_date = today.replace(month=1, day=1)
        return (start_date.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'), 'This Year')

    else:
        # Default to last week
        days_since_monday = today.weekday()
        this_monday = today - timedelta(days=days_since_monday)
        last_sunday = this_monday - timedelta(days=1)
        last_monday = last_sunday - timedelta(days=6)
        return (last_monday.strftime('%Y-%m-%d'), last_sunday.strftime('%Y-%m-%d'), 'Last Week')


def format_date_short(date_str: str) -> str:
    """
    Format ISO date string to DD.MM.YY format.

    Args:
        date_str: ISO date string (YYYY-MM-DD)

    Returns:
        Formatted date (DD.MM.YY)
    """
    try:
        date_obj = datetime.strptime(date_str[:10], '%Y-%m-%d')
        return date_obj.strftime('%d.%m.%y')
    except (ValueError, IndexError):
        return 'N/A'


def parse_refresh_rate(rate_str: str) -> int:
    """
    Parse refresh rate string to milliseconds.

    Args:
        rate_str: Refresh rate string (e.g., '10s', '5m')

    Returns:
        Milliseconds, or None if invalid
    """
    import re

    if not rate_str:
        return None

    match = re.match(r'^(\d+)([sm])$', rate_str.lower())
    if not match:
        return None

    value = int(match.group(1))
    unit = match.group(2)

    if unit == 's':
        return value * 1000  # seconds to milliseconds
    elif unit == 'm':
        return value * 60 * 1000  # minutes to milliseconds

    return None
