"""The Came Eti Domo integration."""
import asyncio

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, CONF_HOST, CONF_PASSWORD, CONF_USERNAME

from .config_flow import ConfigFlow

from eti_domo import Domo, ServerNotFound

import logging
_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_HOST): cv.string
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS = ["light", "switch", "sensor", "climate"]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Came Eti Domo component."""

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Came Eti Domo from a config entry."""
    # TODO Store an API object for your platforms to access
    # hass.data[DOMAIN][entry.entry_id] = MyApi(...)

    # create an entry into the hass object
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    # get info from entry 
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    host = entry.data[CONF_HOST]

    # create a new Domo object
    hub = Domo(host)
    # login to the server
    hub.login(username, password)

    # save the session info into the hass object
    hass.data[DOMAIN]["hub"] = hub
    # set up entry id
    hass.data[DOMAIN][entry.entry_id] = hub.id

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop("hub")
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
