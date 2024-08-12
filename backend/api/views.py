from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework import generics  # module in REST framework that provides pre-built views for common tasks, like creating or listing objects.
from .serializers import UserSerializer, NoteSerializer  # the file we made
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Note


# Create your views here.


# INSTEAD OF FUNCTION-BASED VIEWS, WE ARE CREATING CLASS-BASED VIEWS
# a generic class built-into django, CreateAPIView is designed to handle POST requests to create new objects in the database.
class CreateUserView(generics.CreateAPIView):

    # these three attributes are overriden in generics.CreateAPIView

    # tells view which model we want to add to, make sure user does not already exist (handled by serializer)
    queryset = User.objects.all()
    # tells this view what serializer to use to validate incoming data and create model
    serializer_class = UserSerializer
    # specifies who can call this class, in our case anyone, even if they are not authenticated
    permission_classes = [AllowAny]




# this view does 2 things, in our case, list all the notes user has created, and create a new note
class NoteListCreate(generics.ListCreateAPIView):
    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated]  # cannot call this route unless authenticated and pass a valid JWT token

    # instead of declaring the queryset, because we want to get the authenticated user then filter
    def get_queryset(self):
        user = self.request.user # get the authenticated user
        return Note.objects.filter(author=user)

    # custom and override create method
    def perform_create(self, serializer):
        if serializer.is_valid():
            # since we specified in our serializer that author field is read-only, 
            # which means we have to explicitly pass data into it
            serializer.save(author=self.request.user)
        else:
            print(serializer.errors)





class NoteDelete(generics.DestroyAPIView):
    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated]


    # specify the valid notes that we could delete, in this case all the current user's notes
    def get_queryset(self):
        user = self.request.user
        return Note.objects.filter(author=user)