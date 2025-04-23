from rest_framework import permissions
from .models import Company


class Owner(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return super().has_object_permission(request, view, obj) and request.user == obj


class OtherOnlyRead(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return super().has_object_permission(request, view, obj) and request.user == obj.user


class RecruitmentOwner(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if super().has_object_permission(request, view, obj) is False:
            return False

        if request.user.is_employer() is False:
            return False

        company_id = request.data.get('company')
        try:
            company = Company.objects.get(id=company_id, user=request.user)
            return company.verified
        except Company.DoesNotExist:
            return False