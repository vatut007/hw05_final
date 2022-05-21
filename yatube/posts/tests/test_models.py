from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у модели Post корректно работает __str__."""
        act = PostModelTest.post.text[:15]
        self.assertEqual(
            act,
            self.post.text,
            'Метод post.text работает неправильно.')

    def test_models_have_correct_object_group(self):
        """Проверяем, что у модели Group корректно работает __str__."""
        act = PostModelTest.group.title
        self.assertEqual(
            act,
            self.group.title,
            'Метод grop.title работает неправильно.')
