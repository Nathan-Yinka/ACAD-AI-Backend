"""Custom permission classes for the application."""
from rest_framework import permissions


class IsStudentOwner(permissions.BasePermission):
    """
    Permission class to ensure students can only access their own submissions.
    """
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'student'):
            return obj.student == request.user
        return False

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class IsStudent(permissions.BasePermission):
    """
    Permission class to ensure only students can perform certain actions.
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_student
        )


class IsAdmin(permissions.BasePermission):
    """
    Permission class to ensure only admins can perform certain actions.
    Admins are users where is_student=False.
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            not request.user.is_student
        )

