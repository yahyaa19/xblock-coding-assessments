"""Compatibility layer for Open edX."""

from typing import Any

from django.conf import settings


def _get_current_site_configuration_value(key: str, default: Any = None) -> Any:  # pragma: no cover
    """
    Get value from the current site configuration.

    Args:
        key: The key to retrieve from the site configuration.
        default: The default value to return if the key is not found.
    Returns:
        The value associated with the key, or the default value.
    """
    # pylint: disable=import-error,import-outside-toplevel
    from openedx.core.djangoapps.site_configuration.helpers import get_value

    return get_value(key, default)


def _get_site_configuration_value(domain: str, key: str, default: Any = None) -> Any:  # pragma: no cover
    """
    Get value from the site configuration for a given domain.

    Args:
        domain: The domain to retrieve site configuration for.
        key: The key to retrieve from the site configuration.
        default: The default value to return if the key is not found.

    Returns:
        The value associated with the key, or the default value.
    """
    # pylint: disable=import-error,import-outside-toplevel
    from openedx.core.djangoapps.site_configuration.models import SiteConfiguration

    try:
        config = SiteConfiguration.objects.get(site__domain=domain).site_values
        return config.get(key, default)
    except SiteConfiguration.DoesNotExist:
        return default


def get_site_configuration_api_key(block_settings_key: str, api_key_name: str) -> str | None:
    """
    Retrieve API key from site configuration based on execution context.

    In Open edX, site configurations are defined separately for LMS and CMS (Studio)
    environments. API keys are typically stored in the LMS site configuration.
    This function handles the different contexts:

    In LMS: Get the API key directly from the current site configuration.
    In CMS: Get the API key using LMS site configuration.
        The LMS domain is retrieved from CMS site configuration or Django settings.

    This special handling is necessary because when an XBlock is being edited in Studio,
    it needs to access API keys that are stored in the corresponding LMS site configuration,
    not in the Studio site configuration.

    Args:
        block_settings_key: The key under which block settings are stored.
        api_key_name: Name of the API key to retrieve.

    Returns:
        The API key if found, None otherwise.
    """
    if getattr(settings, "SERVICE_VARIANT", None) == "lms":
        block_config = _get_current_site_configuration_value(block_settings_key, {})
        return block_config.get(api_key_name)

    lms_base = _get_current_site_configuration_value("LMS_BASE", getattr(settings, "LMS_BASE", None))
    block_config = _get_site_configuration_value(lms_base, block_settings_key, {})
    return block_config.get(api_key_name)
