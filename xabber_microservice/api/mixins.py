from django.conf import settings


class AdminMethodMixin:
    def _authenticate(self):
        auth_header = self.request.headers.get('Authorization')

        if not auth_header:
            raise Exception('Authentication credentials were not provided.')

        try:
            auth_type, token = auth_header.split(' ')
            if auth_type.lower() != 'bearer':
                raise ValueError('Invalid authentication type')
        except ValueError:
            raise Exception('Invalid Authorization header format. Expected: Bearer <token>')

        if token != settings.WEEBHOOKS_SECRET:
            raise Exception('Invalid authentication token')