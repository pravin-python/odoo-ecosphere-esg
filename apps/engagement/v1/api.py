"""Gamification APIs: challenges, badges, rewards store, leaderboard, profile."""
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.v1.permissions import CanManage

from .leaderboard import employee_leaderboard
from .models import Badge, Challenge, ChallengeParticipation, EmployeeProfile, Reward
from .services import RedemptionError, get_or_create_profile, redeem_reward


class ChallengeSerializer(serializers.ModelSerializer):
    difficulty_label = serializers.CharField(source="get_difficulty_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Challenge
        fields = ("id", "public_id", "title", "description", "xp_reward", "difficulty",
                  "difficulty_label", "start_date", "end_date", "deadline",
                  "status", "status_label", "is_active")

    def validate(self, attrs):
        start, end = attrs.get("start_date"), attrs.get("end_date")
        if start and end and end < start:
            raise serializers.ValidationError({"end_date": "End date must be on or after the start date."})
        return attrs


class ChallengeParticipationSerializer(serializers.ModelSerializer):
    challenge_title = serializers.CharField(source="challenge.title", read_only=True)
    employee_name = serializers.CharField(source="employee.get_full_name", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = ChallengeParticipation
        fields = ("id", "public_id", "challenge_title", "employee_name",
                  "progress", "status", "status_label")


class BadgeSerializer(serializers.ModelSerializer):
    tier_label = serializers.CharField(source="get_tier_display", read_only=True)

    class Meta:
        model = Badge
        fields = ("id", "public_id", "name", "description", "icon", "tier", "tier_label")


class RewardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reward
        fields = ("id", "public_id", "name", "description", "points_required",
                  "stock_count", "is_active")

    def validate_points_required(self, value):
        if value <= 0:
            raise serializers.ValidationError("Points required must be greater than zero.")
        return value


class ChallengeViewSet(viewsets.ModelViewSet):
    queryset = Challenge.objects.all()
    serializer_class = ChallengeSerializer
    permission_classes = [CanManage]
    http_method_names = ["get", "post"]


class ChallengeParticipationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ChallengeParticipation.objects.select_related("challenge", "employee").all()
    serializer_class = ChallengeParticipationSerializer


class BadgeViewSet(viewsets.ModelViewSet):
    queryset = Badge.objects.all()
    serializer_class = BadgeSerializer
    permission_classes = [CanManage]
    http_method_names = ["get", "post"]


class RewardViewSet(viewsets.ModelViewSet):
    queryset = Reward.objects.filter(is_active=True)
    serializer_class = RewardSerializer
    http_method_names = ["get", "post"]

    def get_permissions(self):
        # Creating rewards is a staff action; redeeming/listing is for everyone.
        return [CanManage()] if self.action == "create" else [IsAuthenticated()]

    @action(detail=True, methods=["post"])
    def redeem(self, request, pk=None):
        reward = self.get_object()
        try:
            redemption = redeem_reward(request.user, reward)
        except RedemptionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        profile = get_or_create_profile(request.user)
        return Response({
            "detail": f"Redeemed “{reward.name}”. {redemption.points_spent} XP deducted.",
            "xp_balance": profile.xp_balance,
        })


class LeaderboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.core.v1.rls.context import rls_admin

        limit = min(int(request.query_params.get("limit", 10)), 50)
        user = request.user
        privileged = user.is_superuser or getattr(user, "role", None) in ("ADMIN", "GOVERNANCE_OFFICER")
        # A leaderboard is a shared ranking: bypass the per-owner RLS on
        # EmployeeProfile but scope explicitly to the caller's department
        # (org-wide for admins/governance), so nothing leaks across departments.
        department = None if privileged else user.department
        with rls_admin():
            data = employee_leaderboard(limit=limit, department=department)
        return Response(data)


class MyProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = get_or_create_profile(request.user)
        return Response({
            "xp_balance": profile.xp_balance,
            "total_earned_xp": profile.total_earned_xp,
            "level": profile.level,
            "badges": [
                {"name": b.name, "tier": b.tier, "icon": b.icon}
                for b in profile.badges.all()
            ],
        })
