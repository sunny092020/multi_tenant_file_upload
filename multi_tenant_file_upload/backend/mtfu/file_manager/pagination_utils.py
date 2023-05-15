from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from mtfu.file_manager.serializers import FileSerializer

DEFAULT_PAGE_NUMBER = 1
DEFAULT_PAGE_SIZE = 10


def paginate_files(request, files, returned_fields):
    page_number = request.GET.get("page", DEFAULT_PAGE_NUMBER)
    page_size = request.GET.get("page_size", DEFAULT_PAGE_SIZE)

    files = files.order_by("name")

    paginator = Paginator(files, page_size)
    try:
        file_list = paginator.page(page_number)
    except PageNotAnInteger:
        file_list = paginator.page(DEFAULT_PAGE_NUMBER)
    except EmptyPage:
        file_list = paginator.page(paginator.num_pages)

    serializer = FileSerializer(file_list, many=True, fields=returned_fields)

    # Return serialized data with pagination information
    data = {
        "count": paginator.count,
        "num_pages": paginator.num_pages,
        "page_range": list(paginator.page_range),
        "files": serializer.data,
    }
    return data
