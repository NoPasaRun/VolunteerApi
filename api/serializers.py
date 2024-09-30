import base64
import uuid

from django.contrib.auth.models import update_last_login
from django.core.files.base import ContentFile
from django.db import IntegrityError
from rest_framework.exceptions import APIException

from rest_framework.serializers import (
    Serializer, UUIDField, ModelSerializer,
    SerializerMethodField, CharField, ImageField
)
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.settings import api_settings

from api.models import Link, Task, VUser, Volunteer, Unit, Comment


class Base64ImageField(ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format_, img_str = data.split(';base64,')
            name, ext = str(uuid.uuid4().urn[9:]), format_.split('/')[-1]
            data = ContentFile(base64.b64decode(img_str), name=name + '.' + ext)
        return super(Base64ImageField, self).to_internal_value(data)


class VUserSerializer(ModelSerializer):

    username = CharField(required=True, write_only=True, max_length=50)

    def save(self, password: str):
        try:
            if not self.is_valid():
                return None
            user = VUser(**self.validated_data)
            user.set_password(password)
            user.save()
        except IntegrityError as e:
            raise APIException({"detail": str(e)}, 400)
        self.validated_data.pop("username")
        return user

    class Meta:
        model = VUser
        write_only_fields = ('username',)
        fields = (
            "username",
            "first_name",
            "last_name",
            "email"
        )


class UnitSerializer(ModelSerializer):

    class Meta:
        model = Unit
        fields = (
            "title",
            "description"
        )


class VolunteerReadSerializer(ModelSerializer):
    unit = UnitSerializer(source="link.unit", read_only=True)
    user = VUserSerializer(read_only=True)

    class Meta:
        model = Volunteer
        write_only_fields = ('code',)
        fields = (
            "unit",
            "user",
            "avatar",
        )


class VolunteerSerializer(ModelSerializer):

    code = UUIDField(required=True, write_only=True)
    user = VUserSerializer()
    avatar = Base64ImageField(required=False)

    def create(self, validated_data):
        code = self.validated_data.pop("code")
        link = Link.objects.filter(code=code).first()
        if not link or not link.is_open:
            raise APIException({"code": "Not found or locked"}, 404)

        user_serializer = VUserSerializer(data=self.validated_data.pop("user"))
        user = user_serializer.save(password=str(code))

        try:
            volunteer = Volunteer(**self.validated_data, user=user)
            volunteer.link, volunteer.user = link, user
            volunteer.save()
        except IntegrityError as e:
            user.delete()
            raise APIException({"detail": str(e)}, 400)
        self.validated_data["user"] = user_serializer.validated_data
        return volunteer

    @property
    def data(self):
        volunteer_serializer = VolunteerReadSerializer(instance=self.instance)
        return volunteer_serializer.data

    class Meta:
        model = Volunteer
        write_only_fields = ('code',)
        fields = (
            "user",
            "avatar",
            "code",
        )


class TaskSerializer(ModelSerializer):

    creator = VUserSerializer(read_only=True)
    photo = SerializerMethodField()

    def get_photo(self, obj):
        comment = obj.comments.filter(photo__isnull=False).first()
        if comment:
            request = self.context["request"]
            return request.build_absolute_uri(comment.photo.url)
        return None

    class Meta:
        model = Task
        read_only_fields = ('creator', 'photo',)
        fields = (
            "title",
            "description",
            "creator",
            "score",
            "date_start",
            "date_end",
            "is_open",
            "photo"
        )


class CommentReadSerializer(ModelSerializer):

    volunteer = VolunteerReadSerializer(read_only=True)
    task = TaskSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ("text", "photo", "volunteer", "task")


class CommentSerializer(ModelSerializer):

    photo = Base64ImageField(required=False, write_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def data(self):
        comment_serializer = CommentReadSerializer(instance=self.instance)
        return comment_serializer.data

    def save(self, task: Task, volunteer: Volunteer):
        obj = Comment(**self.validated_data)
        obj.task, obj.volunteer = task, volunteer
        obj.save()

    class Meta:
        model = Comment
        fields = ("text", "photo",)


class VUserLoginSerializer(Serializer):

    code = UUIDField(required=True)

    def validate(self, attrs):
        link = Link.objects.filter(code=attrs.get('code')).first()
        if not link or not hasattr(link, 'volunteer'):
            raise APIException({"message": "Code is invalid"}, 400)
        user = link.volunteer.user

        token = AccessToken.for_user(user)
        if api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, user)
        print(token.payload)

        return {
            "access": str(token)
        }
