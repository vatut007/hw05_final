from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import resolve, Resolver404

from ..models import Group, Post

User = get_user_model()


class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.not_author = User.objects.create_user(username='NoAuthor')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.not_author_client = Client()
        self.not_author_client.force_login(self.not_author)
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовый пост',
            group=self.group,
        )

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/follow/': 'posts/follow.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html'

        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_urls_exists_at_desired_location(self):
        """Проверем доступность страниц."""
        urls = (
            '/',
            '/follow/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user.username}/',
            f'/posts/{self.post.id}/',
            '/create/',
            f'/posts/{self.post.id}/edit/',
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_unexisting_page(self):
        """Проверяет статус 404 несуществующей страницы."""
        with self.assertRaises(Resolver404):
            resolve('/foo/')

    def test_urls_uses_correct_errors_template(self):
        """Страница 404 отдает кастомный шаблон."""
        response = self.authorized_client.get('/404')
        self.assertTemplateUsed(response, 'core/404.html')

    def test_profile_post_edit_auth_not_author(self):
        """Страница /<username>/<post_id>/edit/ перенаправит
         авторизированного пользователя(не автора поста) на страницу поста.
        """
        response = self.not_author_client.get(
            (f'/posts/'
             f'{self.post.pk}/edit/'),
            follow=True
        )
        self.assertRedirects(
            response, (f'/posts/'
                       f'{self.post.pk}/'))

    def test_profile_post_edit_not_auth(self):
        """Страница /<username>/<post_id>/edit/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get(
            (f'/posts/'
             f'{self.post.pk}/edit/'),
            follow=True
        )
        self.assertRedirects(
            response,
            (f'/auth/login/?next=/'
             f'posts/'
             f'{self.post.pk}/edit/')
        )
