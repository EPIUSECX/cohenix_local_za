from za_local import hooks
from za_local.tests.compat import UnitTestCase


class TestSchedulerHookIntegrity(UnitTestCase):
	def test_compliance_jobs_use_supported_long_queue_events(self):
		allowed_events = {
			"all",
			"hourly",
			"hourly_long",
			"daily",
			"daily_long",
			"weekly",
			"weekly_long",
			"monthly",
			"monthly_long",
			"cron",
			"yearly",
			"annual",
		}
		self.assertTrue(set(hooks.scheduler_events).issubset(allowed_events))
		self.assertEqual(
			set(hooks.scheduler_events),
			{"daily_long", "weekly_long", "monthly_long"},
		)

	def test_every_compliance_scheduler_entrypoint_is_registered(self):
		registered = {
			method
			for methods in hooks.scheduler_events.values()
			if isinstance(methods, list)
			for method in methods
		}
		self.assertTrue(
			{
				"za_local.tasks.daily",
				"za_local.tasks.weekly",
				"za_local.tasks.monthly",
				"za_local.tasks.quarterly",
			}.issubset(registered)
		)
