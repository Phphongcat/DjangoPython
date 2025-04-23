from rest_framework.pagination import PageNumberPagination


class RecruitmentPaginator(PageNumberPagination):
    page_size = 5


class CompanyPaginator(PageNumberPagination):
    page_size = 5


class CommentPaginator(PageNumberPagination):
    page_size = 10


class ResumePaginator(PageNumberPagination):
    page_size = 5