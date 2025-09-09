from django.shortcuts import render
from .serializers import TerratracUserSerializer, ForestAreaSerializer, NDVIRecordSerializer, AlertSerializer, CommunityReportSerializer, VerificationSerializer
from .models import TerratracUser, ForestArea, NDVIRecord, Alert, CommunityReport, Verification
from django.contrib.auth import authenticate
from django_filters import rest_framework as filters
from rest_framework import viewsets, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model

# Create your views here.
class RegisterUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TerratracUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': TerratracUserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class LoginUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': TerratracUserSerializer(user).data
            }, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid Credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class LogoutUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.auth.delete()
        request.session.pop('token', None)
        return Response(status=status.HTTP_204_NO_CONTENT, data={'message': 'Logged out successfully'})
    
class TerratracUserViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = TerratracUserSerializer
    queryset = TerratracUser.objects.all()

    def get(self,request):
        if request.user.is_staff:
            return TerratracUser.objects.all()
        return TerratracUser.objects.filter(id=request.user.id)
    
    def update(self, request):
        user = self.get_object()
        if request.user != user and not request.user.is_staff:
            return Response({'error': 'You do not have permission to update this user.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response({'error': "data is not correct"}, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request):
        user = self.get_object()
        if request.user != user and not request.user.is_staff:
            return Response({'error': 'You do not have permission to delete this user.'}, status=status.HTTP_403_FORBIDDEN)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class ForestAreaViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = ForestAreaSerializer
    queryset = ForestArea.objects.all()
    filter_backends = [filters.DjangoFilterBackend]
    filterset_fields = ['name', 'latitude', 'longitude', 'last_ndvi']

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def perform_create(self, serializer):
        if not self.request.user.is_staff:
            raise PermissionError("Only staff users can create Forest Areas.")
        serializer.save()

    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated])
    def perform_update(self, serializer):
        if not self.request.user.is_staff:
            raise PermissionError("Only staff users can update Forest Areas.")
        serializer.save()

    def get_queryset(self):
        return super().get_queryset()
    

class AlertViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = AlertSerializer
    queryset = Alert.objects.all()
    filter_backends = [filters.DjangoFilterBackend]
    filterset_fields = ['forest_area__name', 'alert_type', 'status', 'triggered_on']

    def get_queryset(self):
        return super().get_queryset()
    
    def verify(self, request, pk=None):
        alert = self.get_object()
        if alert.status != 'Pending':
            return Response({'error': 'Alert has already been verified or rejected.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = VerificationSerializer(data=request.data)
        if serializer.is_valid():
            verification = serializer.save(alert=alert, verified_by=request.user)
            perform_verify(verification)
            return Response(VerificationSerializer(verification).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def reject(self, request, pk=None):
        alert = self.get_object()
        if alert.status != 'Pending':
            return Response({'error': 'Alert has already been verified or rejected.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = VerificationSerializer(data=request.data)
        if serializer.is_valid():
            verification = serializer.save(alert=alert, verified_by=request.user, verified=False)
            perform_verify(verification)
            return Response(VerificationSerializer(verification).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)