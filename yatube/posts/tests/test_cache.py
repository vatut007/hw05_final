from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post

User = get_user_model()


class CacheViewsTest(TestCase):
    """Проверка хранения и очищения кэша для index."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='VasyaVasyev')

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовый пост')

    def test_cache_index(self):
        response = self.authorized_client.get(reverse('posts:home'))
        posts = response.content
        Post.objects.create(
            text='Тестовый пост 2',
            author=self.user,
        )
        response_old = self.authorized_client.get(
            reverse('posts:home')
        )
        old_posts = response_old.content
        self.assertEqual(
            old_posts,
            posts,
            'Не возвращает кэшированную страницу.'
        )
        cache.clear()
        response_new = self.authorized_client.get(reverse('posts:home'))
        new_posts = response_new.content
        self.assertNotEqual(old_posts, new_posts, 'Нет сброса кэша.')
