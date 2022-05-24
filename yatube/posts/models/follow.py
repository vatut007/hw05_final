from django.db import models

from .user import User


class Follow (models.Model):
    user = models.ForeignKey(
        User,
        related_name='follower',
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        User,
        related_name='following',
        on_delete=models.CASCADE,
    )

    class Meta:
        db_table = 'Follow'
        constraints = [models.UniqueConstraint(fields=['user', 'author'],
                       name='unique_follower')]
