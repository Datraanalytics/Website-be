from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional
from app.database import get_db
from app.schemas import DeveloperData, DeveloperAnalyticsResponse

router = APIRouter(prefix="/api/developers", tags=["Developer Analytics"])

# Map frontend periods to database periods
PERIOD_MAP = {
    "3M": "3M",
    "6M": "6M",
    "1Y": "12M",
    "12M": "12M",
    "CurrentMonth": "CurrentMonth"
}


@router.get("", response_model=DeveloperAnalyticsResponse)
async def get_developer_analytics(
    city: Optional[str] = Query(None, description="Filter by city (not supported in topDevelopers)"),
    period: str = Query("6M", description="Time period: 3M, 6M, 1Y"),
    db: AsyncSession = Depends(get_db)
):
    """Get developer analytics from topDevelopers table"""

    db_period = PERIOD_MAP.get(period, "6M")

    query = text("""
        SELECT
            Developer as developer,
            Sale_resale,
            SUM(NoofTransaction) as total_transactions,
            SUM(TotalValueInCr) as total_value,
            SUM(TotalSQFTinMillion) as total_sqft
        FROM topDevelopers
        WHERE period = :period
        GROUP BY Developer, Sale_resale
        ORDER BY total_value DESC
        LIMIT 50
    """)

    try:
        result = await db.execute(query, {"period": db_period})
        rows = result.fetchall()

        developers = [
            DeveloperData(
                developer=row.developer if row.developer else "Unknown",
                city=None,  # topDevelopers doesn't have city column
                total_transactions=int(row.total_transactions) if row.total_transactions else 0,
                total_value=float(row.total_value) if row.total_value else 0.0,
                avg_price=0.0  # topDevelopers doesn't have avg price
            )
            for row in rows
        ]

        return DeveloperAnalyticsResponse(developers=developers)
    except Exception as e:
        print(f"Developer analytics error: {e}")
        return DeveloperAnalyticsResponse(developers=[])


@router.get("/top")
async def get_top_developers(
    city: Optional[str] = Query(None),
    period: str = Query("6M"),
    sort_by: str = Query("total_value", description="Sort by: total_value, transactions"),
    limit: int = Query(20),
    db: AsyncSession = Depends(get_db)
):
    """Get top developers ranked by different metrics"""

    db_period = PERIOD_MAP.get(period, "6M")

    valid_sort_fields = {
        "total_value": "total_value DESC",
        "transactions": "total_transactions DESC"
    }

    order_by = valid_sort_fields.get(sort_by, "total_value DESC")

    # Note: topDevelopers doesn't have city column, so city filter is ignored
    # Use topDevelopers for overall developer rankings
    query = text(f"""
        SELECT
            Developer as developer,
            NULL as city,
            SUM(NoofTransaction) as total_transactions,
            SUM(TotalValueInCr) as total_value,
            0 as avg_price
        FROM topDevelopers
        WHERE period = :period
        GROUP BY Developer
        ORDER BY {order_by}
        LIMIT :limit
    """)
    params = {"period": db_period, "limit": limit}

    try:
        result = await db.execute(query, params)
        rows = result.fetchall()

        return [
            {
                "rank": idx + 1,
                "developer": row.developer if row.developer else "Unknown",
                "city": row.city,
                "total_transactions": int(row.total_transactions) if row.total_transactions else 0,
                "total_value": float(row.total_value) if row.total_value else 0.0,
                "avg_price": float(row.avg_price) if row.avg_price else 0.0
            }
            for idx, row in enumerate(rows)
        ]
    except Exception as e:
        return {"error": str(e), "message": "Error fetching developer data"}


@router.get("/summary")
async def get_developer_summary(
    period: str = Query("6M"),
    db: AsyncSession = Depends(get_db)
):
    """Get developer summary by sale type"""

    db_period = PERIOD_MAP.get(period, "6M")

    query = text("""
        SELECT
            Sale_resale,
            COUNT(DISTINCT Developer) as developer_count,
            SUM(NoofTransaction) as total_transactions,
            SUM(TotalValueInCr) as total_value,
            SUM(TotalSQFTinMillion) as total_sqft
        FROM topDevelopers
        WHERE period = :period
        GROUP BY Sale_resale
    """)

    try:
        result = await db.execute(query, {"period": db_period})
        rows = result.fetchall()

        return [
            {
                "sale_type": "Sale" if row.Sale_resale == "Primary" else row.Sale_resale,
                "developer_count": int(row.developer_count) if row.developer_count else 0,
                "total_transactions": int(row.total_transactions) if row.total_transactions else 0,
                "total_value": float(row.total_value) if row.total_value else 0.0,
                "total_sqft": float(row.total_sqft) if row.total_sqft else 0.0
            }
            for row in rows
        ]
    except Exception as e:
        return {"error": str(e)}


@router.get("/compare")
async def compare_developers(
    developers: str = Query(..., description="Comma-separated developer names"),
    period: str = Query("6M"),
    db: AsyncSession = Depends(get_db)
):
    """Compare multiple developers"""

    db_period = PERIOD_MAP.get(period, "6M")

    developer_list = [d.strip() for d in developers.split(",")]
    placeholders = ", ".join([f":dev_{i}" for i in range(len(developer_list))])
    params = {"period": db_period}
    params.update({f"dev_{i}": dev for i, dev in enumerate(developer_list)})

    query = text(f"""
        SELECT
            Developer as developer,
            Sale_resale,
            SUM(NoofTransaction) as transactions,
            SUM(TotalValueInCr) as value,
            SUM(TotalSQFTinMillion) as total_sqft
        FROM topDevelopers
        WHERE Developer IN ({placeholders}) AND period = :period
        GROUP BY Developer, Sale_resale
        ORDER BY Developer, value DESC
    """)

    try:
        result = await db.execute(query, params)
        rows = result.fetchall()

        comparison = {}
        for row in rows:
            dev_name = row.developer if row.developer else "Unknown"
            if dev_name not in comparison:
                comparison[dev_name] = {"sale_types": [], "total_value": 0, "total_transactions": 0}
            comparison[dev_name]["sale_types"].append({
                "sale_type": row.Sale_resale,
                "transactions": int(row.transactions) if row.transactions else 0,
                "value": float(row.value) if row.value else 0.0,
                "total_sqft": float(row.total_sqft) if row.total_sqft else 0.0
            })
            comparison[dev_name]["total_value"] += float(row.value) if row.value else 0
            comparison[dev_name]["total_transactions"] += int(row.transactions) if row.transactions else 0

        return comparison
    except Exception as e:
        return {"error": str(e)}
