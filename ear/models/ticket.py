"""Pydantic models for Odoo tickets."""

from typing import Optional, Dict, List
from pydantic import BaseModel, Field
from datetime import datetime


class OdooTicket(BaseModel):
    """Raw Odoo ticket data."""
    id: int
    name: str
    description: Optional[str] = None
    priority: str = "0"
    create_date: Optional[str] = None
    write_date: Optional[str] = None
    close_date: Optional[str] = None
    user_id: Optional[tuple] = None
    partner_id: Optional[tuple] = None
    project_id: Optional[tuple] = None
    stage_id: Optional[tuple] = None

    class Config:
        arbitrary_types_allowed = True


class EnrichedTicket(BaseModel):
    """Enriched ticket with readable fields."""
    id: int
    name: str
    description: Optional[str] = None
    priority: str = "0"
    create_date: Optional[str] = None
    write_date: Optional[str] = None
    close_date: Optional[str] = None
    is_closed: bool = False

    # Enriched fields (extracted from tuples)
    user: str = "Unassigned"
    user_name: str = "Unassigned"  # Alias for compatibility
    customer: str = "No Customer"
    customer_name: str = "No Customer"  # Alias for compatibility
    project: str = "No Project"
    project_name: str = "No Project"  # Alias for compatibility
    stage: str = "Unknown"
    stage_name: str = "Unknown"  # Alias for compatibility


class UserActivity(BaseModel):
    """Aggregated Odoo activity for a user."""
    user_name: str
    tickets_created: List[EnrichedTicket] = Field(default_factory=list)
    tickets_assigned: List[EnrichedTicket] = Field(default_factory=list)
    customers: List[str] = Field(default_factory=list)
    projects: List[str] = Field(default_factory=list)
    by_customer: Dict[str, List[EnrichedTicket]] = Field(default_factory=dict)
    by_project: Dict[str, List[EnrichedTicket]] = Field(default_factory=dict)
    total_tickets: int = 0
    total_open: int = 0
    total_closed: int = 0
    by_priority: Dict[str, int] = Field(default_factory=dict)
