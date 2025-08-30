from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from .models import Job, JobType, JobStatus, JobPriority


class JobModelTest(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create job types, statuses, and priorities
        self.job_type = JobType.objects.create(
            name='Test Type',
            description='Test job type'
        )
        
        self.status = JobStatus.objects.create(
            name='Pending',
            color='#ffc107'
        )
        
        self.priority = JobPriority.objects.create(
            name='High',
            level=3,
            color='#dc3545'
        )
        
        # Create test job
        self.job = Job.objects.create(
            title='Test Job',
            description='Test job description',
            job_type=self.job_type,
            status=self.status,
            priority=self.priority,
            created_by=self.user,
            assigned_to=self.user
        )

    def test_job_creation(self):
        """Test that a job can be created successfully"""
        self.assertEqual(self.job.title, 'Test Job')
        self.assertEqual(self.job.job_code[:3], 'JOB')
        self.assertEqual(self.job.created_by, self.user)
        self.assertEqual(self.job.assigned_to, self.user)

    def test_job_code_generation(self):
        """Test that job codes are generated automatically"""
        self.assertTrue(self.job.job_code)
        self.assertTrue(len(self.job.job_code) > 10)

    def test_job_overdue_property(self):
        """Test the is_overdue property"""
        # Job with past due date should be overdue
        self.job.due_date = timezone.now() - timedelta(days=1)
        self.job.save()
        self.assertTrue(self.job.is_overdue)
        
        # Job with future due date should not be overdue
        self.job.due_date = timezone.now() + timedelta(days=1)
        self.job.save()
        self.assertFalse(self.job.is_overdue)

    def test_job_progress_percentage(self):
        """Test the progress_percentage property"""
        # Test different statuses
        completed_status = JobStatus.objects.create(name='Completed', color='#28a745')
        self.job.status = completed_status
        self.job.save()
        self.assertEqual(self.job.progress_percentage, 100)

    def test_job_duration_calculation(self):
        """Test duration calculation"""
        self.job.started_at = timezone.now()
        self.job.completed_at = timezone.now() + timedelta(hours=2)
        self.job.save()
        
        duration = self.job.duration
        self.assertIsNotNone(duration)
        self.assertAlmostEqual(duration, 2.0, places=1)


class JobViewTest(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create job types, statuses, and priorities
        self.job_type = JobType.objects.create(name='Test Type')
        self.status = JobStatus.objects.create(name='Pending', color='#ffc107')
        self.priority = JobPriority.objects.create(name='High', level=3, color='#dc3545')
        
        # Create test job
        self.job = Job.objects.create(
            title='Test Job',
            description='Test job description',
            job_type=self.job_type,
            status=self.status,
            priority=self.priority,
            created_by=self.user,
            assigned_to=self.user
        )
        
        # Create client
        self.client = Client()

    def test_job_list_view(self):
        """Test job list view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('job:job_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Job')
        self.assertContains(response, self.job.job_code)

    def test_job_detail_view(self):
        """Test job detail view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('job:job_detail', args=[self.job.pk]))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Job')
        self.assertContains(response, self.job.job_code)

    def test_job_create_view(self):
        """Test job create view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('job:job_create'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create New Job')

    def test_job_update_view(self):
        """Test job update view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('job:job_update', args=[self.job.pk]))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit Job')

    def test_job_delete_view(self):
        """Test job delete view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('job:job_delete', args=[self.job.pk]))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Confirm Delete')

    def test_job_dashboard_view(self):
        """Test job dashboard view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('job:job_dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Job Dashboard')

    def test_unauthorized_access(self):
        """Test that unauthorized users are redirected to login"""
        response = self.client.get(reverse('job:job_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login


class JobFormTest(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create job types, statuses, and priorities
        self.job_type = JobType.objects.create(name='Test Type')
        self.status = JobStatus.objects.create(name='Pending', color='#ffc107')
        self.priority = JobPriority.objects.create(name='High', level=3, color='#dc3545')

    def test_job_form_valid(self):
        """Test that job form is valid with correct data"""
        from .forms import JobForm
        
        form_data = {
            'title': 'Test Job',
            'description': 'Test job description',
            'job_type': self.job_type.pk,
            'status': self.status.pk,
            'priority': self.priority.pk,
            'assigned_to': self.user.pk,
        }
        
        form = JobForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_job_form_invalid(self):
        """Test that job form is invalid with missing required fields"""
        from .forms import JobForm
        
        form_data = {
            'title': '',  # Missing required field
            'description': 'Test job description',
        }
        
        form = JobForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_job_search_form(self):
        """Test job search form"""
        from .forms import JobSearchForm
        
        form_data = {
            'search_term': 'test',
            'search_field': 'title',
            'job_type': self.job_type.pk,
        }
        
        form = JobSearchForm(data=form_data)
        self.assertTrue(form.is_valid())


class JobURLTest(TestCase):
    def test_job_urls(self):
        """Test that job URLs resolve correctly"""
        from django.urls import reverse
        
        # Test job list URL
        url = reverse('job:job_list')
        self.assertEqual(url, '/job/')
        
        # Test job create URL
        url = reverse('job:job_create')
        self.assertEqual(url, '/job/create/')
        
        # Test job dashboard URL
        url = reverse('job:job_dashboard')
        self.assertEqual(url, '/job/dashboard/')
        
        # Test job detail URL
        url = reverse('job:job_detail', args=[1])
        self.assertEqual(url, '/job/1/')
        
        # Test job update URL
        url = reverse('job:job_update', args=[1])
        self.assertEqual(url, '/job/1/edit/')
        
        # Test job delete URL
        url = reverse('job:job_delete', args=[1])
        self.assertEqual(url, '/job/1/delete/')


class JobAdminTest(TestCase):
    def setUp(self):
        # Create superuser
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123'
        )
        
        # Create job types, statuses, and priorities
        self.job_type = JobType.objects.create(name='Test Type')
        self.status = JobStatus.objects.create(name='Pending', color='#ffc107')
        self.priority = JobPriority.objects.create(name='High', level=3, color='#dc3545')
        
        # Create test job
        self.job = Job.objects.create(
            title='Test Job',
            description='Test job description',
            job_type=self.job_type,
            status=self.status,
            priority=self.priority,
            created_by=self.admin_user,
            assigned_to=self.admin_user
        )

    def test_job_admin_list_display(self):
        """Test that job admin displays correctly"""
        from django.contrib.admin.sites import site
        from .admin import JobAdmin
        
        admin = JobAdmin(Job, site)
        self.assertIn('job_code', admin.list_display)
        self.assertIn('title', admin.list_display)
        self.assertIn('status', admin.list_display)

    def test_job_type_admin(self):
        """Test job type admin"""
        from django.contrib.admin.sites import site
        from .admin import JobTypeAdmin
        
        admin = JobTypeAdmin(JobType, site)
        self.assertIn('name', admin.list_display)
        self.assertIn('is_active', admin.list_display) 