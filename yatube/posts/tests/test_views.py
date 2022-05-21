import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, Follow
from yatube.settings import NUMBER_Of_POSTS

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='VasyaVasyev')
        cls.guest_client = Client()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif')
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        for text in range(13):
            self.post = Post.objects.create(
                author=self.user,
                text=f'Тестовый пост {text}',
                group=self.group,
                image=uploaded)
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:home'): 'posts/index.html',
            reverse('posts:group_list', kwargs={
                'slug': self.group.slug}): 'posts/group_list.html',
            reverse('posts:profile', kwargs={
                'username': self.user.username}): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={
                'post_id': self.post.id}): 'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={
                'post_id': self.post.id}): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template, in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_index_group_profile_page_show_correct_cont(self):
        """Проверяем Context страницы index, group, profile"""
        context = [
            self.authorized_client.get(reverse('posts:home')),
            self.authorized_client.get(reverse(
                'posts:group_list', kwargs={'slug': self.group.slug})),
            self.authorized_client.get(reverse(
                'posts:profile', kwargs={'username': self.user.username})),
        ]
        for response in context:
            first_object = response.context['page_obj'][0]
            context_objects = {
                self.user.id: first_object.author.id,
                self.post.text: first_object.text,
                self.post.id: first_object.id,
                self.post.image: first_object.image,
            }
            for reverse_name, response_name in context_objects.items():
                with self.subTest(reverse_name=reverse_name):
                    self.assertEqual(response_name, reverse_name)

    def test_first_page_contains_ten_records(self):
        """Проверяем, что количество постов на первой странице равно 10"""
        response = self.client.get(reverse('posts:home'))
        self.assertEqual(len(response.context['page_obj']), NUMBER_Of_POSTS)

    def test_second_page_contains_three_records(self):
        """Проверяем, что количество постов на второй странице равно 3"""
        response = self.client.get(reverse('posts:home') + '?page=2')
        total_number_of_posts = Post.objects.count()
        rest_of_post = total_number_of_posts - NUMBER_Of_POSTS
        self.assertEqual(len(response.context['page_obj']), rest_of_post)

    def test_post_detail_show_correct_context(self):
        """Проверяем Context страницы post_detail"""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        first_object = response.context['post']
        context_objects = {
            self.post.id: first_object.id,
            self.post.author.posts.count(): first_object.author.posts.count(),
            self.post.image: first_object.image}
        for reverse_name, response_name in context_objects.items():
            with self.subTest(reverse_name=reverse_name):
                self.assertEqual(response_name, reverse_name)

    def test_post_create_show_correct_context(self):
        """Проверяем Context страницы post_create"""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.ModelChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Пррверяем Context страницы post_edit"""
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.group.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.ModelChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_add_comment_for_guest(self):
        '''Неавторизированный пользователь не может оставить комментарий'''
        response = self.guest_client.get(
            reverse('posts:add_comment', kwargs={
                'post_id': self.post.pk, }))
        self.assertEqual(response.status_code, HTTPStatus.FOUND.value, (
            'Неавторизированный пользователь',
            'не может оставлять комментарий'))

    def test_comment_for_auth_user(self):
        """Авторизированный пользователь может оставить комментарий"""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        self.assertEqual(
            response.status_code,
            HTTPStatus.OK,
            ('Авторизированный пользователь'
             ' должен иметь возможность'
             ' оставлять комментарий'))


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='VasyaVasyev2')
        cls.user_follow = User.objects.create_user(username='le02')
        cls.guest_client = Client()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        self.post = Post.objects.create(
            author=self.user_follow,
            text='Тестовый пост')

    def test_follow(self):
        '''Проверка работы подписки на автора'''
        author = self.user_follow
        self.authorized_client.get(
            reverse('posts:profile_follow', args=[author.username]))
        follower = Follow.objects.filter(
            user=self.user, author=author).exists()
        self.assertTrue(
            follower,
            'Не работает подписка на автора'
        )

    def test_unfollow(self):
        """Тест работы отписки от автора."""
        author = self.user_follow
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                args=[author.username]
            ),
        )
        follower = Follow.objects.filter(
            user=self.user,
            author=author
        ).exists()
        self.assertFalse(
            follower,
            'Не работает отписка от автора'
        )

    def test_new_author_post_for_follower(self):
        '''Запись пользователя появляется у тех, кто на него подписан'''
        author = self.user_follow
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                args=[author.username]
            )
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 1)
        Post.objects.create(
            text='test_new_post',
            author=author)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 2)

    def test_new_author_post_for_unfollower(self):
        '''Запись пользователя не появляется у тех, кто не подписан'''
        author = self.user_follow
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                args=[author.username]
            )
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 0)
        Post.objects.create(
            text='test_new_post',
            author=author)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 0)
