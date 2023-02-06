from django.core.paginator import Paginator


NUMBER_OF_POSTS = 10


def get_pages(request, post_list):
    paginator = Paginator(post_list, NUMBER_OF_POSTS)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
