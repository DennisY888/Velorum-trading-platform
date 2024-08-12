from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Note



class UserSerializer(serializers.ModelSerializer):
    # meta class is special inner class in python that provides additional information, Django uses it for models, serializers, and forms
    class Meta:
        model = User
        # fields we need when we take in and return a new user
        fields = ["id", "username", "password"]
        # tells django we want to accept password but not return password when we are giving information about a user
        extra_kwargs = {"password": {"write_only": True}}
    

    # serializer automatically checks user inputted credentials
    # once credential data validated it passes to this function and we create a new user
    def create(self, validated_data):
        print(validated_data)
        # ** splits up keys from a dictionary to pass in separately
        user = User.objects.create_user(**validated_data)
        return user
    



class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ["id", "title", "content", "created_at", "author"]
        extra_kwargs = {"author": {"read_only": True}}
