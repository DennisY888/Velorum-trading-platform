# backend/api/views.py

from django.shortcuts import render
from django.contrib.auth.models import User
from .serializers import *
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import *
from rest_framework import generics, viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .helpers import lookup_quote, lookup_basic_financial, lookup_profile, usd
from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.pagination import LimitOffsetPagination
import random

# --- CONCURRENCY IMPORT ---
from django.db import transaction

# Creates a new User entry
class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_stock_quote(request, symbol):
    quote_data = lookup_quote(symbol)
    financial_data = lookup_basic_financial(symbol)
    profile_data = lookup_profile(symbol)

    if quote_data and financial_data and profile_data:
        # Combine all data
        data = quote_data.copy()
        data.update(financial_data)
        data.update(profile_data)
        return Response(data, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'Could not retrieve stock data'}, status=status.HTTP_400_BAD_REQUEST)

class PortfolioHistoryView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user_profile = request.user.userprofile
        history = PortfolioHistory.objects.filter(user=user_profile).order_by('date')
        serializer = PortfolioHistorySerializer(history, many=True)
        return Response(serializer.data, status=200)

class PortfolioBreakdownView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user_profile = request.user.userprofile
        portfolio = Portfolio.objects.filter(user=user_profile)
        total_stock_value = Decimal(0)
        portfolio_data = []
        colors = []
        
        for item in portfolio:
            stock_data = lookup_quote(item.symbol)
            if stock_data:
                current_price = Decimal(stock_data['current_price'])
                stock_value = current_price * item.shares
                total_stock_value += stock_value
                
                color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
                while color in colors:
                    color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
                colors.append(color)
                
                portfolio_data.append({
                    'symbol': item.symbol,
                    'shares': item.shares,
                    'current_value': stock_value,
                    'color': color,
                })
        
        total_value_with_cash = total_stock_value + user_profile.cash
        for stock in portfolio_data:
            stock['percent'] = round((stock['current_value'] / total_value_with_cash) * 100, 2)

        cash_color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
        cash_percent = round((user_profile.cash / total_value_with_cash) * 100, 2)

        return Response({
            'portfolio': portfolio_data,
            'cash': {
                'value': user_profile.cash,
                'percent': cash_percent,
                'color': cash_color
            },
        }, status=200)

