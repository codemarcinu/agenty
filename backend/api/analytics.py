"""
Analytics API Endpoints

This module provides API endpoints for expense analytics and reporting:
- Expense statistics
- Spending trends
- Category analysis
- Budget tracking
- Financial insights
"""

from datetime import datetime, timedelta
import logging

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from infrastructure.database.database import get_db
from models.shopping import Product, ShoppingTrip

router = APIRouter(tags=["Analytics"])
logger = logging.getLogger(__name__)


@router.get("/expenses", response_model=None)
async def get_expense_analytics(
    start_date: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    category_id: int | None = Query(None, description="Filter by category ID"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get comprehensive expense analytics
    """
    try:
        # Parse dates
        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").replace(
                tzinfo=datetime.now().astimezone().tzinfo
            )
        else:
            start_date = datetime.now().astimezone() - timedelta(
                days=30
            )  # Last 30 days

        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d").replace(
                tzinfo=datetime.now().astimezone().tzinfo
            )
        else:
            end_date = datetime.now().astimezone()

        # Build query
        query = select(ShoppingTrip).options(selectinload(ShoppingTrip.products))

        # Apply date filter
        query = query.where(
            and_(
                ShoppingTrip.created_at >= start_date,
                ShoppingTrip.created_at <= end_date,
            )
        )

        # Apply category filter if specified
        if category_id:
            query = query.join(Product).where(Product.category == str(category_id))

        # Execute query
        result = await db.execute(query)
        trips = result.scalars().all()

        # Calculate analytics
        total_expenses = sum(trip.total_amount for trip in trips if trip.total_amount)
        trip_count = len(trips)

        # Category breakdown
        category_expenses = {}
        for trip in trips:
            for product in trip.products:
                if product.category:
                    cat_name = product.category
                    if cat_name not in category_expenses:
                        category_expenses[cat_name] = 0
                    category_expenses[cat_name] += product.unit_price or 0

        # Monthly trend (last 6 months)
        monthly_trend = []
        now = datetime.now().astimezone()
        for i in range(6):
            month_start = now.replace(day=1) - timedelta(days=30 * i)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(
                days=1
            )

            month_trips = [
                trip for trip in trips if month_start <= trip.created_at <= month_end
            ]
            month_total = sum(
                trip.total_amount for trip in month_trips if trip.total_amount
            )

            monthly_trend.append(
                {
                    "month": month_start.strftime("%Y-%m"),
                    "total": month_total,
                    "trip_count": len(month_trips),
                }
            )

        # Average spending per trip
        avg_per_trip = total_expenses / trip_count if trip_count > 0 else 0

        # Most expensive trips
        expensive_trips = sorted(
            [
                {
                    "id": trip.id,
                    "total": trip.total_amount,
                    "date": trip.created_at.isoformat(),
                }
                for trip in trips
                if trip.total_amount
            ],
            key=lambda x: x["total"],
            reverse=True,
        )[:5]

        analytics_data = {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": (end_date - start_date).days,
            },
            "summary": {
                "total_expenses": round(total_expenses, 2),
                "trip_count": trip_count,
                "average_per_trip": round(avg_per_trip, 2),
                "total_products": sum(len(trip.products) for trip in trips),
            },
            "category_breakdown": [
                {
                    "category": cat,
                    "amount": round(amount, 2),
                    "percentage": (
                        round(amount / total_expenses * 100, 1)
                        if total_expenses > 0
                        else 0
                    ),
                }
                for cat, amount in sorted(
                    category_expenses.items(), key=lambda x: x[1], reverse=True
                )
            ],
            "monthly_trend": monthly_trend,
            "expensive_trips": expensive_trips,
            "insights": _generate_insights(
                total_expenses, trip_count, category_expenses, monthly_trend
            ),
        }

        return JSONResponse(
            status_code=200,
            content={
                "status_code": 200,
                "message": "Expense analytics retrieved successfully",
                "data": analytics_data,
            },
        )

    except Exception as e:
        logger.error(f"Error getting expense analytics: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to get expense analytics",
                "details": {"error": str(e)},
            },
        )


@router.get("/budget", response_model=None)
async def get_budget_analytics(
    monthly_budget: float = Query(2000.0, description="Monthly budget amount"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get budget tracking analytics
    """
    try:
        # Get current month expenses
        now = datetime.now().astimezone()
        current_month_start = now.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        current_month_end = (current_month_start + timedelta(days=32)).replace(
            day=1
        ) - timedelta(days=1)

        query = select(ShoppingTrip).where(
            and_(
                ShoppingTrip.created_at >= current_month_start,
                ShoppingTrip.created_at <= current_month_end,
            )
        )

        result = await db.execute(query)
        trips = result.scalars().all()

        current_month_expenses = sum(
            trip.total_amount for trip in trips if trip.total_amount
        )
        days_in_month = current_month_end.day
        days_elapsed = datetime.now().day

        # Calculate budget metrics
        budget_used = current_month_expenses
        budget_remaining = monthly_budget - budget_used
        budget_usage_percentage = (
            (budget_used / monthly_budget) * 100 if monthly_budget > 0 else 0
        )

        # Projected spending
        daily_average = budget_used / days_elapsed if days_elapsed > 0 else 0
        projected_monthly = daily_average * days_in_month

        # Budget status
        if budget_usage_percentage > 90:
            status = "critical"
        elif budget_usage_percentage > 75:
            status = "warning"
        else:
            status = "good"

        budget_data = {
            "monthly_budget": monthly_budget,
            "current_month": {
                "expenses": round(budget_used, 2),
                "remaining": round(budget_remaining, 2),
                "usage_percentage": round(budget_usage_percentage, 1),
                "days_elapsed": days_elapsed,
                "days_in_month": days_in_month,
            },
            "projections": {
                "daily_average": round(daily_average, 2),
                "projected_monthly": round(projected_monthly, 2),
                "projected_overspend": (
                    round(projected_monthly - monthly_budget, 2)
                    if projected_monthly > monthly_budget
                    else 0
                ),
            },
            "status": status,
            "recommendations": _generate_budget_recommendations(
                budget_usage_percentage, projected_monthly, monthly_budget
            ),
        }

        return JSONResponse(
            status_code=200,
            content={
                "status_code": 200,
                "message": "Budget analytics retrieved successfully",
                "data": budget_data,
            },
        )

    except Exception as e:
        logger.error(f"Error getting budget analytics: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to get budget analytics",
                "details": {"error": str(e)},
            },
        )


def _generate_insights(
    total_expenses: float,
    trip_count: int,
    category_expenses: dict[str, float],
    monthly_trend: list[dict],
) -> list[str]:
    """Generate insights from analytics data"""
    insights = []

    if total_expenses > 0:
        # Top spending category
        if category_expenses:
            top_category = max(category_expenses.items(), key=lambda x: x[1])
            insights.append(
                f"Główna kategoria wydatków: {top_category[0]} ({top_category[1]:.2f} zł)"
            )

        # Spending trend
        if len(monthly_trend) >= 2:
            recent = monthly_trend[0]["total"]
            previous = monthly_trend[1]["total"]
            if recent > previous * 1.1:
                insights.append(
                    "Wydatki wzrosły o ponad 10% w porównaniu do poprzedniego miesiąca"
                )
            elif recent < previous * 0.9:
                insights.append(
                    "Wydatki spadły o ponad 10% w porównaniu do poprzedniego miesiąca"
                )

        # Trip frequency
        if trip_count > 0:
            avg_trip_value = total_expenses / trip_count
            insights.append(f"Średnia wartość zakupów: {avg_trip_value:.2f} zł")

    return insights


def _generate_budget_recommendations(
    usage_percentage: float, projected_monthly: float, monthly_budget: float
) -> list[str]:
    """Generate budget recommendations"""
    recommendations = []

    if usage_percentage > 90:
        recommendations.append(
            "⚠️ Krytyczny poziom wydatków - rozważ ograniczenie zakupów"
        )
    elif usage_percentage > 75:
        recommendations.append("⚠️ Wysoki poziom wydatków - monitoruj wydatki")

    if projected_monthly > monthly_budget * 1.1:
        recommendations.append(
            "📈 Projektowane przekroczenie budżetu - zmniejsz wydatki"
        )
    elif projected_monthly < monthly_budget * 0.8:
        recommendations.append(
            "✅ Dobra kontrola wydatków - możesz pozwolić sobie na więcej"
        )

    return recommendations
