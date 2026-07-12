from django.contrib.auth import get_user_model
from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import EcoSphereTokenSerializer, RegisterSerializer, UserSerializer

User = get_user_model()


class EcoSphereTokenView(TokenObtainPairView):
    """POST username/password -> access + refresh JWT (role embedded)."""

    serializer_class = EcoSphereTokenSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveUpdateAPIView):
    """Return / update the authenticated user's own profile."""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
