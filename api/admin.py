from django.contrib import admin
from api.models import (
    VUser, Volunteer, Rating, Comment, Task, Link, Unit
)


@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    readonly_fields = ('code',)


admin.site.register(VUser)
admin.site.register(Volunteer)
admin.site.register(Rating)
admin.site.register(Comment)
admin.site.register(Task)
admin.site.register(Unit)
