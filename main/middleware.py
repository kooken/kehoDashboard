from django.core.mail import mail_admins
from django.utils.deprecation import MiddlewareMixin


class NotifyOSErrorMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        if isinstance(exception, OSError):
            subject = f"Site Error: {request.path}"
            message = f"""
            Exception: {exception}
            URL: {request.build_absolute_uri()}
            Request Method: {request.method}
            User Agent: {request.headers.get('User-Agent', 'unknown')}
            """
            mail_admins(subject, message)
