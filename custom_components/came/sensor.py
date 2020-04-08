"""Platform for light integration."""
import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv

from homeassistant.const import DEVICE_CLASS_HUMIDITY, UNIT_PERCENTAGE

from homeassistant.helpers.entity import Entity

from eti_domo import Domo, ServerNotFound

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Hue lights from a config entry."""

    # Get the Domo object
    hub = hass.data[DOMAIN]["hub"]

    # Retrieve all the sensors from the eti/domo server
    analogs = hub.list_request(Domo.available_commands['analogin'])['array']

    # Add all the lights as entities
    async_add_entities(CameHygrometer(hub, sensor) for sensor in analogs)

class CameHygrometer(Entity):
    """Representation of XBee Pro temperature sensor."""

    def __init__(self, hub: Domo, sensor):
        """Init switch device."""
        self.entity_id = "sensor." + sensor['name'].lower().replace(" ", "_") + "_" + str(sensor['act_id'])
        self._name = sensor['name']
        self._id = sensor['act_id']
        self._hub = hub
        self._value = sensor['value']
        self._unit_of_measurement = sensor['unit']

    @property
    def unique_id(self):
        """Return unique ID for this device."""
        return self.entity_id

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor. (current value)"""
        return self._value

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement the value is expressed in."""
        return self._unit_of_measurement

    def update(self):
        """Get the latest data."""

        # Send a keep alive request
        self._hub.keep_alive()

        # Retrieve all the sensors from the eti/domo server
        analogs = self._hub.list_request(Domo.available_commands['analogin'])['array']

        # Search for the sensor
        for sensor in analogs:
            if sensor['act_id'] == self._id:
                # update the value
                self._value = sensor['value']

