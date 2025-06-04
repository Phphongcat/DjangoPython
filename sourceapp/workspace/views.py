from rest_framework import mixins, viewsets, generics, status, parsers, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.mail import send_mail
from django.db.models import Q
from datetime import datetime

from . import serializers, perms, models, paginators


class CategoryViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = models.Category.objects.filter(active=True)
    serializer_class = serializers.CategorySerializer


class WorkTypeViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = models.WorkType.objects.filter(active=True)
    serializer_class = serializers.WorkTypeSerializer


class CompanyViewSet(viewsets.ViewSet, generics.ListCreateAPIView):
    queryset = models.Company.objects.filter(active=True)
    serializer_class = serializers.CompanySerializer

    @action(methods=['get'], detail=False, url_path='owner', permission_classes=[permissions.IsAuthenticated])
    def get_companies_by_user(self, request):
        data = self.serializer_class(request.user.company).data
        return Response(data)


class RecruitmentViewSet(viewsets.ViewSet, generics.ListCreateAPIView, mixins.RetrieveModelMixin):
    queryset = models.Recruitment.objects.\
        select_related('company', 'category', 'work_type').\
        filter(active=True).\
        order_by('id')
    pagination_class = paginators.RecruitmentPaginator
    serializer_class = serializers.RecruitmentSerializer

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [perms.RecruitmentOwner()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        query = self.queryset

        com_id = self.request.query_params.get('company_id')
        if com_id:
            query = query.filter(company_id=com_id)

        cate_id = self.request.query_params.get('category_id')
        if cate_id:
            query = query.filter(category__id=cate_id)

        work_id = self.request.query_params.get('work_type_id')
        if work_id:
            query = query.filter(work_type__id=work_id)

        k = self.request.query_params.get('key')
        if k:
            query = query.filter(title__icontains=k)

        province = self.request.query_params.get('province')
        if province:
            query = query.filter(location__icontains=province)

        date = self.request.query_params.get('date_start')
        if date:
            try:
                date_obj = datetime.strptime(date, '%Y-%m-%d').date()
                query = query.filter(date_start__gte=date_obj)
            except ValueError:
                pass

        return query

    def perform_create(self, serializer):
        user = self.request.user
        followers = models.Follow.objects.select_related('user').filter(company=user.company)
        emails = [f.user.email for f in followers if f.user.email]

        if emails:
            send_mail(
                subject='Thông báo từ công ty bạn đang theo dõi',
                message=f'Công ty {user.company.name} vừa đăng tin tuyển dụng, hãy xem ngay!',
                from_email=user.email,
                recipient_list=emails,
                fail_silently=False,
            )

    @action(detail=True, methods=['patch'], url_path='change', permission_classes=[permissions.IsAuthenticated])
    def change_active(self, request, pk=None):
        recruitment = models.Recruitment.objects.get(id=pk)
        if 'active' in request.data:
            recruitment.active = request.data['active']

        recruitment.save()
        recruitment.refresh_from_db()

        return Response(serializers.RecruitmentSerializer(recruitment).data)


    @action(detail=True, methods=['get'], url_path='applied', permission_classes=[permissions.IsAuthenticated])
    def get_applied(self, request, pk=None):
        user = request.user
        applied = models.Apply.objects.filter(resume__user=user, recruitment_id=pk).exists()
        return Response({'applied': applied}, status=status.HTTP_200_OK)


class ResumeViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin,
    mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet
):
    queryset = models.Resume.objects.select_related('user').filter(active=True).order_by('id')
    serializer_class = serializers.ResumeSerializer
    pagination_class = paginators.ResumePaginator

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
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

    @action(detail=False, methods=['get'], url_path='owner', permission_classes=[permissions.IsAuthenticated])
    def get_recruitment(self, request):
        resumes = self.queryset.filter(user=request.user)
        page = self.paginate_queryset(resumes)

        if page:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(resumes, many=True)
        return Response(serializer.data)


