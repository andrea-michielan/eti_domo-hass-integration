"""Platform for light integration."""
import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
# Import the device class from the component that you want to support
from homeassistant.components.light import Light

from homeassistant.helpers.entity import Entity

from eti_domo import Domo, ServerNotFound

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Awesome Light platform."""
    pass

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Hue lights from a config entry."""

    # Get the Domo object
    hub = hass.data[DOMAIN]["hub"]

    # Retrieve all the lights from the eti/domo server
    floors = hub.list_request(Domo.available_commands['lights'])['array']

    # Create a list of lights
    lights = []
    
    # Fetch the lights inside the floors and rooms
    for floor in floors:
        for room in floor['array']:
            for item in room['array']:
                lights.append([item, floor['name'], room['name']])

    # Add all the lights as entities
    async_add_entities(CameLight(light[0], light[1], light[2],  hub) for light in lights)

class CameLight(Light):
    """Representation of an Awesome Light."""

    def __init__(self, light: dict, floor_name: str, room_name: str, hub: Domo):
        """Initialize an AwesomeLight."""
        self.entity_id = "light." + floor_name.lower().replace(" ", "_") + "_" + light['name'].lower().replace(" ", "_").replace(".", "") + "_" + str(light['act_id'])
        self._id = light['act_id']
        self._name = light['name']
        self._state = light['status']
        self._floor_ind = light['floor_ind']
        self._room_ind = light['room_ind']
        self._hub = hub

    @property
    def unique_id(self):
        """Return unique ID for this device."""
        return self.entity_id

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

    @property
    def hub(self):
        """Return the hub object"""
        return self._hub

    @property
    def id(self):
        """Return the id of the light"""
        return self._id

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._state

    @property
    def floor_ind(self):
        """Return the index of the floor that contains the light"""
        return self._floor_ind

    @property
    def room_ind(self):
        """Return the index of the room that contains the light"""
        return self._room_ind

    def turn_on(self):
        """Instruct the light to turn on.
        You can skip the brightness part if your light does not support
        brightness control.
        """

        # Send a keep alive request
        self._hub.keep_alive()

        # Turn on the light
        self._hub.switch(self._id, status=True, is_light=True)

        # Update the status
        self.update()

    def turn_off(self):
        """Instruct the light to turn off."""

        # Send a keep alive request
        self._hub.keep_alive()
        # Turn off the light
        self._hub.switch(self._id, status=False, is_light=True)

        # Update the status
        self.update()

    def update(self):
        """Fetch new state data for this light.
        This is the only method that should fetch new data for Home Assistant.
        """

        # Send a keep alive request
        self._hub.keep_alive()

        # Update the light info
        floors = self._hub.list_request(Domo.available_commands['lights'])['array']

        # Search for the light
        for floor in floors:
            if floor['floor_ind'] == self._floor_ind:
                for room in floor['array']:
                    if room['room_ind'] == self._room_ind:
                        for light in room['array']:
                            if light['act_id'] == self._id:
                                # Light found, updating the status
                                self._state = light['status']

        