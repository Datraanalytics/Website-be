from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# Request Schemas
class DashboardFilters(BaseModel):
    period: str = "6M"
    property_type: Optional[str] = None  # Residential / Commercial
    sale_type: Optional[str] = None  # Sale / Resale
    state: Optional[str] = None
    city: Optional[str] = None


class CityAnalyticsFilters(BaseModel):
    period: str = "6M"
    transaction_type: Optional[str] = None


class LocalityFilters(BaseModel):
    city: str
    period: str = "6M"
    transaction_type: Optional[str] = None
    sale_type: Optional[str] = None


class DeveloperFilters(BaseModel):
    city: Optional[str] = None
    period: str = "6M"


class ProjectFilters(BaseModel):
    city: Optional[str] = None
    developer: Optional[str] = None
    period: str = "6M"


class RentalFilters(BaseModel):
    city: Optional[str] = None
    period: str = "6M"


# Response Schemas
class KPIResponse(BaseModel):
    total_transactions: int
    total_market_value: float
    average_price: float
    total_area_sold: float


class CityData(BaseModel):
    city: str
    state: Optional[str] = None
    total_transactions: int
    total_value: float
    avg_price: float
    area_sold: Optional[float] = None


class CityAnalyticsResponse(BaseModel):
    cities: List[CityData]
    top_gainers: List[dict]


class LocalityData(BaseModel):
    locality: str
    city: str
    total_transactions: int
    avg_price: float
    total_value: float
    area_sold: Optional[float] = None


class LocalityAnalyticsResponse(BaseModel):
    localities: List[LocalityData]
    city: str


class DeveloperData(BaseModel):
    developer: str
    city: Optional[str] = None
    total_transactions: int
    total_value: float
    avg_price: float


class DeveloperAnalyticsResponse(BaseModel):
    developers: List[DeveloperData]


class ProjectData(BaseModel):
    project: str
    developer: str
    city: str
    locality: Optional[str] = None
    total_transactions: int
    price_change: Optional[float] = None
    percent_change: Optional[float] = None


class ProjectAnalyticsResponse(BaseModel):
    projects: List[ProjectData]


class RentalCityData(BaseModel):
    city: str
    avg_rent: float
    total_transactions: int
    rent_change: Optional[float] = None
    percent_change: Optional[float] = None


class RentalAnalyticsResponse(BaseModel):
    cities: List[RentalCityData]
    top_gainers: List[dict]


class FilterOptions(BaseModel):
    states: List[str]
    cities: List[str]
    periods: List[str] = ["3M", "6M", "1Y"]
    property_types: List[str] = ["Residential", "Commercial"]
    sale_types: List[str] = ["Sale", "Resale"]


class ChartData(BaseModel):
    labels: List[str]
    datasets: List[dict]
