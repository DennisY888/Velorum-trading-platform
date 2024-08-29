from django.contrib.auth.models import User
from rest_framework import serializers
from .models import *
from .helpers import usd  # Import your usd helper function


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
