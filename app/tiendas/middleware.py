from django.conf import settings
from .models import Dominio

class CompanyDomainMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        host = request.get_host().split(':')[0].lower()
        request.company = None
        if host != settings.AMCEB_DOMAIN:
            dominio = (
                Dominio.objects
                .select_related('company')
                .filter(
                    dominio_personalizado=host
                )
                .first()
            )

            if dominio:
                request.company = dominio.company
                print('host:', host)
                print('company:', request.company)

        response = self.get_response(request)

        return response
