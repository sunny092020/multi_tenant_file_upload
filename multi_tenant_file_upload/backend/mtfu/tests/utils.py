import json


def get_content_from_response(response):
    return json.loads(response.content.decode("utf8"))
