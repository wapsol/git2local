#!/usr/bin/env python3
"""
Natural Language Query Parser for Odoo Helpdesk
Converts speech-to-text queries into Odoo domain filters
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional


class QueryParser:
    """Parse natural language queries into Odoo domain filters."""

    PRIORITY_MAP = {
        'low': '0',
        'medium': '1',
        'high': '2',
        'urgent': '3',
        'critical': '3'
    }

    def __init__(self, user_id: int, username: str):
        """
        Initialize parser with user context.

        Args:
            user_id: Odoo user ID
            username: Username for context
        """
        self.user_id = user_id
        self.username = username

    def parse(self, query_text: str) -> Tuple[List, Dict]:
        """
        Parse natural language query into Odoo domain and options.

        Args:
            query_text: Natural language query string

        Returns:
            Tuple of (domain_filter, options_dict)
            domain_filter: Odoo domain list
            options_dict: Additional query options (limit, order, fields)
        """
        query_lower = query_text.lower().strip()
        domain = []
        options = {
            'limit': 50,
            'order': 'write_date desc',
            'fields': ['id', 'name', 'user_id', 'partner_id', 'project_id',
                      'stage_id', 'priority', 'create_date', 'write_date',
                      'close_date', 'description']
        }

        # Pattern 1: "my tickets" or "my open/closed tickets"
        if re.search(r'\bmy\b', query_lower):
            domain.append(('user_id', '=', self.user_id))

            if re.search(r'\bopen\b', query_lower):
                domain.append(('close_date', '=', False))
            elif re.search(r'\bclosed\b', query_lower):
                domain.append(('close_date', '!=', False))

        # Pattern 2: Priority filters
        for priority_word, priority_val in self.PRIORITY_MAP.items():
            if re.search(rf'\b{priority_word}\b', query_lower):
                domain.append(('priority', '=', priority_val))
                break

        # Pattern 3: State filters (if not already filtered by "my open/closed")
        if not any('close_date' in str(d) for d in domain):
            if re.search(r'\bopen\b', query_lower):
                domain.append(('close_date', '=', False))
            elif re.search(r'\bclosed\b', query_lower):
                domain.append(('close_date', '!=', False))

        # Pattern 4: Time-based filters
        time_domain = self._parse_time_filter(query_lower)
        if time_domain:
            domain.extend(time_domain)

        # Pattern 5: Customer/partner name (extract quoted text or after "for/from")
        customer_match = re.search(r'(?:for|from|customer)\s+["\']?([a-zA-Z0-9\s]+)["\']?', query_lower)
        if customer_match:
            customer_name = customer_match.group(1).strip()
            # Use ilike for partial matching
            domain.append(('partner_id.name', 'ilike', customer_name))

        # Pattern 6: Project name
        project_match = re.search(r'(?:project)\s+["\']?([a-zA-Z0-9\s]+)["\']?', query_lower)
        if project_match:
            project_name = project_match.group(1).strip()
            domain.append(('project_id.name', 'ilike', project_name))

        # Pattern 7: Limit filters
        limit_match = re.search(r'\b(\d+)\s+(?:tickets?|results?)\b', query_lower)
        if limit_match:
            options['limit'] = min(int(limit_match.group(1)), 100)  # Max 100

        # Pattern 8: "all tickets" - no user filter
        if re.search(r'\ball\s+tickets?\b', query_lower) and not re.search(r'\bmy\b', query_lower):
            # Remove any user_id filter
            domain = [d for d in domain if 'user_id' not in str(d)]

        # If no domain specified, default to user's open tickets
        if not domain:
            domain = [
                ('user_id', '=', self.user_id),
                ('close_date', '=', False)
            ]

        return domain, options

    def _parse_time_filter(self, query_lower: str) -> List:
        """Parse time-based filters from query."""
        domain = []
        today = datetime.now().date()

        if re.search(r'\btoday\b', query_lower):
            domain.append(('write_date', '>=', today.strftime('%Y-%m-%d')))

        elif re.search(r'\byesterday\b', query_lower):
            yesterday = today - timedelta(days=1)
            domain.append(('write_date', '>=', yesterday.strftime('%Y-%m-%d')))
            domain.append(('write_date', '<', today.strftime('%Y-%m-%d')))

        elif re.search(r'\bthis\s+week\b', query_lower):
            # Start of week (Monday)
            start_of_week = today - timedelta(days=today.weekday())
            domain.append(('write_date', '>=', start_of_week.strftime('%Y-%m-%d')))

        elif re.search(r'\blast\s+week\b', query_lower):
            end_of_last_week = today - timedelta(days=today.weekday())
            start_of_last_week = end_of_last_week - timedelta(days=7)
            domain.append(('write_date', '>=', start_of_last_week.strftime('%Y-%m-%d')))
            domain.append(('write_date', '<', end_of_last_week.strftime('%Y-%m-%d')))

        elif re.search(r'\bthis\s+month\b', query_lower):
            start_of_month = today.replace(day=1)
            domain.append(('write_date', '>=', start_of_month.strftime('%Y-%m-%d')))

        elif re.search(r'\blast\s+(\d+)\s+days?\b', query_lower):
            match = re.search(r'\blast\s+(\d+)\s+days?\b', query_lower)
            days = int(match.group(1))
            start_date = today - timedelta(days=days)
            domain.append(('write_date', '>=', start_date.strftime('%Y-%m-%d')))

        return domain

    def get_query_summary(self, domain: List, options: Dict) -> str:
        """
        Generate human-readable summary of the query.

        Args:
            domain: Odoo domain filter
            options: Query options

        Returns:
            Human-readable query description
        """
        parts = []

        # Check for user filter
        user_filtered = any('user_id' in str(d) for d in domain)
        if user_filtered:
            parts.append("your")
        else:
            parts.append("all")

        # Check for state filter
        has_close_filter = any('close_date' in str(d) for d in domain)
        if has_close_filter:
            if "('close_date', '=', False)" in str(domain):
                parts.append("open")
            elif "('close_date', '!=', False)" in str(domain):
                parts.append("closed")

        # Check for priority
        for priority_word, priority_val in self.PRIORITY_MAP.items():
            if f"('priority', '=', '{priority_val}')" in str(domain):
                parts.append(priority_word + " priority")
                break

        parts.append("tickets")

        # Check for customer filter
        for d in domain:
            if 'partner_id' in str(d) and 'ilike' in str(d):
                parts.append(f"for customer matching '{d[2]}'")

        # Check for time filter
        for d in domain:
            if 'write_date' in str(d) and '>=' in str(d):
                date_str = d[2]
                parts.append(f"since {date_str}")
                break

        result = " ".join(parts)

        if options.get('limit', 50) < 100:
            result += f" (limit: {options['limit']})"

        return result.capitalize()


def test_parser():
    """Test the query parser with common queries."""
    parser = QueryParser(user_id=2, username="test_user")

    test_queries = [
        "show my tickets",
        "my open tickets",
        "my closed tickets",
        "show high priority tickets",
        "urgent tickets",
        "my tickets this week",
        "show all tickets today",
        "tickets for euroblaze",
        "my open tickets last 7 days",
        "show 10 tickets",
        "all open tickets"
    ]

    print("Testing Query Parser:")
    print("=" * 60)

    for query in test_queries:
        domain, options = parser.parse(query)
        summary = parser.get_query_summary(domain, options)
        print(f"\nQuery: '{query}'")
        print(f"Domain: {domain}")
        print(f"Summary: {summary}")
        print("-" * 60)


if __name__ == '__main__':
    test_parser()
