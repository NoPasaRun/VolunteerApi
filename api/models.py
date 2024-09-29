import os
from datetime import timedelta, datetime
from uuid import uuid4

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Sum
from django.utils.deconstruct import deconstructible


@deconstructible
class UploadToPathAndRename(object):
    def __init__(self, path):
        self.sub_path = path

    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        name = instance.pk if instance.pk else uuid4().hex
        return os.path.join(self.sub_path, '{}.{}'.format(name, ext))


class VUser(AbstractUser):
    TARIFFS = (
        ((FREE := "free"), "Бесплатный"),
        ("advanced", "Расширенный"),
        ("special", "Специальный")
    )
    tariff = models.CharField(max_length=100, choices=TARIFFS, default=FREE)


class Unit(models.Model):
    creator = models.ForeignKey(VUser, on_delete=models.CASCADE, related_name='units')
    title = models.CharField(max_length=100)
    description = models.TextField()


class Link(models.Model):
    code = models.UUIDField(unique=True, default=uuid4)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='links')

    def is_open(self):
        return hasattr(self, 'volunteer')


class Task(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    creator = models.ForeignKey(VUser, on_delete=models.CASCADE, related_name='tasks')
    score = models.PositiveIntegerField(default=0)
    date_start = models.DateTimeField()
    date_end = models.DateTimeField()
    is_open = models.BooleanField(default=True)

    @property
    def is_archived(self):
        return self.date_end + timedelta(days=2) > datetime.now()


class Volunteer(models.Model):
    user = models.OneToOneField(VUser, on_delete=models.CASCADE, related_name='volunteer')
    link = models.OneToOneField(Link, on_delete=models.CASCADE, related_name='volunteer')
    avatar = models.ImageField(upload_to=UploadToPathAndRename("volunteer"), null=True, blank=True)

    @property
    def score(self):
        return self.ratings.filter(task__is_open=False).aggregate(
            Sum("task__score")
        ).get("task__score__sum", 0)


class Rating(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='ratings')
    volunteer = models.ForeignKey(Volunteer, on_delete=models.CASCADE, related_name='ratings')

    class Meta:
        unique_together = ('task', 'volunteer')


class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    volunteer = models.ForeignKey(Volunteer, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    photo = models.ImageField(upload_to=UploadToPathAndRename("comment"), null=True, blank=True)
