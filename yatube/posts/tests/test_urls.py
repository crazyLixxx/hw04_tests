from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()
CommonURLs = {
    '': 'posts/index.html',
    '/group/group_slug/': 'posts/group_list.html',
    '/profile/hanson/': 'posts/profile.html',
    '/posts/1/': 'posts/post_detail.html',
}
OnlyAuthorisedURLs = {
    '/create/': 'posts/create_post.html',
}
OnlyAuthorURLs = {
    '/posts/1/edit/': 'posts/create_post.html',
}
UnexistingURLs = {
    '/unexisting_page': '',
}


class DynamicURLTests(TestCase):
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
        Post.objects.create(
            author=User.objects.get(username='hanson'),
            text='тут текст гениального поста про стенс'
        )

    def setUp(self):
        self.guest_client = Client()
        self.user_reader = User.objects.get(username='tom')
        self.authorized_user_reader = Client()
        self.authorized_user_reader.force_login(self.user_reader)
        self.user_author = User.objects.get(username='hanson')
        self.authorized_user_author = Client()
        self.authorized_user_author.force_login(self.user_author)

    def test_urls_exist_at_desired_location(self):
        '''Проверка доступности страниц с учётом прав'''
        test_sessions = [
            ('неавторизованный пользователь на общедоступных страницах',
                self.guest_client,
                CommonURLs,
                200),
            ('неавторизованный пользователь на страницах для авторизованных',
                self.guest_client,
                OnlyAuthorisedURLs,
                302),
            ('неавторизованный пользователь пытается что-то сделать '
                'с чужим постом',
                self.guest_client,
                OnlyAuthorURLs,
                302),
            ('неавторизованный пользователь на несуществующей странице ',
                self.guest_client,
                UnexistingURLs,
                404),
            ('авторизованный пользователь на общедоступных страницах',
                self.authorized_user_reader,
                CommonURLs,
                200),
            ('авторизованный пользователь на страницах для авторизованных',
                self.authorized_user_reader,
                OnlyAuthorisedURLs,
                200),
            ('авторизованный пользователь пытается что-то сделать '
                'с чужим постом',
                self.authorized_user_reader,
                OnlyAuthorURLs,
                302),
            ('авторизованный пользователь на несуществующей странице ',
                self.authorized_user_reader,
                UnexistingURLs,
                404),
            ('авторизованный пользователь пытается что-то сделать '
                'со своим постом',
                self.authorized_user_author,
                OnlyAuthorURLs,
                200),
        ]
        for test_case, user, pages, code in test_sessions:
            for address in pages:
                with self.subTest(address=address):
                    self.assertEqual(
                        user.get(address).status_code,
                        code,
                        f'Сценарий /{test_case}/ не проходит на'
                        f'странице {address}'
                    )

    def test_pages_uses_correct_template(self):
        '''Проверяем, что страницы используют правильный шаблон'''
        test_sessions = [
            CommonURLs,
            OnlyAuthorisedURLs,
            OnlyAuthorURLs
        ]
        for session in test_sessions:
            for address, template in session.items():
                with self.subTest(address=address):
                    response = self.authorized_user_author.get(address)
                    self.assertTemplateUsed(response, template)
