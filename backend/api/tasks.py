# backend/api/tasks.py

from celery import shared_task
from celery.schedules import crontab
from django.core.cache import cache
from .helpers import lookup_quote, lookup_basic_financial, lookup_profile
from api.models import Portfolio, PortfolioHistory, UserProfile
from decimal import Decimal
import pytz
from datetime import datetime

# --- WEBSOCKET IMPORTS ---
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@shared_task
def cache_all_stocks():
    """
    Fetches real-time data AND pushes it to WebSockets.
    Resume Claim: 'live market updates'
    """
    # 1. Get all symbols users currently own
    symbols = Portfolio.objects.values_list('symbol', flat=True).distinct()
    
    # 2. Get the Channel Layer (The Pipe)
    channel_layer = get_channel_layer()

    for symbol in symbols:
        # This function now uses the Market-Aware TTL from helpers.py
        stock_data = lookup_quote(symbol)
        
        if stock_data:
            # 3. PUSH DATA TO WEBSOCKET GROUP
            # Group name must match consumers.py: f"stock_{self.symbol}"
            group_name = f"stock_{symbol.upper()}"
            
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'stock_update', # Must match method name in StockConsumer
                    'price': stock_data['current_price']
                }
            )

    return "Cached and Broadcasted Stock Data"

# Keep existing tasks
@shared_task
def cache_financial_and_profile_data():
    symbols = Portfolio.objects.values_list('symbol', flat=True).distinct()
    for symbol in symbols:
        lookup_basic_financial(symbol)
        lookup_profile(symbol)
    return "Cached financial/profile data"

@shared_task
def capture_daily_portfolio_value():
    users = UserProfile.objects.all()
    for user_profile in users:
        total_value = Decimal(user_profile.cash)
        for item in Portfolio.objects.filter(user=user_profile):
            stock_data = lookup_quote(item.symbol)
            if stock_data:
                total_value += Decimal(item.shares) * Decimal(stock_data['current_price'])
        PortfolioHistory.objects.create(user=user_profile, total_value=total_value)
    return "Portfolio values captured"