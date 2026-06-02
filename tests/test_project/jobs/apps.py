from django.apps import AppConfig


class JobsConfig(AppConfig):
    """Test-only app exercising the request-driven custom-view escape hatch.

    ``JobAdmin`` overrides ``change_view`` to branch on ``?run_custom=1`` and
    render a hand-rolled template (no ``change_form_template`` attribute), so
    the form-spec resolver must *probe* the view to detect the custom render
    and return the ``html-fragment`` payload the MCP wire surfaces as the
    ``custom-template`` discriminator (#84 / cross-repo fixture)."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "tests.test_project.jobs"
    label = "jobs"
