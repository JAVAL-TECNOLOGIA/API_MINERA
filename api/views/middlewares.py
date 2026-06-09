class DebugLoginRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path in {"/api/auth/login/", "/api/plantillas/asignadas/"}:
            print("\n=== DEBUG LOGIN REQUEST ===")
            print("REMOTE_ADDR:", request.META.get("REMOTE_ADDR"))
            print("HOST HEADER:", request.META.get("HTTP_HOST"))
            print("CONTENT_TYPE:", request.META.get("CONTENT_TYPE"))
            auth_state = "<present>" if request.META.get("HTTP_AUTHORIZATION") else "<empty>"
            print("AUTH HEADER:", auth_state)
            print("RAW BODY:", "<redacted>")

        response = self.get_response(request)

        if request.path in {"/api/auth/login/", "/api/plantillas/asignadas/"}:
            print("RESPONSE STATUS:", response.status_code)
            print("=== END DEBUG LOGIN ===\n")

        return response
