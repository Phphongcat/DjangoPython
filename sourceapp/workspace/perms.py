from rest_framework import permissions


class Self(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return super().has_object_permission(request, view, obj) and request.user == obj


class Owner(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return super().has_object_permission(request, view, obj) and request.user == obj.user


class RecruitmentOwner(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return super().has_object_permission(request, view, obj) and request.user == obj.company.user