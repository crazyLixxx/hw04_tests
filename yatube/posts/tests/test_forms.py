from django import forms
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
        self.post = Post.objects.get(id=1)
        self.group = Group.objects.get(slug='group_slug')

    def test_post_forms(self):
        '''
        Тестируем формы на страницах создания и редактирования
        поста выводится форма
        '''
        test_objects = [
            (reverse('posts:post_edit', kwargs={'post_id': self.post.id})),
            (reverse('posts:post_create')),
        ]
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }

        for page in test_objects:
            response = self.authorized_user_author.get(page)
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_post(self):
        '''
        Проверяем, что в форму редактирования поста передаётся пост
        , соответсвующий урлу
        '''
        response = self.authorized_user_author.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        post_id = response.context['form'].instance.id

        self.assertEqual(post_id, self.post.id)

    def test_sending_valid_form_create_post(self):
        '''Проверяем, что валидная форма создаёт пост'''

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
