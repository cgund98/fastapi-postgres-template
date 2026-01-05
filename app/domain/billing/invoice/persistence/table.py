"""Invoice table definition."""

from sqlalchemy import Column, DateTime, ForeignKey, MetaData, Numeric, String, Table
from sqlalchemy.dialects.postgresql import UUID

metadata: MetaData = MetaData()

invoices_table = Table(
    "invoices",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("amount", Numeric(10, 2), nullable=False),
    Column("status", String(50), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("paid_at", DateTime(timezone=True), nullable=True),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)
