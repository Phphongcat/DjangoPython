from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views


router = DefaultRouter()
router.register('categories', views.CategoryViewSet, basename='category')
router.register(r'resumes', views.ResumeViewSet, basename='resume')
router.register('applies', views.ApplyViewSet, basename='apply')
router.register('follows', views.FollowViewSet, basename='follow')
router.register(r'companies', views.CompanyViewSet, basename='company')
router.register('comments', views.CommentViewSet, basename='comment')
router.register(r'recruitments', views.RecruitmentViewSet, basename='recruitment')
router.register('users', views.UserViewSet, basename='user')
urlpatterns = [
    path('', include(router.urls)),
]