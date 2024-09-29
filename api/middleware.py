class VolunteerMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            volunteer = request.user.volunteer if hasattr(request.user, 'volunteer') else None
            setattr(request, "volunteer", volunteer)

        response = self.get_response(request)
        return response
