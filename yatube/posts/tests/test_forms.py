from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostCreationAndEditFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User.objects.create_user(username='hanson')
        Group.objects.create(
            title='Название группы',
            slug='group_slug',
            description='Описание группы на 500 символов'
        )
        Post.objects.create(
            author=User.objects.get(username='hanson'),
            text='Мой первый пост'
        )

    def setUp(self):
        self.user_author = User.objects.get(username='hanson')
        self.authorized_user_author = Client()
        self.authorized_user_author.force_login(self.user_author)

    def test_sending_valid_form_create_post(self):
        '''Проверяем, что валидная форма создаёт и редактирует пост'''

        posts_count = Post.objects.count()
        form_data = {
            'text': 'тестовый текст поста'
        }
        self.authorized_user_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)

    def test_sending_valid_form_edit_post(self):
        '''Проверяем, что происходит редактирование поста'''

        group = Group.objects.get(id=1)
        form_data = {
            'text': 'забыл добавить группу',
            'group': '1'
        }
        self.authorized_user_author.post(
            reverse('posts:post_edit', args=('1',)),
            data=form_data
        )
        post = Post.objects.get(id=1)
        self.assertEqual(post.text, 'забыл добавить группу')
        self.assertEqual(post.group, group)
