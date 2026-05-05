class NoStoreSensitivePagesMiddleware:
    """Prevent browser/proxy caching for account, cart, order, and payment pages."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        no_store_prefixes = getattr(request, 'no_store_prefixes', None)
        if no_store_prefixes is None:
            no_store_prefixes = (
                '/accounts/',
                '/cart/',
                '/orders/',
                '/payments/',
            )

        if request.path.startswith(no_store_prefixes):
            response['Cache-Control'] = 'no-store, no-cache, max-age=0, must-revalidate, private'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'

        return response
