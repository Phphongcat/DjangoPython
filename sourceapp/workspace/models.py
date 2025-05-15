from cloudinary.models import CloudinaryField
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        (0, 'Default'),
        (1, 'Employer'),
    ]

    role = models.IntegerField(choices=ROLE_CHOICES, default=0)
    phone = models.CharField(max_length=15, null=True, blank=True)
    avatar = CloudinaryField(null=True, blank=True)

    def __str__(self):
        return self.username

    def is_employer(self):
        return self.role == 1

    def full_name(self):
        return "%s %s" % (self.first_name, self.last_name)


class ModelBase(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class Category(ModelBase):
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class WorkType(ModelBase):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Company(ModelBase):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20, unique=True)
    verified = models.BooleanField(default=False)

    # relationship
    user = models.ForeignKey(User, related_name="companies", on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class CompanyImage(ModelBase):
    image = CloudinaryField(null=True, blank=True)

    # foreignKey
    company = models.ForeignKey(Company, related_name="images", on_delete=models.CASCADE)

    def __str__(self):
        return f"Image of {self.company.name}"


class Resume(ModelBase):
    name = models.CharField(max_length=255)
    cv = CloudinaryField(null=True, blank=True)

    # relationship
    user = models.ForeignKey(User, related_name="resumes", on_delete=models.CASCADE)

    class Meta:
        unique_together = ('name', 'user')

    def __str__(self):
        return f"{self.name}"


class Recruitment(ModelBase):
    title = models.CharField(max_length=255)
    description = models.TextField()
    skills_required = models.CharField(max_length=255)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    work_time_start = models.DateTimeField(null=False)
    location = models.CharField(max_length=255)

    # foreignKey
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='recruitments')

    def __str__(self):
        return f"{self.title} - {self.company.name}"


class Apply(ModelBase):
    STATUS = [
        (0, 'Default'),
        (1, 'Accepted'),
        (2, 'Rejected'),
    ]

    status = models.IntegerField(choices=STATUS, default=0)

    # foreignKey
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)
    recruitment = models.ForeignKey(Recruitment, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.resume.user.full_name()} applied for {self.recruitment.title}"

    def is_done(self):
        return self.status != 0


class Interact(ModelBase):
    # foreignKey
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class Follow(Interact):
    def __str__(self):
        return f"{self.user.full_name()} follows {self.company.name}"

    class Meta:
        unique_together = ('user', 'company')


class UserComment(Interact):
    content = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.user.full_name()} commented on {self.company.user.full_name()}"


class CompanyComment(Interact):
    content = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.company.user.full_name()} commented on {self.user.full_name()}"