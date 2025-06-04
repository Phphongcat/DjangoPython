from rest_framework.serializers import ModelSerializer, ValidationError, CharField
from . import models


class CategorySerializer(ModelSerializer):
    class Meta:
        model = models.Category
        fields = ['id', 'name', 'description']


class WorkTypeSerializer(ModelSerializer):
    class Meta:
        model = models.WorkType
        fields = ['id', 'name']


class ResumeSerializer(ModelSerializer):
    def create(self, validated_data):
        user = self.context['request'].user
        resume = models.Resume.objects.create(user=user, **validated_data)
        return resume

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['cv'] = instance.cv.url if instance.cv else ''
        return data

    def validate(self, attrs):
        user = self.context['request'].user
        name = attrs.get('name')
        if self.instance is None:
            if models.Resume.objects.filter(name=name, user=user).exists():
                raise ValidationError({'info': 'Tên hồ sơ không được trùng lặp.'})
        return attrs

    class Meta:
        model = models.Resume
        fields = ['id', 'name', 'cv']


class CompanyImageSerializer(ModelSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['image'] = instance.image.url if instance.image else ''
        return data

    class Meta:
        model = models.CompanyImage
        fields = ['image']


class CompanySerializer(ModelSerializer):
    images = CompanyImageSerializer(many=True, read_only=True)

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user
        company = models.Company.objects.create(user=user, **validated_data)

        image_files = [
            file for key, file in request.FILES.items()
            if key.startswith('images')
        ]

        for image in image_files:
            models.CompanyImage.objects.create(company=company, image=image)

        return company

    class Meta:
        model = models.Company
        fields = ['id', 'name', 'code', 'verified', 'images']


class RecruitmentSerializer(ModelSerializer):
    company_name = CharField(source='company.name', read_only=True)
    category_name = CharField(source='category.name', read_only=True)
    work_type_name = CharField(source='work_type.name', read_only=True)

    class Meta:
        model = models.Recruitment
        fields = ['id', 'title', 'description', 'salary', 'company_name',
                  'category_name', 'work_type_name', 'location', 'company',
                  'category', 'work_type', 'date_start']


class ApplySerializer(ModelSerializer):
    class Meta:
        model = models.Apply
        fields = ['id', 'resume', 'recruitment', 'status', 'created_date']


class FollowSerializer(ModelSerializer):
    company_name = CharField(source='company.name', read_only=True)

    def create(self, validated_data):
        request = self.context.get('request')
        return models.Follow.objects.create(user=request.user, **validated_data)

    class Meta:
        model = models.Follow
        fields = ['id', 'company', 'company_name']


class UserSerializer(ModelSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['avatar'] = instance.avatar.url if instance.avatar else ''
        return data

    def create(self, validated_data):
        data = validated_data.copy()
        u = models.User(**data)
        u.set_password(u.password)
        u.save()
        return u

    class Meta:
        model = models.User
        fields = ['id', 'email', 'phone', 'first_name', 'last_name', 'role', 'avatar']
        extra_kwargs = {
            'password': {
                'write_only': True
            }
        }


class CompanyCommentSerializer(ModelSerializer):
    user = UserSerializer(read_only=True)

    def create(self, validated_data):
        request = self.context.get('request')
        return models.CompanyComment.objects.create(user=request.user, **validated_data)

    class Meta:
        model = models.CompanyComment
        fields = ['id', 'content', 'user', 'company', 'created_date']


class UserCommentSerializer(ModelSerializer):
    company_name = CharField(source='company.name', read_only=True)

    class Meta:
        model = models.UserComment
        fields = ['id', 'content', 'user', 'company', 'created_date', 'company_name']
