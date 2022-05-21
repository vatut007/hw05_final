from django.db import models

from .user import User
from .post import Post


class Comment (models.Model):
    post = models.ForeignKey(
        Post,
        verbose_name='Комментарий',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    text = models.TextField(
        verbose_name='Текст нового комментария'
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']
