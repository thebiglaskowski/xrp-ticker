"""Pydantic models for XRP Ticker data structures."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class ConnectionState(str, Enum):
    """WebSocket connection states."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


class PriceData(BaseModel):
    """Real-time price data from exchange."""

    symbol: str = "XRPUSDT"
    price: float = Field(ge=0, description="Current price in USD")
    price_change: float = Field(default=0.0, description="24h price change in USD")
    price_change_percent: float = Field(default=0.0, description="24h price change percentage")
    high_24h: float | None = Field(default=None, ge=0, description="24h high price")
    low_24h: float | None = Field(default=None, ge=0, description="24h low price")
    volume: float | None = Field(default=None, ge=0, description="24h trading volume")
    timestamp: datetime = Field(default_factory=datetime.now)
    source: str = Field(default="unknown", description="Data source name")

    @field_validator("price", "high_24h", "low_24h", mode="before")
    @classmethod
    def parse_string_float(cls, v):
        """Parse string values to float."""
        if isinstance(v, str):
            return float(v)
        return v


class WalletData(BaseModel):
    """Wallet balance data from XRPL."""

    address: str = Field(description="XRP wallet address")
    balance_drops: int = Field(ge=0, description="Balance in drops (1 XRP = 1,000,000 drops)")
    balance_xrp: float = Field(ge=0, description="Balance in XRP")
    timestamp: datetime = Field(default_factory=datetime.now)
    source: str = Field(default="xrpl", description="Data source")

    @field_validator("balance_xrp", mode="before")
    @classmethod
    def calculate_xrp_from_drops(cls, v, info):
        """Calculate XRP from drops if not provided."""
        if v is None or v == 0:
            drops = info.data.get("balance_drops", 0)
            return drops / 1_000_000
        return v

    @classmethod
    def from_drops(cls, address: str, drops: int, source: str = "xrpl") -> "WalletData":
        """Create WalletData from drops value."""
        return cls(
            address=address,
            balance_drops=drops,
            balance_xrp=drops / 1_000_000,
            source=source,
        )


class XRPLAccountInfo(BaseModel):
    """XRPL account_info response format."""

    Account: str
    Balance: str

    def to_wallet_data(self) -> WalletData:
        """Convert XRPL response to WalletData."""
        drops = int(self.Balance)
        return WalletData.from_drops(address=self.Account, drops=drops, source="xrpl")


class XRPLResponse(BaseModel):
    """XRPL WebSocket response wrapper."""

    result: dict | None = None
    error: str | None = None
    error_message: str | None = None
    status: str | None = None


class ServiceStatus(BaseModel):
    """Status of a WebSocket service."""

    name: str
    state: ConnectionState = ConnectionState.DISCONNECTED
    last_message: datetime | None = None
    reconnect_attempts: int = 0
    error_message: str | None = None

    @property
    def is_connected(self) -> bool:
        """Check if service is connected."""
        return self.state == ConnectionState.CONNECTED

    @property
    def is_stale(self) -> bool:
        """Check if data is stale (no message for 30 seconds)."""
        if not self.last_message:
            return True
        return (datetime.now() - self.last_message).total_seconds() > 30
