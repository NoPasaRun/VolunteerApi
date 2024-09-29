from rest_framework.permissions import BasePermission


class VolunteerPermission(BasePermission):
    def has_permission(self, request, view):
        return bool(request.volunteer)
