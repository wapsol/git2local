"""Unified Odoo service for all Odoo operations."""

import sys
from typing import List, Dict, Optional, Set
from collections import defaultdict

from ..models.config import OdooConfig
from ..models.ticket import EnrichedTicket, UserActivity
from ..utils.odoo_api import OdooAPI
from ..utils.text_processing import extract_name_from_odoo_tuple


class OdooService:
    """Unified Odoo service consolidating all Odoo operations."""

    def __init__(self, config: OdooConfig):
        """Initialize Odoo service.

        Args:
            config: Odoo configuration
        """
        self.config = config
        self._api: Optional[OdooAPI] = None
        self._users_cache: Optional[Dict] = None
        self._partners_cache: Optional[Dict] = None
        self._stages_cache: Optional[Dict] = None

    @property
    def api(self) -> OdooAPI:
        """Lazy connection with caching."""
        if self._api is None:
            if not self.config.password:
                raise ConnectionError("Odoo password not configured")

            self._api = OdooAPI(
                url=self.config.url,
                db=self.config.db,
                username=self.config.user,
                password=self.config.password
            )

            if not self._api.authenticate():
                raise ConnectionError("Odoo authentication failed")

        return self._api

    def fetch_tickets(
        self,
        since_date: str,
        end_date: str,
        domain: List = None
    ) -> List[Dict]:
        """Fetch tickets with optional domain filters.

        Args:
            since_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            domain: Optional Odoo domain filters

        Returns:
            List of raw ticket dictionaries
        """
        return self.api.fetch_helpdesk_tickets(since_date, end_date, domain)

    def query_tickets(
        self,
        domain: List,
        limit: int = 50,
        order: str = 'write_date desc',
        fields: List[str] = None
    ) -> List[Dict]:
        """Query tickets with domain filters.

        Args:
            domain: Odoo domain filter
            limit: Maximum number of results
            order: Sort order
            fields: Fields to return

        Returns:
            List of ticket dictionaries
        """
        return self.api.query_tickets(domain, limit, order, fields)

    def enrich_ticket(self, ticket: Dict) -> EnrichedTicket:
        """Enrich a single ticket with metadata.

        Args:
            ticket: Raw ticket dictionary

        Returns:
            EnrichedTicket with readable fields
        """
        # Lazy-load caches
        if self._users_cache is None:
            self._users_cache = self.api.fetch_users()
        if self._partners_cache is None:
            self._partners_cache = self.api.fetch_partners()
        if self._stages_cache is None:
            self._stages_cache = self.api.get_helpdesk_stages()

        # Extract user info
        user_name = extract_name_from_odoo_tuple(ticket.get('user_id')) or "Unassigned"

        # Extract customer info
        customer_name = extract_name_from_odoo_tuple(ticket.get('partner_id')) or "No Customer"

        # Extract project info
        project_name = extract_name_from_odoo_tuple(ticket.get('project_id')) or "No Project"

        # Extract stage info
        stage_id_tuple = ticket.get('stage_id')
        if isinstance(stage_id_tuple, (list, tuple)) and len(stage_id_tuple) >= 2:
            sid, stage_name = stage_id_tuple[0], stage_id_tuple[1]
        else:
            sid = stage_id_tuple
            stage_name = 'Unknown'

        stage_info = self._stages_cache.get(sid, {'name': stage_name, 'is_closed': False})
        is_closed = stage_info.get('is_closed', False) or bool(ticket.get('close_date'))

        return EnrichedTicket(
            id=ticket.get('id', 0),
            name=ticket.get('name', 'Untitled Ticket'),
            description=ticket.get('description', ''),
            priority=str(ticket.get('priority', '0')),
            create_date=ticket.get('create_date'),
            write_date=ticket.get('write_date'),
            close_date=ticket.get('close_date'),
            is_closed=is_closed,
            user=user_name,
            user_name=user_name,
            customer=customer_name,
            customer_name=customer_name,
            project=project_name,
            project_name=project_name,
            stage=stage_info.get('name', stage_name),
            stage_name=stage_info.get('name', stage_name)
        )

    def aggregate_by_user(
        self,
        tickets: List[Dict],
        filter_users: Optional[Set[str]] = None
    ) -> Dict[str, UserActivity]:
        """Aggregate tickets by user.

        Args:
            tickets: List of raw ticket dictionaries
            filter_users: Optional set of usernames to filter

        Returns:
            Dictionary mapping username to UserActivity
        """
        user_activity = defaultdict(lambda: {
            'tickets_created': [],
            'tickets_assigned': [],
            'customers': set(),
            'projects': set(),
            'by_customer': defaultdict(list),
            'by_project': defaultdict(list),
            'total_tickets': 0,
            'total_open': 0,
            'total_closed': 0,
            'by_priority': defaultdict(int)
        })

        for ticket in tickets:
            # Enrich ticket
            enriched = self.enrich_ticket(ticket)

            user_name = enriched.user_name

            # Filter by user if specified
            if filter_users and user_name not in filter_users:
                continue

            # Aggregate data
            user_activity[user_name]['tickets_assigned'].append(enriched)
            user_activity[user_name]['customers'].add(enriched.customer_name)
            user_activity[user_name]['projects'].add(enriched.project_name)
            user_activity[user_name]['by_customer'][enriched.customer_name].append(enriched)
            user_activity[user_name]['by_project'][enriched.project_name].append(enriched)
            user_activity[user_name]['total_tickets'] += 1

            if enriched.is_closed:
                user_activity[user_name]['total_closed'] += 1
            else:
                user_activity[user_name]['total_open'] += 1

            # Priority stats
            user_activity[user_name]['by_priority'][enriched.priority] += 1

        # Convert to UserActivity models
        result = {}
        for user_name, data in user_activity.items():
            result[user_name] = UserActivity(
                user_name=user_name,
                tickets_assigned=data['tickets_assigned'],
                customers=sorted(list(data['customers'])),
                projects=sorted(list(data['projects'])),
                by_customer=dict(data['by_customer']),
                by_project=dict(data['by_project']),
                total_tickets=data['total_tickets'],
                total_open=data['total_open'],
                total_closed=data['total_closed'],
                by_priority=dict(data['by_priority'])
            )

        return result

    def query_natural_language(self, query: str, limit: int = 50) -> List[EnrichedTicket]:
        """Natural language query (used by API).

        Args:
            query: Natural language query string
            limit: Maximum results

        Returns:
            List of enriched tickets
        """
        from ..utils.query_parser import QueryParser

        parser = QueryParser(user_id=self.api.uid, username=self.config.user)
        domain, options = parser.parse(query)

        raw_tickets = self.query_tickets(
            domain=domain,
            limit=options.get('limit', limit),
            order=options.get('order', 'write_date desc'),
            fields=options.get('fields')
        )

        return [self.enrich_ticket(t) for t in raw_tickets]

    def get_query_summary(self, query: str) -> str:
        """Get human-readable summary of a query.

        Args:
            query: Natural language query

        Returns:
            Query summary string
        """
        from ..utils.query_parser import QueryParser

        parser = QueryParser(user_id=self.api.uid, username=self.config.user)
        domain, options = parser.parse(query)
        return parser.get_query_summary(domain, options)

    def get_current_user_id(self) -> int:
        """Get current authenticated user ID.

        Returns:
            Odoo user ID
        """
        return self.api.get_current_user_id()