class PortfolioViewSet(viewsets.ModelViewSet):
    queryset = Portfolio.objects.all()
    serializer_class = PortfolioSerializer
    permission_classes = [IsAuthenticated]

    # --- RESUME CLAIM: HIGH CONCURRENCY / ATOMIC TRANSACTIONS ---
    @action(detail=False, methods=['post'])
    def buy(self, request):
        symbol = request.data.get('symbol')
        try:
            shares = int(request.data.get('shares'))
        except (ValueError, TypeError):
             return Response({'error': 'Invalid shares'}, status=status.HTTP_400_BAD_REQUEST)

        if not symbol or shares <= 0:
            return Response({'error': 'Invalid symbol or shares'}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Start Atomic Block
        with transaction.atomic():
            # 2. Lock the User Profile Row (Prevents race conditions on balance)
            user_profile = UserProfile.objects.select_for_update().get(user=request.user)
            
            stock_data = lookup_quote(symbol)
            if not stock_data:
                return Response({'error': 'Stock symbol not found'}, status=status.HTTP_400_BAD_REQUEST)
            
            profile_data = lookup_profile(symbol)
            total_cost = Decimal(str(stock_data['current_price'])) * Decimal(shares)

            if user_profile.cash < total_cost:
                return Response({'error': 'Insufficient funds'}, status=status.HTTP_400_BAD_REQUEST)

            # 3. Deduct Balance
            user_profile.cash -= total_cost
            user_profile.save()

            # 4. Lock/Get Portfolio Row
            portfolio_item, created = Portfolio.objects.select_for_update().get_or_create(
                user=user_profile,
                symbol=symbol
            )
            portfolio_item.shares += shares
            portfolio_item.save()

            # 5. Record History
            History.objects.create(
                user=user_profile,
                symbol=symbol,
                shares=shares,
                method='buy',
                price=stock_data['current_price'],
                name=profile_data.get('name', 'N/A'),
                new_cash=user_profile.cash,
                total_value=total_cost
            )

        return Response({'message': 'Stock purchased successfully'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def sell(self, request):
        symbol = request.data.get('symbol')
        try:
            shares = int(request.data.get('shares'))
        except (ValueError, TypeError):
             return Response({'error': 'Invalid shares'}, status=status.HTTP_400_BAD_REQUEST)

        if not symbol or shares <= 0:
            return Response({'error': 'Invalid symbol or shares'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            user_profile = UserProfile.objects.select_for_update().get(user=request.user)
            
            # Lock Portfolio Row
            portfolio_item = get_object_or_404(Portfolio.objects.select_for_update(), user=user_profile, symbol=symbol)

            if portfolio_item.shares < shares:
                return Response({'error': 'Not enough shares to sell'}, status=status.HTTP_400_BAD_REQUEST)

            stock_data = lookup_quote(symbol)
            profile_data = lookup_profile(symbol)

            if not stock_data:
                 return Response({'error': 'Stock data unavailable'}, status=status.HTTP_400_BAD_REQUEST)

            portfolio_item.shares -= shares
            if portfolio_item.shares == 0:
                portfolio_item.delete()
            else:
                portfolio_item.save()

            total_earnings = Decimal(str(stock_data['current_price'])) * Decimal(shares)
            user_profile.cash += total_earnings
            user_profile.save()

            History.objects.create(
                user=user_profile,
                symbol=symbol,
                shares=shares,
                method='sell',
                price=stock_data['current_price'],
                name=profile_data.get('name', 'N/A'),
                new_cash=user_profile.cash,
                total_value=total_earnings
            )

        return Response({'message': 'Stock sold successfully'}, status=status.HTTP_200_OK)

class OwnedStockSearchView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        query = request.query_params.get('q', '').upper()
        user_profile = UserProfile.objects.select_related('user').get(user=request.user)
        if query:
            owned_stocks = Portfolio.objects.filter(
                user=user_profile,
                symbol__icontains=query
            )
            data = [lookup_profile(stock.symbol) for stock in owned_stocks]
            return Response(data, status=status.HTTP_200_OK)
        return Response({"error": "Query parameter 'q' is missing"}, status=status.HTTP_400_BAD_REQUEST)

class HistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = History.objects.all()
    serializer_class = HistorySerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def my_history(self, request):
        user_profile = UserProfile.objects.select_related('user').get(user=request.user)
        # N+1 Query Optimization: select_related/prefetch if needed, but history is flat here
        history = self.queryset.filter(user=user_profile).order_by('-transacted')
        paginator = LimitOffsetPagination()
        paginated_history = paginator.paginate_queryset(history, request)
        response_data = [
            {
                'id': transaction.id,
                'symbol': transaction.symbol,
                'name': transaction.name,
                'shares': transaction.shares,
                'method': transaction.method,
                'price': usd(transaction.price),
                'total_value': usd(transaction.total_value),
                'transacted': transaction.transacted,
                'new_cash': usd(transaction.new_cash)
            }
            for transaction in paginated_history
        ]
        return paginator.get_paginated_response(response_data)

class LeaderboardView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        # Optimization: Prefetch portfolios to avoid N+1
        queryset = UserProfile.objects.prefetch_related('portfolios').all()
        user_data = []
        for user_profile in queryset:
            total_stock_value = Decimal(0)
            for portfolio in user_profile.portfolios.all():
                stock_data = lookup_quote(portfolio.symbol)
                if stock_data:
                    total_stock_value += portfolio.shares * Decimal(stock_data['current_price'])
            total_value = user_profile.cash + total_stock_value
            user_data.append({
                'user_profile': user_profile,
                'total_value': total_value
            })
        sorted_data = sorted(user_data, key=lambda x: x['total_value'], reverse=True)
        for index, data in enumerate(sorted_data):
            data['ranking'] = index + 1
        return sorted_data

    def list(self, request, *args, **kwargs):
        query = request.query_params.get('q', '')
        if query:
            sorted_data = self.get_queryset()
            filtered_data = [data for data in sorted_data if query.lower() in data['user_profile'].user.username.lower()]
            response_data = [{'user': data['user_profile'].user.username, 'total_value': usd(data['total_value']), 'ranking': data['ranking']} for data in filtered_data]
        else:
            sorted_data = self.get_queryset()[:10]
            response_data = [{'user': data['user_profile'].user.username, 'cash': usd(data['user_profile'].cash), 'total_value': usd(data['total_value']), 'ranking': data['ranking']} for data in sorted_data]
        return Response(response_data)

class IndexView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        user_profile = UserProfile.objects.select_related('user').get(user=request.user)
        portfolio = Portfolio.objects.filter(user=user_profile)
        portfolio_data = []
        total_value = Decimal(0)
        for item in portfolio:
            stock_data = lookup_quote(item.symbol)
            if stock_data:
                current_price = Decimal(stock_data['current_price'])
                prev_close = Decimal(stock_data['previous_close'])
                percent_change = Decimal((current_price - prev_close) / prev_close) * 100 if prev_close else 0
                item_value = current_price * item.shares
                total_value += item_value
                portfolio_data.append({
                    'symbol': item.symbol,
                    'shares': item.shares,
                    'current_price': current_price,
                    'total_value': item_value,
                    'daily_change': percent_change,
                })
        current_cash = user_profile.cash
        grand_total = current_cash + total_value
        return Response({
            'username': request.user.username,
            'portfolio': portfolio_data,
            'cash': current_cash,
            'grand_total': grand_total,
        })

class WatchlistViewSet(viewsets.ModelViewSet):
    queryset = Watchlist.objects.all()
    serializer_class = WatchlistSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        user_profile = UserProfile.objects.select_related('user').get(user=self.request.user)
        return Watchlist.objects.filter(user=user_profile)
    @action(detail=False, methods=['get'])
    def my_watchlist(self, request):
        user_profile = UserProfile.objects.select_related('user').get(user=request.user)
        watchlist = self.get_queryset().order_by('-id')
        paginator = LimitOffsetPagination()
        paginated_watchlist = paginator.paginate_queryset(watchlist, request)
        paginated_watchlist_data = []
        for item in paginated_watchlist:
            stock_data = lookup_quote(item.symbol)
            profile_data = lookup_profile(item.symbol)
            if stock_data:
                current_price = Decimal(stock_data.get('current_price', 0))
                prev_close = Decimal(stock_data.get('previous_close', 0))
                percent_change = Decimal((current_price - prev_close) / prev_close) * 100 if prev_close else 0
                paginated_watchlist_data.append({
                    'symbol': item.symbol,
                    'name': profile_data.get('name', 'N/A') if profile_data else 'N/A',
                    'current_price': current_price,
                    'daily_change': percent_change,
                })
        return paginator.get_paginated_response(paginated_watchlist_data)

    @action(detail=False, methods=['post'])
    def add_to_watchlist(self, request):
        symbol = request.data.get('symbol')
        user_profile = UserProfile.objects.select_related('user').get(user=request.user)
        if Watchlist.objects.filter(user=user_profile, symbol=symbol).exists():
             return Response({'error': 'Stock is already in watchlist'}, status=status.HTTP_400_BAD_REQUEST)
        watchlist_item = Watchlist.objects.create(user=user_profile, symbol=symbol)
        return Response({'message': 'Stock added to watchlist', 'watchlist_item': WatchlistSerializer(watchlist_item).data}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['delete'])
    def remove_from_watchlist(self, request):
        symbol = request.data.get('symbol')
        user_profile = UserProfile.objects.select_related('user').get(user=request.user)
        watchlist_item = Watchlist.objects.filter(user=user_profile, symbol=symbol).first()
        if not watchlist_item:
            return Response({'error': 'Stock not found in watchlist'}, status=status.HTTP_404_NOT_FOUND)
        watchlist_item.delete()
        return Response({'message': 'Stock removed from watchlist'}, status=status.HTTP_200_OK)