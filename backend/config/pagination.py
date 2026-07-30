"""Paginacion estandar del back office."""
from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """
    PageNumberPagination que permite al cliente elegir el tamano de pagina via
    ?page_size=... (hasta 100). El back office trae todos los registros pidiendo
    paginas grandes; los consumidores que no lo especifican reciben PAGE_SIZE.
    """

    page_size_query_param = "page_size"
    max_page_size = 100
