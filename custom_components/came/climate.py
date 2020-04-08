"""Platform for light integration."""
import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv

from homeassistant.components.climate.const import (
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_FAN_MODE,
    SUPPORT_TARGET_TEMPERATURE,
    DEFAULT_MIN_TEMP,
    DEFAULT_MAX_TEMP
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    PRECISION_TENTHS,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)

from homeassistant.helpers.entity import Entity
from homeassistant.components.climate import ClimateDevice
from typing import Any, Dict, List, Optional

from eti_domo import Domo, ServerNotFound

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Hue lights from a config entry."""

    # Get the Domo object
    hub = hass.data[DOMAIN]["hub"]

    # Retrieve all the thermo regulation from the eti/domo server
    thermos = hub.list_request(Domo.available_commands['thermoregulation'])['array']

    # Add all the devices as entities
    async_add_entities(CameClimate(hub, climate) for climate in thermos)

class CameClimate(ClimateDevice):
    """Representation of XBee Pro temperature sensor."""

    def __init__(self, hub: Domo, climate):
        """Init switch device."""
        self.entity_id = "climate." + climate['name'].lower().replace(" ", "_") + "_" + str(climate['act_id'])
        self._name = climate['name']
        self._id = climate['act_id']
        self._hub = hub
        self._status = climate['status']
        self._temp = float(climate['temp']) / 10.0
        self._mode = climate['mode']
        self._set_point = float(climate['set_point']) / 10.0
        self._season = climate['season']

        # check if the thermo zone has a hygrometer
        if 'hygro' in climate:
            self._humidity = climate['hygro']
        else:
            self._humidity = None

    @property
    def unique_id(self):
        """Return unique ID for this device."""
        return self.entity_id

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    def update(self):
        """Get the latest data."""

        # Send a keep alive request
        self._hub.keep_alive()

        # Retrieve all the sensors from the eti/domo server
        thermos = self._hub.list_request(Domo.available_commands['thermoregulation'])['array']

        # Search for the sensor
        for climate in thermos:
            if climate['act_id'] == self._id:
                # update the value
                self._status = climate['status']
                self._temp = float(climate['temp']) / 10.0
                self._mode = climate['mode']
                self._set_point = float(climate['set_point']) / 10.0
                self._season = climate['season']
                # check if the thermo zone has a hygrometer
                if 'hygro' in climate:
                    self._humidity = climate['hygro']
                else:
                    self._humidity = None

    @property
    def precision(self) -> float:
        """Return the precision of the system."""
        return PRECISION_TENTHS

    @property
    def temperature_unit(self) -> str:
        """Return the unit of measurement used by the platform."""
        return TEMP_CELSIUS

    @property
    def current_humidity(self) -> Optional[int]:
        """Return the current humidity."""
        return self._humidity

    @property
    def hvac_mode(self) -> str:
        """Return current hvac operation ie. heat, cool mode.

        Need to be one of HVAC_MODE_*.
        """
        return Domo.thermo_status[self._mode]

    @property
    def hvac_modes(self) -> List[str]:
        """Return the list of available hvac operation modes.

        Need to be a subset of HVAC_MODES.
        """
        return [HVAC_MODE_OFF, HVAC_MODE_AUTO, HVAC_MODE_COOL, HVAC_MODE_HEAT]


    @property
    def hvac_action(self) -> Optional[str]:
        """Return the current running hvac operation if supported.

        Need to be one of CURRENT_HVAC_*.
        """
        return None

    @property
    def current_temperature(self) -> Optional[float]:
        """Return the current temperature."""
        return self._temp

    @property
    def target_temperature(self) -> Optional[float]:
        """Return the temperature we try to reach."""
        return self._set_point

    @property
    def target_temperature_step(self) -> Optional[float]:
        """Return the supported step of target temperature."""
        return 0.1

    @property
    def target_temperature_high(self) -> Optional[float]:
        """Return the highbound target temperature we try to reach.

        Requires SUPPORT_TARGET_TEMPERATURE_RANGE.
        """
        return 35.0

    @property
    def target_temperature_low(self) -> Optional[float]:
        """Return the lowbound target temperature we try to reach.

        Requires SUPPORT_TARGET_TEMPERATURE_RANGE.
        """
        raise 5.0

    def set_temperature(self, **kwargs) -> None:
        """Set new target temperature."""
        if ATTR_TEMPERATURE in kwargs:
            self._hub.thermo_mode(self._id, self._mode, kwargs[ATTR_TEMPERATURE])

        # update infos about the climate device
        self.update()

    def set_hvac_mode(self, hvac_mode: str) -> None:
        """Set new target hvac mode."""
        
        # Check if there is a need to change season
        if hvac_mode == HVAC_MODE_COOL:
            # change season if necessary
            if not self._season == "summer":
                self._hub.change_season(Domo.seasons["summer"])
            # Turn on the heater
            self.turn_on()
        elif hvac_mode == HVAC_MODE_HEAT:
            # change season if necessary
            if not self._season == "winter":
                self._hub.change_season(Domo.seasons["winter"])
            # Turn on the heater
            self.turn_on()
        else:
            # default to auto
            value = 2
            # Check if it is to be set to auto or off
            if hvac_mode == HVAC_MODE_AUTO:
                value = 2
            elif hvac_mode == HVAC_MODE_OFF:
                value = 0
            # change mode
            self._hub.thermo_mode(self._id, value, self._set_point)

        # update infos about the climate device
        self.update()

    def turn_on(self) -> None:
        """Turn the entity on."""
        
        # Send a keep alive request
        self._hub.keep_alive()

        # Turn on the climate
        self._hub.thermo_mode(self._id, 1, self._set_point)

        # update infos about the climate device
        self.update()

    def turn_off(self) -> None:
        """Turn the entity off."""

        # Send a keep alive request
        self._hub.keep_alive()

        # Turn off the climate with default 20 degrees celsius
        self._hub.thermo_mode(self._id, 0, self._set_point)

        # update infos about the climate device
        self.update()

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        return SUPPORT_TARGET_TEMPERATURE

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        return DEFAULT_MIN_TEMP

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        return DEFAULT_MAX_TEMP

