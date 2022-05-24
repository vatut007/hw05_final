import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, Comment

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
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
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        '''Валидная форма создает запись Post'''
        post_count = Post.objects.count()
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
            content_type='image/gif'
        )
        group_field = self.group.id
        form_data = {
            'text': 'Тестовый текст поста 2',
            'group': group_field,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True)
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=self.group.id,
                text=form_data['text'],
                id=Post.objects.all().order_by('-id')[0].id,
                image='posts/small.gif'
            ).exists()
        )

    def test_edit_post(self):
        '''Проверка формы редактирования поста и изменение его в базе данных'''
        group_field = self.group.id
        form_data = {
            'text': 'Тестовый текст отредактированного поста',
            'group': group_field,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={
                'post_id': self.post.pk}),
            data=form_data,
            follow=True)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={
                'post_id': self.post.pk}))
        self.assertTrue(
            Post.objects.filter(
                group=self.group,
                text=form_data['text'],
                id=self.post.pk,
            ).exists()
        )

    def test_create_comment(self):
        """Проверка формы создания нового комментария"""
        comment_count = Comment.objects.filter(post=self.post.pk).count()
        form_data = {
            'text': 'Тестовый текст комментария',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={
                'post_id': self.post.pk}), data=form_data, follow=True)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                post=self.post.pk,
                text=form_data['text'],
                id=Comment.objects.all().order_by('-id')[0].id
            ).exists()
        )
