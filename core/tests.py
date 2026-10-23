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

    def test_register_duplicate_username(self):
        response = self.client.post(reverse('register'), {
            'username': 'existinguser',
            'email': 'uniquemail@example.com',
            'password1': 'supersecretpass123',
            'password2': 'supersecretpass123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'username', 'Bu kullanıcı adında bir kullanıcı zaten mevcut.')

    def test_register_integrity_error_handles_race_condition(self):
        from unittest.mock import patch
        from django.db import IntegrityError

        # Simulate race condition: form.is_valid passes, but concurrently created user raises IntegrityError during save
        def fake_save(self_form):
            User.objects.create_user(username='concurrentuser', email='concurrent@example.com', password='validpassword123')
            raise IntegrityError('duplicate key value violates unique constraint')

        with patch('core.forms.RegisterForm.save', side_effect=fake_save, autospec=True):
            response = self.client.post(reverse('register'), {
                'username': 'concurrentuser',
                'email': 'concurrent@example.com',
                'password1': 'validpassword123',
                'password2': 'validpassword123',
            }, follow=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context['user'].is_authenticated)
            self.assertEqual(response.context['user'].username, 'concurrentuser')

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


class PollExpirationAndAuthorActionsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.author = User.objects.create_user(
            username='pollauthor2',
            email='author2@example.com',
            password='password123'
        )
        self.other_user = User.objects.create_user(
            username='stranger',
            email='stranger@example.com',
            password='password123'
        )
        self.poll = Poll.objects.create(
            author=self.author,
            question='Hangi kahveyi içmeliyim?'
        )
        self.opt1 = Option.objects.create(poll=self.poll, text='Türk Kahvesi')
        self.opt2 = Option.objects.create(poll=self.poll, text='Filtre Kahve')

    def test_poll_duration_calculation_on_create(self):
        self.client.login(username='pollauthor2', password='password123')
        # Create with 1h duration
        response = self.client.post(reverse('poll_create'), {
            'question': '1 saatlik acil anket sorusu?',
            'options': ['Evet', 'Hayır'],
            'duration': '1h',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        p1 = Poll.objects.get(question='1 saatlik acil anket sorusu?')
        self.assertIsNotNone(p1.expires_at)
        self.assertFalse(p1.is_closed)

        # Create with 'never' duration
        response = self.client.post(reverse('poll_create'), {
            'question': 'Süresiz açık kalacak soru?',
            'options': ['A', 'B'],
            'duration': 'never',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        p2 = Poll.objects.get(question='Süresiz açık kalacak soru?')
        self.assertIsNone(p2.expires_at)

    def test_poll_auto_close_when_expired(self):
        from django.utils import timezone
        from datetime import timedelta

        # Set expiration in the past
        self.poll.expires_at = timezone.now() - timedelta(minutes=5)
        self.poll.save()
        self.assertTrue(self.poll.is_closed)

        # Voting on expired poll must fail
        url = reverse('poll_vote_api', kwargs={'poll_id': self.poll.id})
        response = self.client.post(
            url,
            data=json.dumps({'option_id': self.opt1.id}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data.get('success'))
        self.assertIn('kapatılmıştır', data.get('error'))

    def test_author_can_toggle_poll_status(self):
        self.client.login(username='pollauthor2', password='password123')
        url = reverse('poll_toggle_status', kwargs={'poll_id': self.poll.id})
        
        # Close poll
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.poll.refresh_from_db()
        self.assertFalse(self.poll.is_active)
        self.assertTrue(self.poll.is_closed)

        # Reopen poll
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.poll.refresh_from_db()
        self.assertTrue(self.poll.is_active)

    def test_non_author_cannot_toggle_poll_status(self):
        self.client.login(username='stranger', password='password123')
        url = reverse('poll_toggle_status', kwargs={'poll_id': self.poll.id})
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 403)
        self.poll.refresh_from_db()
        self.assertTrue(self.poll.is_active)

    def test_author_can_delete_poll(self):
        self.client.login(username='pollauthor2', password='password123')
        url = reverse('poll_delete', kwargs={'poll_id': self.poll.id})
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Poll.objects.filter(id=self.poll.id).exists())
        self.assertFalse(Option.objects.filter(poll_id=self.poll.id).exists())

    def test_non_author_cannot_delete_poll(self):
        self.client.login(username='stranger', password='password123')
        url = reverse('poll_delete', kwargs={'poll_id': self.poll.id})
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Poll.objects.filter(id=self.poll.id).exists())

    def test_anonymous_vote_persists_across_signup_and_logout(self):
        # 1. Anonymous visitor visits site and votes
        guest_client = Client()
        vote_url = reverse('poll_vote_api', kwargs={'poll_id': self.poll.id})
        vote_resp = guest_client.post(
            vote_url,
            data=json.dumps({'option_id': self.opt1.id}),
            content_type='application/json'
        )
        self.assertEqual(vote_resp.status_code, 200)
        self.assertEqual(self.opt1.poll.total_votes, 1)

        # Ensure voter token cookie was set
        self.assertIn('krarsizim_voter_token', guest_client.cookies)
        voter_token = guest_client.cookies['krarsizim_voter_token'].value

        # 2. Anonymous visitor registers an account
        reg_resp = guest_client.post(reverse('register'), {
            'username': 'converted_user',
            'email': 'converted@example.com',
            'password1': 'mypassword123',
            'password2': 'mypassword123',
        }, follow=True)
        self.assertEqual(reg_resp.status_code, 200)

        # Check VoteLog was migrated to converted_user
        converted_user = User.objects.get(username='converted_user')
        log = VoteLog.objects.get(poll=self.poll)
        self.assertEqual(log.user, converted_user)
        self.assertEqual(log.voter_token, voter_token)

        # 3. User logs out
        logout_resp = guest_client.get(reverse('logout'), follow=True)
        self.assertEqual(logout_resp.status_code, 200)
        self.assertFalse(logout_resp.context['user'].is_authenticated)

        # 4. Same client (now logged out) tries to vote AGAIN on the same poll
        duplicate_vote_resp = guest_client.post(
            vote_url,
            data=json.dumps({'option_id': self.opt2.id}),
            content_type='application/json'
        )
        self.assertEqual(duplicate_vote_resp.status_code, 400)
        data = duplicate_vote_resp.json()
        self.assertFalse(data.get('success'))
        self.assertIn('zaten oy kullandınız', data.get('error'))

        # Total votes must remain 1
        self.opt1.refresh_from_db()
        self.opt2.refresh_from_db()
        self.assertEqual(self.opt1.vote_count, 1)
        self.assertEqual(self.opt2.vote_count, 0)

    def test_newly_registered_user_can_vote_on_existing_polls(self):
        # 1. Existing vote from another user
        User.objects.create_user(username='first_user', email='first@example.com', password='password123')
        VoteLog.objects.create(poll=self.poll, option=self.opt1, voter_token='device_token_xyz')
        self.opt1.vote_count = 1
        self.opt1.save()

        # 2. A brand new user registers on a client that has device_token_xyz cookie
        client = Client()
        client.cookies['krarsizim_voter_token'] = 'device_token_xyz'
        reg_resp = client.post(reverse('register'), {
            'username': 'fresh_user',
            'email': 'fresh@example.com',
            'password1': 'mypassword123',
            'password2': 'mypassword123',
        }, follow=True)
        self.assertEqual(reg_resp.status_code, 200)

        # 3. Check home page: new user must NOT see this poll as already voted
        index_resp = client.get(reverse('index'))
        self.assertEqual(index_resp.status_code, 200)
        found_poll = None
        for item in index_resp.context['poll_data']:
            if item['poll'].id == self.poll.id:
                found_poll = item
                break
        self.assertIsNotNone(found_poll)
        self.assertFalse(found_poll['has_voted'])

        # 4. New user votes on the poll
        vote_url = reverse('poll_vote_api', kwargs={'poll_id': self.poll.id})
        vote_resp = client.post(
            vote_url,
            data=json.dumps({'option_id': self.opt2.id}),
            content_type='application/json'
        )
        self.assertEqual(vote_resp.status_code, 200)
        self.assertTrue(vote_resp.json().get('success'))

        self.opt2.refresh_from_db()
        self.assertEqual(self.opt2.vote_count, 1)

    def test_multiple_users_on_same_device_can_each_vote(self):
        client = Client()
        client.cookies['krarsizim_voter_token'] = 'shared_device_token'

        # User 1 registers and votes
        client.post(reverse('register'), {
            'username': 'device_user1',
            'email': 'du1@example.com',
            'password1': 'password123',
            'password2': 'password123',
        })
        vote_url = reverse('poll_vote_api', kwargs={'poll_id': self.poll.id})
        resp1 = client.post(vote_url, data=json.dumps({'option_id': self.opt1.id}), content_type='application/json')
        self.assertEqual(resp1.status_code, 200)

        # User 1 logs out
        client.get(reverse('logout'))

        # User 2 logs in on the SAME device
        User.objects.create_user(username='device_user2', email='du2@example.com', password='password123')
        client.post(reverse('login'), {'username': 'device_user2', 'password': 'password123'})

        # User 2 CAN vote on the same poll
        resp2 = client.post(vote_url, data=json.dumps({'option_id': self.opt2.id}), content_type='application/json')
        self.assertEqual(resp2.status_code, 200)
        self.assertTrue(resp2.json().get('success'))

        # But User 2 cannot vote a SECOND time
        resp3 = client.post(vote_url, data=json.dumps({'option_id': self.opt2.id}), content_type='application/json')
        self.assertEqual(resp3.status_code, 400)

