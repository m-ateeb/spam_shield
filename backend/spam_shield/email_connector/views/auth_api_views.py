"""
API views for authentication
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
import json

from ..services.auth_service import AuthService

auth_service = AuthService()


@login_required
def get_auth_token(request):
    """Get or create API token for authenticated user"""
    token = auth_service.get_or_create_token(request.user)
    return JsonResponse({
        'token': token.key,
        'user_id': request.user.id,
        'email': request.user.email,
    })


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def email_password_login(request):
    """Login with email and password"""
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return Response(
                {'error': 'Email and password required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = auth_service.authenticate_user(email, password)
        if not user:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        from django.contrib.auth import login
        login(request, user)
        
        token = auth_service.get_or_create_token(user)
        user_info = auth_service.get_user_info(user)
        
        return Response({
            'token': token.key,
            'user': user_info,
        })
    except json.JSONDecodeError:
        return Response(
            {'error': 'Invalid JSON'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def email_password_signup(request):
    """Sign up with email and password"""
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        username = data.get('username')
        
        if not email or not password:
            return Response(
                {'error': 'Email and password required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user, created = auth_service.create_user(email, password, username)
        if not created:
            return Response(
                {'error': 'User with this email already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from django.contrib.auth import login
        login(request, user)
        
        token = auth_service.get_or_create_token(user)
        user_info = auth_service.get_user_info(user)
        
        return Response({
            'token': token.key,
            'user': user_info,
        }, status=status.HTTP_201_CREATED)
    except json.JSONDecodeError:
        return Response(
            {'error': 'Invalid JSON'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@login_required
def logout_view(request):
    """Logout user"""
    from django.contrib.auth import logout
    logout(request)
    return JsonResponse({'success': True})


@login_required
def user_info(request):
    """Get current user information"""
    user_info = auth_service.get_user_info(request.user)
    return JsonResponse({'user': user_info})

