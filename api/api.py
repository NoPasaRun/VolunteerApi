from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework_simplejwt.views import TokenViewBase

from api.models import Link, Task, Rating, Volunteer
from api.permissions import VolunteerPermission
from api.serializers import TaskSerializer, VUserLoginSerializer, VolunteerSerializer, CommentSerializer


class TokenObtainByLink(TokenViewBase):

    def post(self, request, code, *args, **kwargs):
        serializer = VUserLoginSerializer(data={"code": code})
        if serializer.is_valid():
            return Response(serializer.validated_data, status=200)
        return Response(serializer.errors, status=400)


class LinkApiView(APIView):

    permission_classes = (IsAdminUser,)

    def post(self, request, *args, **kwargs):
        (link := Link()).save()
        return Response({"code": link.code}, 201)


class VolunteerApi(generics.ListAPIView):
    serializer_class = VolunteerSerializer

    def get_queryset(self):
        return sorted(Volunteer.objects.all(), key=lambda v: v.score)


class MyApi(APIView):

    permission_classes = (VolunteerPermission,)
    serializer_class = VolunteerSerializer

    def get(self, request):
        data = VolunteerSerializer(instance=request.volunteer).data
        return Response(data, 200)

    def post(self, request, *args, **kwargs):
        serializer = VolunteerSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=200)
        return Response(serializer.errors, status=400)


class TaskApi(generics.ListAPIView):

    serializer_class = TaskSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Task.objects.filter(is_open=False)
        params = self.request.query_params

        queryset = Task.objects.filter(is_open=params.get("is_open", True))
        return queryset


class MyTaskApi(TaskApi):

    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Task.objects.filter(ratings__volunteer__user=self.request.user)


def proceed_task(view):
    def wrapper(self, request, task_id: int, *args, **kwargs):
        task = Task.objects.filter(id=task_id, is_open=True).first()
        if not task:
            return Response({"error": "Task not found or completed"}, status=400)
        return view(self, request, task, *args, **kwargs)
    return wrapper


class ManageTaskApi(APIView):

    permission_classes = (VolunteerPermission,)

    @proceed_task
    def post(self, request, task: Task, *args, **kwargs):
        Rating(task=task, volunteer=request.volunteer).save()
        return Response({"success": True}, 200)

    @proceed_task
    def delete(self, request, task: Task, *args, **kwargs):
        Rating.objects.filter(task=task).delete()
        return Response({"success": True}, 202)


class CommentApi(generics.CreateAPIView):

    serializer_class = CommentSerializer
    permission_classes = (VolunteerPermission,)

    @proceed_task
    def post(self, request, task: Task, *args, **kwargs):
        serializer = CommentSerializer(data=request.data, task=task)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=200)
        return Response(serializer.errors, status=400)
