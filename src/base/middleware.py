from django.utils.deprecation import MiddlewareMixin


class DisableCsrfCheckForNgrok(MiddlewareMixin):
    def process_request(self, request):
        # if 'ngrok.io' in request.get_host():
        setattr(request, '_dont_enforce_csrf_checks', True)