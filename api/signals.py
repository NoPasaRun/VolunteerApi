import os

from django.conf import settings


def remove_file(path) -> bool:
    abs_file_path = os.path.join(settings.MEDIA_ROOT, path)
    if os.path.exists(abs_file_path):
        os.remove(abs_file_path)
        return True
    return False


def update_media(sender, instance, **kwargs) -> None:  # pylint: disable=unused-argument
    if sender.objects.filter(id=instance.id).exists():
        obj = sender.objects.get(id=instance.id)
        files = filter(lambda field: hasattr(obj, field), ["image", "video"])
        for file in files:
            if getattr(obj, file) != getattr(instance, file):
                try:
                    remove_file(str(getattr(obj, file)))
                except IsADirectoryError as error:
                    pass


def delete_media(sender, instance, **kwargs) -> None:  # pylint: disable=unused-argument
    if sender.objects.filter(id=instance.id).exists():
        obj = sender.objects.get(id=instance.id)
        files = filter(lambda field: hasattr(obj, field), ["photo", "avatar"])
        for file in files:
            try:
                remove_file(str(getattr(obj, file)))
            except IsADirectoryError as error:
                pass
