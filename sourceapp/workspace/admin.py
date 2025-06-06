from django.contrib import admin
from django.db.models import Count, Avg
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls.conf import path
from django.utils.dateparse import parse_date
from django.utils.safestring import mark_safe

from . import models


class CompanyImageInline(admin.TabularInline):
    model = models.CompanyImage
    extra = 0
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="100" style="border-radius: 5px;" />')
        return "No Image"

    image_preview.short_description = "Image"


class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'verified', 'user', 'verify_button']
    list_filter = ['verified']
    inlines = [CompanyImageInline]

    def verify_button(self, obj):
        if not obj.verified:
            return mark_safe(f'<a class="button" href="{obj.id}/verify/">Xác Thực</a>')
        return "Đã Xác Thực"

    verify_button.short_description = "Xác Thực"
    verify_button.allow_tags = True

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:company_id>/verify/', self.admin_site.admin_view(self.verify_company), name='verify_company'),
        ]
        return custom_urls + urls

    def verify_company(self, request, company_id):
        company = models.Company.objects.get(pk=company_id)
        company.verified = True
        company.save()
        self.message_user(request, f"Công ty '{company.name}' đã được xác thực.")
        return redirect(f'../../{company_id}/change/')


class MyAdminSite(admin.AdminSite):
    site_header = 'Quản Lý Tìm Kiếm Việc Làm.'

    def get_urls(self):
        return [path('stats/', self.recruitment_stats)] + super().get_urls()

    def recruitment_stats(self, request):
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        start_date_parsed = parse_date(start_date) if start_date else None
        end_date_parsed = parse_date(end_date) if end_date else None

        recruitments = models.Recruitment.objects.all()
        if start_date_parsed:
            recruitments = recruitments.filter(date_start__gte=start_date_parsed)
        if end_date_parsed:
            recruitments = recruitments.filter(date_start__lte=end_date_parsed)

        category_stats = models.Category.objects.filter(
            recruitment__in=recruitments
        ).annotate(
            cate_count=Count('recruitment'),
            avg_salary=Avg('recruitment__salary')
        ).values('name', 'cate_count', 'avg_salary')

        recruitment_stats = [
            {**item, 'avg_salary': float(item['avg_salary']) if item['avg_salary'] is not None else 0.0}
            for item in category_stats
        ]

        work_type_stats = models.WorkType.objects.filter(
            recruitment__in=recruitments
        ).annotate(
            job_count=Count('recruitment')
        ).values('name', 'job_count')

        user_count = models.User.objects.filter(role=0, is_staff=0).count()
        company_count = models.Company.objects.count()

        context = {
            'recruitment_stats': recruitment_stats,
            'work_type_stats': work_type_stats,
            'user_count': user_count,
            'company_count': company_count,
            'start_date': start_date,
            'end_date': end_date,
        }

        return TemplateResponse(request, 'admin/recruitment_stats.html', context)


admin_site = MyAdminSite(name='admin')
admin_site.register(models.Category)
admin_site.register(models.WorkType)
admin_site.register(models.Company, CompanyAdmin)
