from rest_framework.pagination import PageNumberPagination


class RecruitmentPaginator(PageNumberPagination):
    page_size = 5


class ResumePaginator(PageNumberPagination):
    page_size = 7


class ApplyPagination(PageNumberPagination):
    page_size = 8


class CommentPaginator(PageNumberPagination):
    page_size = 10
