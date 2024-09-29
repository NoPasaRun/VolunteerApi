from django.contrib.auth.models import update_last_login
from django.core.exceptions import ValidationError

from rest_framework.serializers import (
    Serializer, UUIDField, ModelSerializer,
    SerializerMethodField
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.settings import api_settings

from api.models import Link, Task, VUser, Volunteer, Unit, Comment


class VUserSerializer(ModelSerializer):

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


class VolunteerSerializer(ModelSerializer):

    unit = UnitSerializer(source="link.unit", read_only=True)
    code = UUIDField(required=True)
    user = VUserSerializer()

    def validate(self, attrs):
        link = Link.objects.filter(code=attrs.pop("code")).first()
        if not link or not link.is_open:
            raise ValidationError({"code": "Not found or locked"})
        attrs["link"] = link

    class Meta:
        model = Volunteer
        read_only_fields = ('unit', "score")
        write_only_fields = ('code',)
        fields = (
            "unit",
            "user",
            "score",
            "avatar",
            "code"
        )


class CommentSerializer(ModelSerializer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not (task := kwargs.get("task")):
            raise ValidationError("Task is required")
        self.data["task"] = task
        self.data["volunteer"] = self.context["request"].volunteer

    class Meta:
        model = Comment
        read_only_fields = ("task", "volunteer")
        fields = "__all__"


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


class VUserLoginSerializer(Serializer):

    code = UUIDField(required=True)

    def validate(self, attrs):
        link = Link.objects.filter(code=attrs.get('code')).first()
        if not link or not hasattr(link, 'volunteer'):
            raise ValidationError(message="Code is invalid")
        user = link.volunteer.user

        refresh = RefreshToken.for_user(user)
        if api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, user)

        return {
            "access": str(refresh.access_token)
        }
