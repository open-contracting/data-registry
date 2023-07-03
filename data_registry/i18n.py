from django.http.response import HttpResponse, HttpResponseRedirect
from django.urls import translate_url
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import check_for_language
from django.views.decorators.csrf import csrf_exempt


# Copy Django function to make CSRF exempt and to not set cookie or session.
# https://github.com/django/django/blob/stable/3.2.x/django/views/i18n.py
# https://docs.djangoproject.com/en/4.2/topics/i18n/translation/#how-django-discovers-language-preference
@csrf_exempt
def set_language(request):
    next_url = request.POST.get("next", request.GET.get("next"))
    if (next_url or request.accepts("text/html")) and not url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        next_url = request.META.get("HTTP_REFERER")
        if not url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            next_url = "/"
    response = HttpResponseRedirect(next_url) if next_url else HttpResponse(status=204)
    if request.method == "POST":
        lang_code = request.POST.get("language")
        if lang_code and check_for_language(lang_code):
            if next_url:
                next_trans = translate_url(next_url, lang_code)
                if next_trans != next_url:
                    response = HttpResponseRedirect(next_trans)
    return response
