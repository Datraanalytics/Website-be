from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional
from app.database import get_db
from app.schemas import KPIResponse, FilterOptions

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

# Map frontend periods to database periods
PERIOD_MAP = {
    "3M": "3M",
    "6M": "6M",
    "1Y": "12M",
    "12M": "12M",
    "CurrentMonth": "CurrentMonth"
}


@router.get("/kpi", response_model=KPIResponse)
async def get_dashboard_kpi(
    period: str = Query("6M", description="Time period: 3M, 6M, 1Y"),
    property_type: Optional[str] = Query(None, description="Residential or Commercial"),
    sale_type: Optional[str] = Query(None, description="Sale or Resale"),
    state: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard KPI metrics from topGainer table"""

    db_period = PERIOD_MAP.get(period, "6M")

    conditions = ["period = :period"]
    params = {"period": db_period}

    if property_type:
        conditions.append("transactionType = :property_type")
        params["property_type"] = property_type

    if sale_type:
        # Map Sale to Primary for database
        sale_val = "Primary" if sale_type == "Sale" else sale_type
        conditions.append("Sale_resale = :sale_type")
        params["sale_type"] = sale_val

    if state:
        conditions.append("state = :state")
        params["state"] = state

    if city:
        conditions.append("city = :city")
        params["city"] = city

    where_clause = " AND ".join(conditions)

    query = text(f"""
        SELECT
            COALESCE(SUM(noOfTrans), 0) as total_transactions,
            COALESCE(SUM(compensationInCr), 0) as total_market_value,
            COALESCE(AVG(weightageAvgValue), 0) as average_price,
            COALESCE(SUM(chargeableSQFTInMillion), 0) as total_area_sold
        FROM topGainer
        WHERE {where_clause}
    """)

    result = await db.execute(query, params)
    row = result.fetchone()

    return KPIResponse(
        total_transactions=int(row.total_transactions) if row.total_transactions else 0,
        total_market_value=float(row.total_market_value) if row.total_market_value else 0.0,
        average_price=float(row.average_price) if row.average_price else 0.0,
        total_area_sold=float(row.total_area_sold) * 1000000 if row.total_area_sold else 0.0
    )


@router.get("/filters", response_model=FilterOptions)
async def get_filter_options(db: AsyncSession = Depends(get_db)):
    """Get available filter options"""

    # Get distinct states
    states_query = text("SELECT DISTINCT state FROM topGainer WHERE state IS NOT NULL ORDER BY state")
    states_result = await db.execute(states_query)
    states = [row[0] for row in states_result.fetchall()]

    # Get distinct cities
    cities_query = text("SELECT DISTINCT city FROM topGainer WHERE city IS NOT NULL ORDER BY city")
    cities_result = await db.execute(cities_query)
    cities = [row[0] for row in cities_result.fetchall()]

    return FilterOptions(
        states=states,
        cities=cities,
        periods=["3M", "6M", "1Y"],
        property_types=["Residential", "Commercial"],
        sale_types=["Sale", "Resale"]
    )


@router.get("/trends")
async def get_market_trends(
    period: str = Query("6M"),
    property_type: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get market trends data for charts"""

    db_period = PERIOD_MAP.get(period, "6M")

    conditions = ["period = :period"]
    params = {"period": db_period}

    if property_type:
        conditions.append("transactionType = :property_type")
        params["property_type"] = property_type

    if city:
        conditions.append("city = :city")
        params["city"] = city

    where_clause = " AND ".join(conditions)

    query = text(f"""
        SELECT
            city,
            SUM(noOfTrans) as transactions,
            SUM(compensationInCr) as market_value,
            AVG(weightageAvgValue) as avg_price
        FROM topGainer
        WHERE {where_clause}
        GROUP BY city
        ORDER BY market_value DESC
        LIMIT 10
    """)

    result = await db.execute(query, params)
    rows = result.fetchall()

    return {
        "labels": [row.city for row in rows],
        "transactions": [int(row.transactions) for row in rows],
        "market_value": [float(row.market_value) for row in rows],
        "avg_price": [float(row.avg_price) for row in rows]
    }


@router.get("/summary")
async def get_dashboard_summary(
    period: str = Query("6M"),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard summary with property type breakdown"""

    db_period = PERIOD_MAP.get(period, "6M")

    query = text("""
        SELECT
            transactionType,
            Sale_resale,
            SUM(noOfTrans) as transactions,
            SUM(compensationInCr) as value,
            AVG(weightageAvgValue) as avg_price
        FROM topGainer
        WHERE period = :period
        GROUP BY transactionType, Sale_resale
    """)

    result = await db.execute(query, {"period": db_period})
    rows = result.fetchall()

    summary = {}
    for row in rows:
        # Map Primary to Sale for frontend display
        sale_type = "Sale" if row.Sale_resale == "Primary" else row.Sale_resale
        key = f"{row.transactionType}_{sale_type}"
        summary[key] = {
            "transactions": int(row.transactions) if row.transactions else 0,
            "value": float(row.value) if row.value else 0.0,
            "avg_price": float(row.avg_price) if row.avg_price else 0.0
        }

    return summary


@router.get("/search")
async def search_data(
    q: str = Query(..., min_length=2, description="Search query"),
    city: Optional[str] = Query(None),
    period: str = Query("6M"),
    db: AsyncSession = Depends(get_db)
):
    """Search for localities, projects, or developers"""

    db_period = PERIOD_MAP.get(period, "6M")
    search_term = f"%{q}%"

    results = {
        "localities": [],
        "developers": []
    }

    # Search localities
    locality_conditions = ["period = :period", "locality LIKE :search"]
    locality_params = {"period": db_period, "search": search_term}

    if city:
        locality_conditions.append("city = :city")
        locality_params["city"] = city

    locality_query = text(f"""
        SELECT
            locality,
            city,
            state,
            SUM(noOfTrans) as total_transactions,
            AVG(weightageAvgValue) as avg_price,
            SUM(compensationInCr) as total_value
        FROM topGainer
        WHERE {" AND ".join(locality_conditions)}
        GROUP BY locality, city, state
        ORDER BY total_value DESC
        LIMIT 10
    """)

    try:
        locality_result = await db.execute(locality_query, locality_params)
        locality_rows = locality_result.fetchall()
        results["localities"] = [
            {
                "locality": row.locality,
                "city": row.city,
                "state": row.state,
                "total_transactions": int(row.total_transactions) if row.total_transactions else 0,
                "avg_price": float(row.avg_price) if row.avg_price else 0.0,
                "total_value": float(row.total_value) if row.total_value else 0.0
            }
            for row in locality_rows
        ]
    except Exception:
        pass

    # Search developers
    developer_query = text("""
        SELECT
            Developer as developer,
            SUM(NoofTransaction) as total_transactions,
            SUM(TotalValueInCr) as total_value
        FROM topDevelopers
        WHERE period = :period AND Developer LIKE :search
        GROUP BY Developer
        ORDER BY total_value DESC
        LIMIT 10
    """)

    try:
        developer_result = await db.execute(developer_query, {"period": db_period, "search": search_term})
        developer_rows = developer_result.fetchall()
        results["developers"] = [
            {
                "developer": row.developer,
                "total_transactions": int(row.total_transactions) if row.total_transactions else 0,
                "total_value": float(row.total_value) if row.total_value else 0.0
            }
            for row in developer_rows
        ]
    except Exception:
        pass

    return results
