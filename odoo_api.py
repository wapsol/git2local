#!/usr/bin/env python3
"""
Odoo API Connector
Provides functions to connect to Odoo ERP and fetch helpdesk ticket data.
"""

import xmlrpc.client
import sys
from typing import Dict, List, Optional
from datetime import datetime


class OdooAPI:
    """Odoo API connector using XML-RPC."""

    def __init__(self, url: str, db: str, username: str, password: str):
        """
        Initialize Odoo API connection.

        Args:
            url: Odoo server URL (e.g., https://erp.wapsol.de)
            db: Database name
            username: User email/login
            password: User password
        """
        self.url = url.rstrip('/')
        self.db = db
        self.username = username
        self.password = password
        self.uid = None

        # XML-RPC endpoints
        self.common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
        self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')

    def authenticate(self) -> bool:
        """
        Authenticate with Odoo server.

        Returns:
            True if authentication successful, False otherwise
        """
        try:
            self.uid = self.common.authenticate(self.db, self.username, self.password, {})
            if self.uid:
                print(f"Successfully authenticated to Odoo as {self.username}", file=sys.stderr)
                return True
            else:
                print(f"Failed to authenticate to Odoo. Check credentials.", file=sys.stderr)
                return False
        except Exception as e:
            print(f"Error authenticating to Odoo: {e}", file=sys.stderr)
            return False

    def execute_kw(self, model: str, method: str, args: list, kwargs: dict = None):
        """
        Execute a model method via XML-RPC.

        Args:
            model: Odoo model name (e.g., 'helpdesk.ticket')
            method: Method to call (e.g., 'search_read')
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Method result
        """
        if kwargs is None:
            kwargs = {}

        return self.models.execute_kw(
            self.db, self.uid, self.password,
            model, method, args, kwargs
        )

    def fetch_helpdesk_tickets(self, since_date: str, end_date: str = None, user_ids: List[int] = None) -> List[Dict]:
        """
        Fetch helpdesk tickets updated within date range.

        Args:
            since_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format (default: today)
            user_ids: List of user IDs to filter by (optional)

        Returns:
            List of ticket dictionaries
        """
        if not self.uid:
            if not self.authenticate():
                return []

        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        # Build domain (filter criteria)
        domain = [
            ('write_date', '>=', since_date),
            ('write_date', '<=', f'{end_date} 23:59:59')
        ]

        if user_ids:
            domain.append(('user_id', 'in', user_ids))

        # Fields to fetch
        fields = [
            'id', 'name', 'description', 'stage_id', 'priority',
            'user_id', 'partner_id', 'project_id', 'team_id',
            'create_date', 'write_date', 'close_date', 'tag_ids'
        ]

        try:
            print(f"Fetching Odoo helpdesk tickets from {since_date} to {end_date}...", file=sys.stderr)
            tickets = self.execute_kw(
                'helpdesk.ticket',
                'search_read',
                [domain],
                {'fields': fields, 'limit': 1000, 'order': 'write_date desc'}
            )
            print(f"Found {len(tickets)} helpdesk tickets", file=sys.stderr)
            return tickets
        except Exception as e:
            print(f"Error fetching helpdesk tickets: {e}", file=sys.stderr)
            return []

    def fetch_users(self, user_ids: List[int] = None) -> Dict[int, str]:
        """
        Fetch user information.

        Args:
            user_ids: List of user IDs to fetch (optional, fetches all if None)

        Returns:
            Dictionary mapping user ID to user name
        """
        if not self.uid:
            if not self.authenticate():
                return {}

        domain = []
        if user_ids:
            domain = [('id', 'in', user_ids)]

        try:
            users = self.execute_kw(
                'res.users',
                'search_read',
                [domain],
                {'fields': ['id', 'name', 'login']}
            )
            return {user['id']: user['name'] for user in users}
        except Exception as e:
            print(f"Error fetching users: {e}", file=sys.stderr)
            return {}

    def fetch_partners(self, partner_ids: List[int] = None) -> Dict[int, str]:
        """
        Fetch partner (customer) information.

        Args:
            partner_ids: List of partner IDs to fetch (optional)

        Returns:
            Dictionary mapping partner ID to partner name
        """
        if not self.uid:
            if not self.authenticate():
                return {}

        domain = []
        if partner_ids:
            domain = [('id', 'in', partner_ids)]

        try:
            partners = self.execute_kw(
                'res.partner',
                'search_read',
                [domain],
                {'fields': ['id', 'name', 'email']}
            )
            return {partner['id']: partner['name'] for partner in partners}
        except Exception as e:
            print(f"Error fetching partners: {e}", file=sys.stderr)
            return {}

    def get_helpdesk_stages(self) -> Dict[int, Dict]:
        """
        Fetch helpdesk stages.

        Returns:
            Dictionary mapping stage ID to stage info (name, is_close)
        """
        if not self.uid:
            if not self.authenticate():
                return {}

        try:
            stages = self.execute_kw(
                'helpdesk.stage',
                'search_read',
                [[]],
                {'fields': ['id', 'name', 'fold', 'sequence']}
            )
            return {
                stage['id']: {
                    'name': stage['name'],
                    'is_closed': stage.get('fold', False),
                    'sequence': stage.get('sequence', 0)
                }
                for stage in stages
            }
        except Exception as e:
            print(f"Error fetching helpdesk stages: {e}", file=sys.stderr)
            return {}

    def query_tickets(self, domain: List, limit: int = 50, order: str = 'write_date desc',
                     fields: List[str] = None) -> List[Dict]:
        """
        Query helpdesk tickets with custom domain filter.

        Args:
            domain: Odoo domain filter (list of tuples)
            limit: Maximum number of results (default: 50, max: 100)
            order: Sort order (default: 'write_date desc')
            fields: Fields to fetch (default: common ticket fields)

        Returns:
            List of ticket dictionaries
        """
        if not self.uid:
            if not self.authenticate():
                return []

        # Default fields
        if fields is None:
            fields = [
                'id', 'name', 'description', 'stage_id', 'priority',
                'user_id', 'partner_id', 'project_id', 'team_id',
                'create_date', 'write_date', 'close_date', 'tag_ids'
            ]

        # Limit to max 100
        limit = min(limit, 100)

        try:
            tickets = self.execute_kw(
                'helpdesk.ticket',
                'search_read',
                [domain],
                {'fields': fields, 'limit': limit, 'order': order}
            )
            return tickets
        except Exception as e:
            print(f"Error querying helpdesk tickets: {e}", file=sys.stderr)
            return []

    def get_current_user_id(self) -> Optional[int]:
        """
        Get the current authenticated user's Odoo ID.

        Returns:
            User ID or None if not authenticated
        """
        return self.uid
