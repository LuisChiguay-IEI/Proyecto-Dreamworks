from django.conf import settings
from django.contrib.auth import logout


class ServerSessionMiddleware:
    """Una sesión local solo es válida durante la ejecución que la creó."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        server_id = settings.SERVER_SESSION_ID
        if (server_id and request.user.is_authenticated
                and request.session.get('_server_session_id') != server_id):
            logout(request)
        response = self.get_response(request)
        if server_id and request.user.is_authenticated:
            request.session['_server_session_id'] = server_id
        return response
