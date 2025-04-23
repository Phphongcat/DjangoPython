from django.contrib import admin
from django.db.models import Count
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls.conf import path
from django.utils.safestring import mark_safe

from .models import Category, Company, CompanyImage


class CompanyImageInline(admin.TabularInline):
    model = CompanyImage
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
        company = Company.objects.get(pk=company_id)
        company.verified = True
        company.save()
        self.message_user(request, f"Công ty '{company.name}' đã được xác thực.")
        return redirect(f'../../{company_id}/change/')


class MyAdminSite(admin.AdminSite):
    site_header = 'Quản Lý Tìm Kiếm Việc Làm.'

    def get_urls(self):
        return [path('recruitment-stats/', self.recruitment_stats)] + super().get_urls()

    def recruitment_stats(self, request):
        stats = Category.objects.annotate(cate_count=Count('recruitment__id')).values('id', 'name', 'cate_count')
        return TemplateResponse(request, 'admin/recruitment_stats.html', {
            'stats': stats
        })


admin_site = MyAdminSite(name='admin')
admin_site.register(Category)
admin_site.register(Company, CompanyAdmin)