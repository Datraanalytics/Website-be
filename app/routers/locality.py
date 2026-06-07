from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional
from app.database import get_db
from app.schemas import LocalityData, LocalityAnalyticsResponse

router = APIRouter(prefix="/api/locality", tags=["Locality Analytics"])

# Map frontend periods to database periods
PERIOD_MAP = {
    "3M": "3M",
    "6M": "6M",
    "1Y": "12M",
    "12M": "12M",
    "CurrentMonth": "CurrentMonth"
}


@router.get("", response_model=LocalityAnalyticsResponse)
async def get_locality_analytics(
    city: str = Query(..., description="City name (required)"),
    period: str = Query("6M", description="Time period: 3M, 6M, 1Y"),
    transaction_type: Optional[str] = Query(None, description="Residential or Commercial"),
    sale_type: Optional[str] = Query(None, description="Sale or Resale"),
    db: AsyncSession = Depends(get_db)
):
    """Get locality-wise analytics for a specific city"""

    db_period = PERIOD_MAP.get(period, "6M")

    conditions = ["city = :city", "period = :period"]
    params = {"city": city, "period": db_period}

    if transaction_type:
        conditions.append("transactionType = :transaction_type")
        params["transaction_type"] = transaction_type

    if sale_type:
        # Map Sale to Primary for database
        sale_val = "Primary" if sale_type == "Sale" else sale_type
        conditions.append("Sale_resale = :sale_type")
        params["sale_type"] = sale_val

    where_clause = " AND ".join(conditions)

    query = text(f"""
        SELECT
            locality,
            city,
            SUM(noOfTrans) as total_transactions,
            AVG(weightageAvgValue) as avg_price,
            SUM(compensationInCr) as total_value,
            SUM(chargeableSQFTInMillion) as area_sold
        FROM topGainer
        WHERE {where_clause}
        GROUP BY locality, city
        ORDER BY total_value DESC
        LIMIT 100
    """)

    result = await db.execute(query, params)
    rows = result.fetchall()

    localities = [
        LocalityData(
            locality=row.locality if row.locality else "Unknown",
            city=row.city,
            total_transactions=int(row.total_transactions) if row.total_transactions else 0,
            avg_price=float(row.avg_price) if row.avg_price else 0.0,
            total_value=float(row.total_value) if row.total_value else 0.0,
            area_sold=float(row.area_sold) * 1000000 if row.area_sold else 0.0
        )
        for row in rows
    ]

    return LocalityAnalyticsResponse(localities=localities, city=city)


@router.get("/top")
async def get_top_localities(
    city: str = Query(...),
    period: str = Query("6M"),
    sort_by: str = Query("total_value", description="Sort by: total_value, transactions, avg_price"),
    limit: int = Query(20),
    db: AsyncSession = Depends(get_db)
):
    """Get top localities in a city"""

    db_period = PERIOD_MAP.get(period, "6M")

    valid_sort_fields = {
        "total_value": "total_value DESC",
        "transactions": "total_transactions DESC",
        "avg_price": "avg_price DESC"
    }

    order_by = valid_sort_fields.get(sort_by, "total_value DESC")

    query = text(f"""
        SELECT
            locality,
            SUM(noOfTrans) as total_transactions,
            AVG(weightageAvgValue) as avg_price,
            SUM(compensationInCr) as total_value,
            SUM(chargeableSQFTInMillion) as area_sold
        FROM topGainer
        WHERE city = :city AND period = :period
        GROUP BY locality
        ORDER BY {order_by}
        LIMIT :limit
    """)

    result = await db.execute(query, {"city": city, "period": db_period, "limit": limit})
    rows = result.fetchall()

    return [
        {
            "rank": idx + 1,
            "locality": row.locality if row.locality else "Unknown",
            "total_transactions": int(row.total_transactions) if row.total_transactions else 0,
            "avg_price": float(row.avg_price) if row.avg_price else 0.0,
            "total_value": float(row.total_value) if row.total_value else 0.0,
            "area_sold": float(row.area_sold) * 1000000 if row.area_sold else 0.0
        }
        for idx, row in enumerate(rows)
    ]


@router.get("/breakdown")
async def get_locality_breakdown(
    city: str = Query(...),
    locality: str = Query(...),
    period: str = Query("6M"),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed breakdown for a specific locality"""

    db_period = PERIOD_MAP.get(period, "6M")

    query = text("""
        SELECT
            transactionType,
            Sale_resale,
            SUM(noOfTrans) as transactions,
            AVG(weightageAvgValue) as avg_price,
            SUM(compensationInCr) as value
        FROM topGainer
        WHERE city = :city AND locality = :locality AND period = :period
        GROUP BY transactionType, Sale_resale
    """)

    result = await db.execute(query, {"city": city, "locality": locality, "period": db_period})
    rows = result.fetchall()

    breakdown = {
        "locality": locality,
        "city": city,
        "period": period,
        "data": [
            {
                "transaction_type": row.transactionType,
                "sale_type": row.Sale_resale,
                "transactions": int(row.transactions) if row.transactions else 0,
                "avg_price": float(row.avg_price) if row.avg_price else 0.0,
                "value": float(row.value) if row.value else 0.0
            }
            for row in rows
        ]
    }

    return breakdown


@router.get("/compare")
async def compare_localities(
    city: str = Query(...),
    localities: str = Query(..., description="Comma-separated locality names"),
    period: str = Query("6M"),
    db: AsyncSession = Depends(get_db)
):
    """Compare multiple localities within a city"""

    db_period = PERIOD_MAP.get(period, "6M")

    locality_list = [l.strip() for l in localities.split(",")]
    placeholders = ", ".join([f":locality_{i}" for i in range(len(locality_list))])
    params = {"city": city, "period": db_period}
    params.update({f"locality_{i}": loc for i, loc in enumerate(locality_list)})

    query = text(f"""
        SELECT
            locality,
            transactionType,
            SUM(noOfTrans) as transactions,
            AVG(weightageAvgValue) as avg_price,
            SUM(compensationInCr) as value
        FROM topGainer
        WHERE city = :city AND period = :period AND locality IN ({placeholders})
        GROUP BY locality, transactionType
        ORDER BY locality, transactionType
    """)

    result = await db.execute(query, params)
    rows = result.fetchall()

    comparison = {}
    for row in rows:
        if row.locality not in comparison:
            comparison[row.locality] = {}
        comparison[row.locality][row.transactionType] = {
            "transactions": int(row.transactions) if row.transactions else 0,
            "avg_price": float(row.avg_price) if row.avg_price else 0.0,
            "value": float(row.value) if row.value else 0.0
        }

    return comparison
