from rest_framework.serializers import ModelSerializer
from .models import User, Category, Resume, Company, Recruitment, CompanyImage, Apply, Follow, Comment


class CategorySerializer(ModelSerializer):
    class Meta:
        model = Category
        fields = ['name', 'description']


class ResumeSerializer(ModelSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['icon'] = instance.icon.url if instance.icon else ''
        return data

    class Meta:
        model = Resume
        fields = ['name', 'cv', 'user']


class CompanySerializer(ModelSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['cv'] = instance.cv.url if instance.cv else ''
        return data

    class Meta:
        model = Company
        fields = ['name', 'icon', 'code']


class CompanyImageSerializer(ModelSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['image'] = instance.image.url if instance.image else ''
        return data

    class Meta:
        model = CompanyImage
        fields = ['image']


class RecruitmentSerializer(ModelSerializer):
    class Meta:
        model = Recruitment
        fields = ['title', 'description', 'skills_required', 'salary', 'location', 'company', 'category', 'work_time_start']


class ApplySerializer(ModelSerializer):
    class Meta:
        model = Apply
        fields = ['resume', 'recruitment', 'status']


class FollowSerializer(ModelSerializer):
    class Meta:
        model = Follow
        fields = ['company', 'user']


class CommentSerializer(ModelSerializer):
    class Meta:
        model = Comment
        fields = ['content', 'user', 'company']


class UserSerializer(ModelSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['avatar'] = instance.avatar.url if instance.avatar else ''
        return data

    class Meta:
        model = User
        fields = ['email', 'phone', 'first_name', 'last_name', 'role', 'avatar']
        extra_kwargs = {
            'password': {
                'write_only': True
            }
        }

    def create(self, validated_data):
        data = validated_data.copy()
        u = User(**data)
        u.set_password(u.password)
        u.save()
        return u
