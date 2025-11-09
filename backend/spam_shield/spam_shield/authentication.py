from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

class DjangoTokenAuthentication(TokenAuthentication):
    """
    Simple token based authentication using Django REST Framework's TokenAuthentication.
    Clients should authenticate by passing the token key in the "Authorization"
    HTTP header, prepended with the string "Token ".  For example:

        Authorization: Token 401f7ac837da42b97f613d789819ff93537bee6a
    """
    keyword = 'Bearer'  # Use 'Bearer' instead of 'Token' for compatibility
