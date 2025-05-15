from rest_framework import viewsets, generics, status, parsers, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from . import serializers, perms, models, paginators


class CategoryViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = models.Category.objects.filter(active=True)
    serializer_class = serializers.CategorySerializer


class WorkTypeViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = models.WorkType.objects.filter(active=True)
    serializer_class = serializers.WorkTypeSerializer


class CompanyViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = models.Company.objects.filter(active=True)
    serializer_class = serializers.CompanySerializer
    pagination_class = paginators.CompanyPaginator

    @action(methods=['get'], detail=True, url_path='images')
    def get_images(self, request):
        images = self.get_object().images.filter(active=True)
        return Response(serializers.CompanyImageSerializer(images, many=True).data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=True, url_path='recruitments')
    def get_recruitments(self, request):
        recruitments = self.get_object().recruitments.filter(active=True)
        return Response(serializers.RecruitmentSerializer(recruitments, many=True).data, status=status.HTTP_200_OK)


class RecruitmentViewSet(viewsets.ViewSet, generics.ListCreateAPIView):
    queryset = models.Recruitment.objects.filter(active=True)
    serializer_class = serializers.RecruitmentSerializer
    pagination_class = paginators.RecruitmentPaginator

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT']:
            return [perms.RecruitmentOwner()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        query = self.queryset

        q = self.request.query_params.get('q')
        if q:
            query = query.filter(title__icontains=q)

        cate_id = self.request.query_params.get('category_id')
        if cate_id:
            query = query.filter(category__id=cate_id)

        return query

    @action(methods=['get'], detail=False, url_path='applies', permission_classes=[permissions.IsAuthenticated])
    def get_recruitments_with_status(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        applications = models.Apply.objects.filter(
            resume__user_id=user_id,
            active=True
        ).select_related('recruitment')

        data = [
            {
                'recruitment': serializers.RecruitmentSerializer(app.recruitment).data,
                'status': app.status
            }
            for app in applications
        ]

        return Response(data, status=status.HTTP_200_OK)


class ResumeViewSet(viewsets.ViewSet, generics.ListCreateAPIView):
    queryset = models.User.objects.filter(is_active=True)
    serializer_class = serializers.ResumeSerializer
    pagination_class = paginators.ResumePaginator

    def get_permissions(self):
        if self.request.method in ['POST', 'PATCH']:
            return [perms.Owner()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        query = self.queryset

        user_id = self.request.query_params.get('user_id')
        if user_id:
            query = query.filter(user__id=user_id)

        recruitment_id = self.request.query_params.get('recruitment_id')
        if recruitment_id:
            query = query.filter(apply__recruitment_id=recruitment_id)

        return query


class ApplyViewSet(viewsets.ViewSet, generics.ListCreateAPIView):
    queryset = models.Apply.objects.filter(active=True)
    serializer_class = serializers.ApplySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        query = self.queryset

        recruitment_id = self.request.query_params.get('recruitment_id')
        if recruitment_id:
            query = query.filter(recruitment_id=recruitment_id).select_related('resume__user')

        return query


class UserCommentViewSet(viewsets.ViewSet, generics.ListCreateAPIView):
    queryset = models.UserComment.objects.filter(active=True)
    serializer_class = serializers.UserCommentSerializer
    pagination_class = paginators.CommentPaginator
    permission_classes = perms.OtherOnlyRead

    def get_queryset(self):
        query = self.queryset
        user_id = self.request.query_params.get('user_id')

        if user_id:
            query = query.filter(user__id=user_id)

        return query


class CompanyCommentViewSet(viewsets.ViewSet, generics.ListCreateAPIView):
    queryset = models.CompanyComment.objects.filter(active=True)
    serializer_class = serializers.CompanyCommentSerializer
    pagination_class = paginators.CommentPaginator
    permission_classes = perms.OtherOnlyRead

    def get_queryset(self):
        query = self.queryset
        company_id = self.request.query_params.get('company_id')

        if company_id:
            query = query.filter(company__id=company_id)

        return query


class FollowViewSet(viewsets.ViewSet, generics.ListCreateAPIView):
    queryset = models.Follow.objects.filter(active=True)
    serializer_class = serializers.FollowSerializer
    permission_classes = perms.OtherOnlyRead

    @action(methods=['get'], detail=False, url_path='companies', permission_classes=[permissions.IsAuthenticated])
    def get_followed_companies(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        follows = self.get_queryset().filter(user_id=user_id).select_related('company')
        data = serializers.CompanySerializer([follow.company for follow in follows], many=True).data
        return Response(data, status=status.HTTP_200_OK)


class UserViewSet(viewsets.ViewSet, generics.CreateAPIView):
    queryset = models.User.objects.filter(is_active=True)
    serializer_class = serializers.UserSerializer
    parser_classes = [parsers.MultiPartParser]

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH']:
            return [perms.Owner()]
        return [permissions.AllowAny()]

    @action(methods=['get', 'patch'], url_path="current-user", detail=False, permission_classes=[permissions.IsAuthenticated])
    def current_user(self, request):
        user = request.user

        if request.method == 'PATCH':
            try:
                if 'avatar' in request.FILES:
                    user.avatar = request.FILES['avatar']
                for key, value in request.data.items():
                    if key in ['phone', 'role']:
                        setattr(user, key, value)
                user.save()
            except Exception as e:
                return Response({'detail': 'Server error: ' + str(e)}, status=500)

        response = serializers.UserSerializer(user).data
        response['supply'] = bool(user.avatar and user.phone)

        if user.is_employer():
            response['has_company'] = models.Company.objects.filter(owner=user).exists()
            response['verified'] = models.Company.objects.filter(owner=user, verified=True).exists()
        else:
            response['verified'] = True

        return Response(response)