class ApplyViewSet(viewsets.ViewSet, generics.ListCreateAPIView):
    queryset = models.Apply.objects.filter(active=True)
    serializer_class = serializers.ApplySerializer
    pagination_class = paginators.ApplyPagination
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['patch'], url_path="change")
    def patch_status(self, request, pk=None):
        apply = models.Apply.objects.select_related('resume__user').get(id=pk)
        if 'status' in request.data:
            apply.status = request.data['status']

        apply.save()
        apply.refresh_from_db()

        return Response(serializers.ApplySerializer(apply).data)

    @action(detail=False, methods=['get'], url_path='candidate/(?P<pk>[^/.]+)')
    def get_by_recruitment(self, request, pk=None):
        applies = models.Apply.objects.select_related('resume__user') \
            .filter(active=True, recruitment_id=pk).order_by('-status')

        page = self.paginate_queryset(applies)
        if page:
            response = self.get_serializer(page, many=True).data
            for i, apply in enumerate(page):
                user = apply.resume.user
                response[i]['user_id'] = user.id
                response[i]['user_name'] = f"{user.first_name} {user.last_name}".strip()
                response[i]['user_email'] = user.email
                response[i]['user_avatar'] = user.avatar.url if user.avatar and hasattr(user.avatar, 'url') else ''
                response[i]['resume_detail'] = serializers.ResumeSerializer(apply.resume).data

            return self.get_paginated_response(response)
        return self.get_paginated_response(serializers.ApplySerializer(applies, many=True).data)

    @action(detail=False, methods=['get'], url_path='employee/(?P<pk>[^/.]+)')
    def get_by_company(self, request, pk=None):
        applies = models.Apply.objects.select_related('resume__user', 'recruitment__company') \
            .filter(active=True, recruitment__company_id=pk, status=4) \
            .order_by('id')

        page = self.paginate_queryset(applies)
        if page:
            response = self.get_serializer(page, many=True).data
            for i, apply in enumerate(page):
                user = apply.resume.user
                response[i]['user_id'] = user.id
                response[i]['user_name'] = f"{user.first_name} {user.last_name}".strip()
                response[i]['user_avatar'] = user.avatar.url if user.avatar and hasattr(user.avatar, 'url') else ''
                response[i]['work'] = apply.recruitment.title

            return self.get_paginated_response(response)
        return self.get_paginated_response(serializers.ApplySerializer(applies, many=True).data)

    @action(detail=False, methods=['get'], url_path='mine')
    def get_by_i(self, request):
        applies = models.Apply.objects.select_related('resume__user', 'recruitment__company') \
            .filter(active=True, resume__user_id=request.user.id) \
            .filter(Q(status=4) | Q(recruitment__active=True)) \
            .order_by('status')

        page = self.paginate_queryset(applies)
        if page:
            response = self.get_serializer(page, many=True).data
            for i, apply in enumerate(page):
                recruitment = apply.recruitment
                response[i]['work'] = recruitment.title
                response[i]['company_id'] = recruitment.company.id
                response[i]['company_name'] = recruitment.company.name

            return self.get_paginated_response(response)
        return self.get_paginated_response(serializers.ApplySerializer(applies, many=True).data)


class UserCommentViewSet(viewsets.ViewSet, generics.ListCreateAPIView):
    queryset = models.UserComment.objects.filter(active=True)
    serializer_class = serializers.UserCommentSerializer
    pagination_class = paginators.CommentPaginator

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH']:
            return [perms.Owner()]
        return [permissions.IsAuthenticated()]

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

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH']:
            return [perms.Owner()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        query = self.queryset
        company_id = self.request.query_params.get('company_id')

        if company_id:
            query = query.filter(company__id=company_id)

        return query


class FollowViewSet(viewsets.ViewSet, mixins.DestroyModelMixin, generics.ListCreateAPIView):
    queryset = models.Follow.objects.filter(active=True)
    serializer_class = serializers.FollowSerializer

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [perms.Owner()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        return self.queryset.filter(user_id=user.id)


class UserViewSet(viewsets.ViewSet, generics.CreateAPIView):
    queryset = models.User.objects.filter(is_active=True)
    serializer_class = serializers.UserSerializer
    parser_classes = [parsers.MultiPartParser]

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH']:
            return [perms.Self()]
        return [permissions.AllowAny()]

    @action(methods=['get', 'patch'], url_path="current-user", detail=False, permission_classes=[permissions.IsAuthenticated])
    def current_user(self, request):
        user = request.user

        if request.method == 'PATCH':
            if 'avatar' in request.FILES:
                user.avatar = request.FILES['avatar']
            for key, value in request.data.items():
                if key in ['email', 'phone', 'role']:
                    setattr(user, key, value)
            user.save()
            user.refresh_from_db()

        response = serializers.UserSerializer(user).data
        response['supply'] = bool(user.email and user.avatar and user.phone)

        if user.is_employer():
            if hasattr(user, 'company'):
                response['has_company'] = True
                response['verified'] = user.company.verified
            else:
                response['has_company'] = False
                response['verified'] = False
        else:
            response['verified'] = user.resumes.exists()

        return Response(response)


class SendMailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        email = request.data.get('email')
        subject = request.data.get('subject')
        message = request.data.get('message')

        if not all([email, subject, message]):
            return Response({'detail': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=request.user.email,
                recipient_list=[email],
                fail_silently=False,
            )
            return Response({'detail': 'Email sent successfully'}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'detail': f'Failed to send email: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
