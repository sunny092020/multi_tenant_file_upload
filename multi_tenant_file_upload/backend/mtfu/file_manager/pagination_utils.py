from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from mtfu.file_manager.serializers import FileSerializer


def paginate_files(request, files, returned_fields):
    page_number = request.GET.get("page", 1)
    page_size = request.GET.get("page_size", 10)

    files = files.order_by("name")

    paginator = Paginator(files, page_size)
    try:
        file_list = paginator.page(page_number)
    except PageNotAnInteger:
        file_list = paginator.page(1)
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
