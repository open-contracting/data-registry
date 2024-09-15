def content_encoding_middleware(get_response):
    def middleware(request):
        response = get_response(request)

        if response.has_header("Content-Encoding") and not response["Content-Encoding"]:
            del response["Content-Encoding"]

        return response

    return middleware
