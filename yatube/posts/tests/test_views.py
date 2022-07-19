from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PagesAndContext(TestCase):
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
            text='пост про зефирных морячков',
            group=Group.objects.get(id=1)
        )

    def setUp(self):
        self.user_author = User.objects.get(username='hanson')
        self.authorized_user_author = Client()
        self.authorized_user_author.force_login(self.user_author)
        self.post = Post.objects.get(id=1)
        self.group = Group.objects.get(slug='group_slug')

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
                'posts:post_detail', kwargs={'post_id': '1'}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': '1'}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html'
        }
        for name, template in test_objects.items():
            with self.subTest(name=name):
                response = self.authorized_user_author.get(name)
                self.assertTemplateUsed(response, template)

    def test_pages_with_many_posts_show_correct_context(self):
        '''
        Тестируем элементы поста при выводе на страницах с несколькими постами
        '''

        test_objects = [
            (reverse('posts:index'), 'page_obj'),
            (reverse(
                'posts:group_list', kwargs={'slug': 'group_slug'}),
                'page_obj'),
            (reverse(
                'posts:profile', kwargs={'username': 'hanson'}),
                'page_obj'),
        ]

        for page, posts in test_objects:
            with self.subTest(page=page):
                response = self.authorized_user_author.get(page)
                test_post = response.context[posts][0]
                self.assertEqual(test_post.author, self.post.author)
                self.assertEqual(test_post.text, self.post.text)
                self.assertEqual(test_post.group, self.post.group)
                self.assertEqual(test_post.created, self.post.created)

    def test_pages_with_one_post_show_correct_context(self):
        '''
        Тестируем элементы поста при выводе на страницах с одним постом
        '''

        test_objects = [
            (reverse(
                'posts:post_detail', kwargs={'post_id': '1'}),
                'article'),
        ]

        for page, post in test_objects:
            with self.subTest(page=page):
                response = self.authorized_user_author.get(page)
                test_post = response.context[post]
                self.assertEqual(test_post.author, self.post.author)
                self.assertEqual(test_post.text, self.post.text)
                self.assertEqual(test_post.group, self.post.group)
                self.assertEqual(test_post.created, self.post.created)

    def test_page_paginator(self):
        '''Тестируем, что пагинатор отдаёт корректное количество постов'''

        Post.objects.bulk_create([
            Post(
                text=f'Текст поста {i+1}',
                author=self.user_author,
                group=self.group
            )
            for i in range(15)
        ])
        test_objects = [
            (reverse('posts:index'),
                'page_obj'),
            (reverse(
                'posts:group_list', kwargs={'slug': 'group_slug'}
            ),
                'page_obj'),
            (reverse(
                'posts:profile', kwargs={'username': 'hanson'}
            ),
                'page_obj'),
        ]

        for page, posts in test_objects:
            response_1 = self.authorized_user_author.get(page)
            response_2 = self.authorized_user_author.get(page + '?page=2')
            self.assertEqual(
                len(response_1.context[posts]),
                10,
                f'ошибка в выдаче первой страницы пагинации на {page}')
            self.assertEqual(
                len(response_2.context[posts]),
                6,
                f'ошибка в выдаче второй страницы пагинации на {page}')

    def test_index_page_show_all_posts_from_defferent_groups(self):
        '''
        Тестируем, что главная страница отображает все посты, в том
        числе их разных групп
        '''

        group_2 = Group.objects.create(
            title='Название группы 2',
            slug='group_slug_2',
            description='Описание группы 2 на 500 символов'
        )
        Post.objects.create(
            text='Небольшой текст',
            author=self.user_author,
            group=group_2
        )
        response = self.authorized_user_author.get(reverse('posts:index'))
        test_posts_count = len(response.context['page_obj'])
        all_posts_count = Post.objects.count()

        self.assertEqual(test_posts_count, all_posts_count)

    def test_group_page_show_posts_only_from_one_group(self):
        '''
        Тестируем, что на странице группы отображаются посты только этой группы
        '''

        new_group = Group.objects.create(
            title='Название группы 2',
            slug='new_group',
            description='Описание группы 2 на 500 символов'
        )
        Post.objects.create(
            text='Небольшой текст',
            author=self.user_author,
            group=new_group
        )
        response_old_group = self.authorized_user_author.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        posts_in_old_group = response_old_group.context['page_obj']

        for post in posts_in_old_group:
            with self.subTest(post=post):
                self.assertEqual(post.group.slug, self.group.slug)

    def test_profile_page_show_posts_from_one_user(self):
        '''
        Тестируем, что в профиле отображаются только посты пользователя
        '''

        author_2 = User.objects.create(username='tom')
        Post.objects.create(
            text='небольшой текст',
            author=author_2
        )
        response = self.authorized_user_author.get(
            reverse('posts:profile', kwargs={'username': author_2.username})
        )
        posts = response.context['page_obj']

        for post in posts:
            with self.subTest(post=post):
                self.assertEqual(
                    post.author.username, author_2.username)

    def test_create_post_and_check_it_availability(self):
        '''
        Проверяем создание поста и его появление вначале
        главной, страницы группы и профиля пользователя
        '''
        test_post = Post.objects.create(
            author=self.user_author,
            text='тестовый тост',
            group=self.group
        )
        test_objects = [
            (
                'Новый пост не появляется на главной странице',
                reverse('posts:index'),
                'page_obj'),
            (
                'Новый пост не появляется на странице присвоенной ему группы',
                reverse(
                    'posts:group_list', kwargs={'slug': self.group.slug}
                ),
                'page_obj'),
            (
                'Новый пост не появляется на странице его автора',
                reverse(
                    'posts:profile',
                    kwargs={'username': self.user_author.username}
                ),
                'page_obj'),
        ]

        for error, page, posts in test_objects:
            with self.subTest(page=page):
                response = self.authorized_user_author.get(page)
                post = response.context[posts][0]
                self.assertEqual(post.id, test_post.id, error)
