from datetime import datetime

from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PagesAndContext(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User.objects.create_user(username='tom')
        User.objects.create_user(username='hanson')
        Group.objects.create(
            title='Название группы',
            slug='group_slug',
            description='Описание группы на 500 символов'
        )
        Group.objects.create(
            title='Название группы 2',
            slug='group_slug_2',
            description='Описание группы 2 на 500 символов'
        )

        posts = 1
        while posts < 14:
            Post.objects.create(
                author=User.objects.get(username='hanson'),
                text='вторая половина личности тома хэнсона писала здесь',
                group=Group.objects.get(id=2)
            )
            posts += 1
        while posts < 19:
            Post.objects.create(
                author=User.objects.get(username='tom'),
                text=f'тут текст гениального поста про {posts} моряков',
                group=Group.objects.get(id=1)
            )
            posts += 1

    def setUp(self):
        self.user_author = User.objects.get(username='hanson')
        self.authorized_user_author = Client()
        self.authorized_user_author.force_login(self.user_author)
        self.user_author2 = User.objects.get(username='tom')
        self.authorized_user_author2 = Client()
        self.authorized_user_author2.force_login(self.user_author2)

    def test_pages_uses_correct_template(self):
        '''Тестируем, что имена из namespace вызывают правильные шаблоны'''
        test_objects = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': 'group_slug'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': 'hanson'}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': '3'}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': '3'}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html'
        }
        for name, template in test_objects.items():
            with self.subTest(name=name):
                response = self.authorized_user_author.get(name)
                self.assertTemplateUsed(response, template)

    def test_pages_show_correct_context(self):
        '''
        Тестируем вывод постов на страницы, где они выводятся во множестве
        '''
        test_objects = [
            (reverse('posts:index'), 'page_obj'),
            (reverse(
                'posts:group_list', kwargs={'slug': 'group_slug_2'}
            ), 'page_obj'),
            (reverse(
                'posts:profile', kwargs={'username': 'hanson'}
            ), 'page_obj'),
        ]
        for page, posts in test_objects:
            with self.subTest(page=page):
                response = self.authorized_user_author.get(page)
                post = response.context[posts][7]
                self.assertEqual(
                    post.author, User.objects.get(username='hanson')
                )
                self.assertEqual(
                    post.text,
                    'вторая половина личности тома хэнсона писала здесь'
                )
                self.assertEqual(post.group, Group.objects.get(id=2))
                self.assertEqual(
                    post.pub_date.strftime('%Y-%m-%d'),
                    datetime.today().strftime('%Y-%m-%d')
                )

    def test_page_paginator(self):
        '''Тестируем пагинатор на страницах, где есть множество постов'''
        test_objects = [
            (reverse('posts:index'),
                'page_obj',
                10,
                8),
            (reverse(
                'posts:group_list', kwargs={'slug': 'group_slug_2'}
            ),
                'page_obj',
                10,
                3),
            (reverse(
                'posts:profile', kwargs={'username': 'hanson'}
            ),
                'page_obj',
                10,
                3),
        ]
        for page, posts, count_page_1, count_page_2 in test_objects:
            response_1 = self.authorized_user_author.get(page)
            response_2 = self.authorized_user_author.get(page + '?page=2')
            self.assertEqual(
                len(response_1.context[posts]),
                count_page_1,
                f'ошибка в выдаче первой страницы пагинации на {page}')
            self.assertEqual(
                len(response_2.context[posts]),
                count_page_2,
                f'ошибка в выдаче второй страницы пагинации на {page}')

    def test_index_page_show_posts_from_defferent_groups(self):
        '''
        Тестируем, что на главной странице отображаются посты из разных групп
        '''
        response = self.authorized_user_author.get(reverse('posts:index'))
        post1 = response.context['page_obj'][0]
        post2 = response.context['page_obj'][9]
        self.assertNotEqual(
            post1.group,
            post2.group
        )

    def test_group_page_show_posts_from_one_group(self):
        '''
        Тестируем, что на странице группы отображаются посты только этой группы
        '''
        response = self.authorized_user_author.get(
            reverse('posts:group_list', kwargs={'slug': 'group_slug'})
        )
        posts = response.context['page_obj']
        for post in posts:
            with self.subTest(post=post):
                self.assertEqual(post.group.id, 1)

    def test_profile_page_show_posts_from_one_user(self):
        '''
        Тестируем, что в профиле отображаются только посты пользователя
        '''
        response = self.authorized_user_author.get(
            reverse('posts:profile', kwargs={'username': 'tom'})
        )
        posts = response.context['page_obj']
        for post in posts:
            with self.subTest(post=post):
                self.assertEqual(
                    post.author.id, 1)

    def test_detail_post_page_show_post_right(self):
        '''Тестируем, что на детальной странице поста отображается пост'''
        response = self.authorized_user_author.get(
            reverse('posts:post_detail', kwargs={'post_id': '3'})
        )
        post = response.context['post']
        self.assertEqual(post.id, 3)
        self.assertEqual(
            post.author, User.objects.get(username='hanson')
        )
        self.assertEqual(
            post.text,
            'вторая половина личности тома хэнсона писала здесь'
        )
        self.assertEqual(post.group, Group.objects.get(id=2))
        self.assertEqual(
            post.pub_date.strftime('%Y-%m-%d'),
            datetime.today().strftime('%Y-%m-%d')
        )

    def test_post_forms(self):
        '''
        Тестируем формы на страницах создания и редактирования
        поста выводится форма
        '''
        test_objects = [
            (reverse('posts:post_edit', kwargs={'post_id': '3'})),
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
            reverse('posts:post_edit', kwargs={'post_id': '3'})
        )
        post_id = response.context['form'].instance.id

        self.assertEqual(post_id, 3)

    def test_create_post_and_check_it_availability(self):
        '''
        Проверяем создание поста и его появление вначале
        главной, страницы группы и профиля пользователя
        '''
        test_post = Post.objects.create(
            author=User.objects.get(username='hanson'),
            text='тестовый тост',
            group=Group.objects.get(id=1)
        )
        test_objects_1 = [
            (
                'Новый пост не появляется на главной странице',
                reverse('posts:index'),
                'page_obj'),
            (
                'Новый пост не появляется на странице присвоенной ему группы',
                reverse(
                    'posts:group_list', kwargs={'slug': 'group_slug'}
                ),
                'page_obj'),
            (
                'Новый пост не появляется на странице его автора',
                reverse(
                    'posts:profile', kwargs={'username': 'hanson'}
                ),
                'page_obj'),
        ]
        test_objects_2 = [
            (
                'Новый пост появляется на странице не своей группы',
                reverse(
                    'posts:group_list', kwargs={'slug': 'group_slug_2'}
                ),
                'page_obj'),
            (
                'Новый пост появляется на странице не своего автора',
                reverse(
                    'posts:profile', kwargs={'username': 'tom'}
                ),
                'page_obj'),
        ]

        for error, page, posts in test_objects_1:
            with self.subTest(page=page):
                response = self.authorized_user_author.get(page)
                post = response.context[posts][0]
                self.assertEqual(post.id, test_post.id, error)

        for error, page, posts in test_objects_2:
            with self.subTest(page=page):
                response = self.authorized_user_author.get(page)
                post = response.context[posts][0]
                self.assertNotEqual(post.id, test_post.id, error)
