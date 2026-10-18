import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import Poll, Option, VoteLog

User = get_user_model()


class UserModelTest(TestCase):
    def test_create_user_with_unique_email(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpassword123'))
        self.assertEqual(str(user), '@testuser')


class AuthViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='validpassword123'
        )

    def test_index_page_loads(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Krarsızım')

    def test_register_get(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Aramıza Katıl')

    def test_register_success(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'supersecretpass123',
            'password2': 'supersecretpass123',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        self.assertEqual(int(response.context['user'].id), User.objects.get(username='newuser').id)

    def test_register_duplicate_email(self):
        response = self.client.post(reverse('register'), {
            'username': 'anotheruser',
            'email': 'existing@example.com',
            'password1': 'supersecretpass123',
            'password2': 'supersecretpass123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='anotheruser').exists())
        self.assertFormError(response.context['form'], 'email', 'Bu e-posta adresi ile zaten kayıtlı bir hesap var.')

    def test_login_success(self):
        response = self.client.post(reverse('login'), {
            'username': 'existinguser',
            'password': 'validpassword123',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)

    def test_login_invalid_password(self):
        response = self.client.post(reverse('login'), {
            'username': 'existinguser',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)

    def test_logout(self):
        self.client.login(username='existinguser', password='validpassword123')
        response = self.client.get(reverse('logout'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)


class PollModelsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='pollauthor',
            email='author@example.com',
            password='authorpass123'
        )
        self.poll = Poll.objects.create(
            author=self.user,
            question='Hangi kahveyi içmeliyim?'
        )
        self.opt1 = Option.objects.create(poll=self.poll, text='Espresso', vote_count=3)
        self.opt2 = Option.objects.create(poll=self.poll, text='Latte', vote_count=7)

    def test_poll_and_options_creation(self):
        self.assertEqual(self.poll.question, 'Hangi kahveyi içmeliyim?')
        self.assertEqual(self.poll.author, self.user)
        self.assertEqual(self.poll.options.count(), 2)
        self.assertEqual(self.poll.total_votes, 10)

    def test_option_percentage(self):
        self.assertEqual(self.opt1.get_percentage(), 30.0)
        self.assertEqual(self.opt2.get_percentage(), 70.0)

    def test_votelog_creation(self):
        votelog = VoteLog.objects.create(
            poll=self.poll,
            option=self.opt1,
            user=self.user,
            session_key='session_xyz'
        )
        self.assertEqual(votelog.poll, self.poll)
        self.assertEqual(votelog.option, self.opt1)
        self.assertEqual(votelog.user, self.user)
        self.assertEqual(votelog.session_key, 'session_xyz')


class PollCreateViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='creator',
            email='creator@example.com',
            password='creatorpass123'
        )

    def test_poll_create_requires_login(self):
        response = self.client.get(reverse('poll_create'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_poll_create_get_authenticated(self):
        self.client.login(username='creator', password='creatorpass123')
        response = self.client.get(reverse('poll_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Yeni Anket Oluştur')

    def test_poll_create_success_with_two_options(self):
        self.client.login(username='creator', password='creatorpass123')
        response = self.client.post(reverse('poll_create'), {
            'question': 'Sinemaya mı gitsem tiyatroya mı?',
            'options': ['Sinema', 'Tiyatro']
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Poll.objects.filter(question='Sinemaya mı gitsem tiyatroya mı?').exists())
        poll = Poll.objects.get(question='Sinemaya mı gitsem tiyatroya mı?')
        self.assertEqual(poll.author, self.user)
        self.assertEqual(poll.options.count(), 2)
        self.assertEqual(set(poll.options.values_list('text', flat=True)), {'Sinema', 'Tiyatro'})

    def test_poll_create_success_with_five_options(self):
        self.client.login(username='creator', password='creatorpass123')
        options = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma']
        response = self.client.post(reverse('poll_create'), {
            'question': 'Buluşma için en uygun gün hangisi?',
            'options': options
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        poll = Poll.objects.get(question='Buluşma için en uygun gün hangisi?')
        self.assertEqual(poll.options.count(), 5)

    def test_poll_create_fails_with_one_option(self):
        self.client.login(username='creator', password='creatorpass123')
        response = self.client.post(reverse('poll_create'), {
            'question': 'Tek seçenekli geçersiz anket sorusu?',
            'options': ['Yalnızca Bir']
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Poll.objects.filter(question='Tek seçenekli geçersiz anket sorusu?').exists())

    def test_poll_create_fails_with_six_options(self):
        self.client.login(username='creator', password='creatorpass123')
        options = ['Opt1', 'Opt2', 'Opt3', 'Opt4', 'Opt5', 'Opt6']
        response = self.client.post(reverse('poll_create'), {
            'question': 'Altı seçenekli geçersiz anket?',
            'options': options
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Poll.objects.filter(question='Altı seçenekli geçersiz anket?').exists())

    def test_poll_create_ajax_success(self):
        self.client.login(username='creator', password='creatorpass123')
        response = self.client.post(
            reverse('poll_create'),
            {
                'question': 'AJAX ile oluşturulan anket sorusu?',
                'options': ['Seçenek A', 'Seçenek B', 'Seçenek C']
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertIn('poll_id', data)


class PollVoteApiTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.author = User.objects.create_user(
            username='pollmaker',
            email='maker@example.com',
            password='makerpassword123'
        )
        self.voter_user = User.objects.create_user(
            username='voter',
            email='voter@example.com',
            password='voterpassword123'
        )
        self.poll = Poll.objects.create(
            author=self.author,
            question='Hangi rengi seversin?'
        )
        self.opt_blue = Option.objects.create(poll=self.poll, text='Mavi', vote_count=0)
        self.opt_red = Option.objects.create(poll=self.poll, text='Kırmızı', vote_count=0)

    def test_authenticated_user_vote_success(self):
        self.client.login(username='voter', password='voterpassword123')
        url = reverse('poll_vote_api', kwargs={'poll_id': self.poll.id})
        response = self.client.post(
            url,
            data=json.dumps({'option_id': self.opt_blue.id}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('total_votes'), 1)
        self.assertEqual(data.get('user_voted_option_id'), self.opt_blue.id)

        # Check DB
        self.opt_blue.refresh_from_db()
        self.assertEqual(self.opt_blue.vote_count, 1)
        self.assertTrue(VoteLog.objects.filter(poll=self.poll, user=self.voter_user, option=self.opt_blue).exists())

    def test_authenticated_user_duplicate_vote_fails(self):
        self.client.login(username='voter', password='voterpassword123')
        url = reverse('poll_vote_api', kwargs={'poll_id': self.poll.id})
        # First vote
        self.client.post(
            url,
            data=json.dumps({'option_id': self.opt_blue.id}),
            content_type='application/json'
        )
        # Second vote
        response = self.client.post(
            url,
            data=json.dumps({'option_id': self.opt_red.id}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data.get('success'))
        self.assertIn('zaten oy kullandınız', data.get('error'))

        # Check vote counts remained 1
        self.opt_blue.refresh_from_db()
        self.opt_red.refresh_from_db()
        self.assertEqual(self.opt_blue.vote_count, 1)
        self.assertEqual(self.opt_red.vote_count, 0)

    def test_anonymous_guest_vote_success(self):
        guest_client = Client()
        url = reverse('poll_vote_api', kwargs={'poll_id': self.poll.id})
        response = guest_client.post(
            url,
            data=json.dumps({'option_id': self.opt_red.id}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('total_votes'), 1)

        self.opt_red.refresh_from_db()
        self.assertEqual(self.opt_red.vote_count, 1)
        self.assertTrue(VoteLog.objects.filter(poll=self.poll, user=None, option=self.opt_red).exists())

    def test_anonymous_guest_duplicate_vote_fails(self):
        guest_client = Client()
        url = reverse('poll_vote_api', kwargs={'poll_id': self.poll.id})
        # 1st vote
        guest_client.post(
            url,
            data=json.dumps({'option_id': self.opt_red.id}),
            content_type='application/json'
        )
        # 2nd vote with same guest session
        response = guest_client.post(
            url,
            data=json.dumps({'option_id': self.opt_blue.id}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data.get('success'))
        self.assertIn('zaten oy kullandınız', data.get('error'))

    def test_vote_invalid_option(self):
        url = reverse('poll_vote_api', kwargs={'poll_id': self.poll.id})
        response = self.client.post(
            url,
            data=json.dumps({'option_id': 999999}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data.get('success'))

    def test_vote_option_from_another_poll(self):
        another_poll = Poll.objects.create(author=self.author, question='Başka bir soru?')
        other_opt = Option.objects.create(poll=another_poll, text='Alakasız Seçenek')

        url = reverse('poll_vote_api', kwargs={'poll_id': self.poll.id})
        response = self.client.post(
            url,
            data=json.dumps({'option_id': other_opt.id}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_vote_via_form_data(self):
        url = reverse('poll_vote_api', kwargs={'poll_id': self.poll.id})
        response = self.client.post(url, {'option_id': str(self.opt_blue.id)})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.opt_blue.refresh_from_db()
        self.assertEqual(self.opt_blue.vote_count, 1)

    def test_index_shows_voted_poll_with_results(self):
        self.client.login(username='voter', password='voterpassword123')
        # Vote on poll
        VoteLog.objects.create(
            poll=self.poll,
            option=self.opt_blue,
            user=self.voter_user
        )
        self.opt_blue.vote_count = 1
        self.opt_blue.save()

        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        # Should contain progress bar class and voted badge
        self.assertContains(response, 'poll-result-row')
        self.assertContains(response, 'Senin Oyun')
