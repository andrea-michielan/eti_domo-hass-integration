"""Component to interface with switches that can be controlled remotely."""
import logging

from homeassistant.components.switch import ENTITY_ID_FORMAT, SwitchDevice

from eti_domo import Domo, ServerNotFound

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up a config entry."""

    # Get the Domo object
    hub = hass.data[DOMAIN]["hub"]
    # Retrieve the list of relays
    relays = hub.list_request(Domo.available_commands['relays'])['array']

    # Add all the relays
    async_add_entities(Relay(hub, relay) for relay in relays)


#async def async_unload_entry(hass, entry):
#    """Unload a config entry."""
#    return await hass.data[DOMAIN].async_unload_entry(entry)


class Relay(SwitchDevice):
    """Representation of a switch."""

    def __init__(self, hub: Domo, relay):
        """Init switch device."""
        self.entity_id = "switch." + relay['name'].lower().replace(" ", "_") + "_" + str(relay['act_id'])
        self._name = relay['name']
        self._id = relay['act_id']
        self._hub = hub
        self._status = relay['status']

    @property
    def unique_id(self):
        """Return unique ID for this device."""
        return self.entity_id

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self._status
        

    def update(self):
        """Fetch new state data for this relay.
        This is the only method that should fetch new data for Home Assistant.
        """

        # Send a keep alive request
        self._hub.keep_alive()
        
        # Retrieve the list of relays
        relays = self._hub.list_request(Domo.available_commands['relays'])['array']

        # Search for the relay
        for relay in relays:
            if relay['act_id'] == self._id:
                # update the status
                self._status = relay['status']

    def turn_on(self, **kwargs):
        """Turn the switch on."""

        # Send a keep alive request
        self._hub.keep_alive()

        # Turn on the light
        self._hub.switch(self._id, status=True, is_light=False)

        # Update the status
        self.update()

    def turn_off(self, **kwargs):
        """Turn the device off."""

        # Send a keep alive request
        self._hub.keep_alive()

        # Turn on the light
        self._hub.switch(self._id, status=False, is_light=False)

        # Update the status
        self.update()
