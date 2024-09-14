# api/tasks.py
from celery import shared_task, Celery
from celery.schedules import crontab
from django.core.cache import cache
from .helpers import lookup_quote, lookup_basic_financial, lookup_profile
from api.models import Portfolio, PortfolioHistory, UserProfile
from datetime import datetime, timedelta
from django.utils import timezone
from decimal import Decimal
import pytz





# Fetch and cache real-time stock quotes every minute during US market hours
@shared_task
def cache_all_stocks():
    """Task to cache real-time stock data for all symbols in Portfolio model."""
    print("I am caching all stocks !!!")
    now = datetime.now(pytz.timezone('US/Eastern'))
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)

    if market_open <= now <= market_close:
        # Market is open, fetch and cache data for 1 minute
        cache_timeout = 60
    else:
        # Market is closed, persist data until next market opening
        if now < market_open:
            # If it's before market open today, set timeout until 9:30 AM today
            next_market_open = market_open
        else:
            # If after market close, set timeout until 9:30 AM next trading day
            next_market_open = market_open + timedelta(days=1)

        # Check if the next day is a weekend, adjust to Monday
        if next_market_open.weekday() >= 5:  # Saturday (5) or Sunday (6)
            next_market_open += timedelta(days=7 - next_market_open.weekday())

        cache_timeout = (next_market_open - now).total_seconds()

    # Get all unique stock symbols in Portfolio
    symbols = Portfolio.objects.values_list('symbol', flat=True).distinct()

    # Fetch and cache stock data for each symbol
    for symbol in symbols:
        stock_data = lookup_quote(symbol)
        if stock_data:
            cache_key = f"quote_{symbol.upper()}"
            cache.set(cache_key, stock_data, timeout=cache_timeout)  # Cache based on current market status

    return "Successfully cached all stock data"






# Cache financial and profile data every 24 hours (outside market hours)
@shared_task
def cache_financial_and_profile_data():
    """Task to cache financial and profile data for all stocks in Portfolio."""
    symbols = Portfolio.objects.values_list('symbol', flat=True).distinct()

    # Fetch and cache financial and profile data for each symbol
    for symbol in symbols:
        financial_data = lookup_basic_financial(symbol)
        profile_data = lookup_profile(symbol)

        if financial_data:
            cache.set(f"basic_financial_{symbol.upper()}", financial_data, timeout=60*60*24)  # Cache for 24 hours
        if profile_data:
            cache.set(f"profile_{symbol.upper()}", profile_data, timeout=60*60*24)  # Cache for 24 hours

    return "Successfully cached financial and profile data"



@shared_task
def capture_daily_portfolio_value():
    """Task to capture and store the total portfolio value for each user at the end of each day."""
    from api.models import UserProfile

    # Get all users
    users = UserProfile.objects.all()

    for user_profile in users:
        total_value = Decimal(user_profile.cash)  # Start with user's cash

        # Get all the user's portfolio items and calculate total value
        for item in Portfolio.objects.filter(user=user_profile):
            stock_data = lookup_quote(item.symbol)
            if stock_data:
                total_value += Decimal(item.shares) * Decimal(stock_data['current_price'])

        # Store this value in PortfolioHistory
        PortfolioHistory.objects.create(user=user_profile, total_value=total_value)

    return "Portfolio values captured"