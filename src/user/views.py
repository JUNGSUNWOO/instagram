from rest_framework import exceptions, generics
from rest_framework.authtoken.models import Token
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from my_validator import check_validation
from base_api import CreateAPIViewWithoutSerializer, UpdateAPIViewWithoutSerializer
from user.models import User
from user.permissions import IsUserMineOrReadOnly
from user.serializers import SignUpSerializer, UserUpdateSerializer, UserProfileSerializer, SearchSerializer


class Login(APIView):
    def post(self, request):
        schema = {'username': {'type': 'string', 'empty': False},
                  'password': {'type': 'string', 'empty': False}}
        data = request.data.dict()
        check_validation(schema, **data)

        user = get_object_or_404(User, username=data['username'])
        if user.check_password(data['password']):
            token, created = Token.objects.get_or_create(user_id=user.id)
            return Response(token.key)
        else:
            raise exceptions.ValidationError('비밀번호가 틀렸습니다.')


class SignUp(CreateAPIViewWithoutSerializer):
    schema = {'username': {'type': 'string', 'maxlength': 150, 'empty': False},
              'password': {'type': 'string', 'maxlength': 128, 'empty': False},
              'phone_number': {'type': 'string', 'maxlength': 13, 'empty': False},
              'email': {'type': 'string', 'regex': '^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$',
                        'maxlength': 254, 'empty': False},
              'description': {'type': 'string'},
              'profile_image': {'type': 'file', 'nullable': True}}
    class_to_create_object = User
    serializer_class = SignUpSerializer


class UserUpdate(UpdateAPIViewWithoutSerializer):
    schema = {'phone_number': {'type': 'string', 'maxlength': 13, 'empty': False},
              'email': {'type': 'string', 'regex': '^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$',
                        'maxlength': 254, 'empty': False},
              'description': {'type': 'string'},
              'profile_image': {'type': 'file', 'nullable': True}}
    queryset = User.objects.all()
    lookup_url_kwarg = 'user_id'
    lookup_field = 'id'
    serializer_class = UserUpdateSerializer
    permission_classes = (
        IsUserMineOrReadOnly,
    )


class UserFollow(UpdateAPIViewWithoutSerializer):
    permission_classes = (
        IsAuthenticatedOrReadOnly,
    )

    def patch(self, request, *args, **kwargs):
        if request.user.followings.filter(id=kwargs['user_id']).exists():
            request.user.followings.remove(kwargs['user_id'])
            result = {'result': False}
            return Response(result)
        else:
            request.user.followings.add(kwargs['user_id'])
            result = {'result': True}
            return Response(result)


class UserProfile(generics.RetrieveAPIView):
    queryset = User.objects.all()
    lookup_url_kwarg = 'user_id'
    lookup_field = 'id'
    serializer_class = UserProfileSerializer


class Search(generics.RetrieveAPIView):
    serializer_class = SearchSerializer

    def post(self, request, *args, **kwargs):
        data = request.data.dict()
        queryset = User.objects.filter(username__contains=data['body'])
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
