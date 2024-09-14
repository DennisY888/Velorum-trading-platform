from django.contrib.auth.models import User
from rest_framework import serializers
from .models import *
from .helpers import *  # Import your usd helper function
import random


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user



class UserProfileSerializer(serializers.ModelSerializer):
    # Modify the 'cash' field to apply the 'usd' filter
    cash = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['user', 'cash']
        extra_kwargs = {
            'user': {'read_only': True},
        }

    def get_cash(self, obj):
        return usd(obj.cash)



class PortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portfolio
        fields = ['id', 'symbol', 'shares', 'user']
        extra_kwargs = {
            'user': {'read_only': True},
        }


class HistorySerializer(serializers.ModelSerializer):
    # Modify the 'price' field to apply the 'usd' filter
    price = serializers.SerializerMethodField()

    class Meta:
        model = History
        fields = ['id', 'symbol', 'shares', 'method', 'price', 'transacted', 'user']
        extra_kwargs = {
            'user': {'read_only': True},
            'symbol': {'read_only': True},
            'transacted': {'read_only': True},
        }

    def get_price(self, obj):
        return usd(obj.price)


class WatchlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Watchlist
        fields = ['user', 'symbol']




# Serializer to return PortfolioHistory for the line chart
class PortfolioHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioHistory
        fields = ['date', 'total_value']


# Serializer for stock performance breakdown (pie chart)
class PortfolioBreakdownSerializer(serializers.ModelSerializer):
    symbol = serializers.CharField()
    shares = serializers.IntegerField()
    current_value = serializers.SerializerMethodField()
    percent = serializers.SerializerMethodField()  # New field for percentage
    color = serializers.SerializerMethodField()  # New field for color

    class Meta:
        model = Portfolio
        fields = ['symbol', 'shares', 'current_value', 'percent', 'color']

    def get_current_value(self, obj):
        stock_data = lookup_quote(obj.symbol)
        return round(Decimal(obj.shares) * Decimal(stock_data['current_price']), 2) if stock_data else 0

    def get_percent(self, obj):
        # Assuming that the view will pass `total_value_with_cash` in the context
        total_value_with_cash = self.context.get('total_value_with_cash', 1)  # Avoid division by zero
        stock_value = self.get_current_value(obj)
        return round((stock_value / total_value_with_cash) * 100, 2)

    def get_color(self, obj):
        # Generate a random color for each stock
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))