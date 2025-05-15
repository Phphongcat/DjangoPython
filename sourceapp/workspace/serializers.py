from rest_framework.serializers import ModelSerializer
from . import models


class CategorySerializer(ModelSerializer):
    class Meta:
        model = models.Category
        fields = ['name', 'description']


class WorkTypeSerializer(ModelSerializer):
    class Meta:
        model = models.WorkType
        fields = ['name']


class ResumeSerializer(ModelSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['icon'] = instance.icon.url if instance.icon else ''
        return data

    class Meta:
        model = models.Resume
        fields = ['name', 'cv', 'user']


class CompanyImageSerializer(ModelSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['image'] = instance.image.url if instance.image else ''
        return data

    class Meta:
        model = models.CompanyImage
        fields = ['image']


class CompanySerializer(ModelSerializer):
    images = CompanyImageSerializer(many=True, write_only=True)

    def create(self, validated_data):
        images_data = validated_data.pop('images')
        company = models.Company.objects.create(**validated_data)
        for image_data in images_data:
            models.CompanyImage.objects.create(company=company, **image_data)
        return company

    class Meta:
        model = models.Company
        fields = ['name', 'code', 'images']


class RecruitmentSerializer(ModelSerializer):
    class Meta:
        model = models.Recruitment
        fields = ['title', 'description', 'skills_required', 'salary', 'location', 'company', 'category', 'work_time_start']


class ApplySerializer(ModelSerializer):
    class Meta:
        model = models.Apply
        fields = ['resume', 'recruitment', 'status']


class FollowSerializer(ModelSerializer):
    class Meta:
        model = models.Follow
        fields = ['company', 'user']


class UserCommentSerializer(ModelSerializer):
    class Meta:
        model = models.UserComment
        fields = ['content', 'company']


class CompanyCommentSerializer(ModelSerializer):
    class Meta:
        model = models.CompanyComment
        fields = ['content', 'user']


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
        fields = ['email', 'phone', 'first_name', 'last_name', 'role', 'avatar']
        extra_kwargs = {
            'password': {
                'write_only': True
            }
        }
