
from __future__ import annotations

import datetime
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import TEMP_CELSIUS, TEMP_CELSIUS, TEMP_FAHRENHEIT, ATTR_TEMPERATURE, CONF_ID
try:
    from homeassistant.components.climate import ClimateEntity
except ImportError:
    from homeassistant.components.climate import ClimateDevice as ClimateEntity
from homeassistant.components.climate.const import (
    SUPPORT_TARGET_TEMPERATURE, SUPPORT_FAN_MODE, SUPPORT_SWING_MODE,
    SUPPORT_PRESET_MODE, PRESET_NONE, PRESET_ECO, PRESET_BOOST)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from msmart.device import air_conditioning as ac

# Local constants
from .const import (
    DOMAIN,
    CONF_PROMPT_TONE,
    CONF_TEMP_STEP,
    CONF_INCLUDE_OFF_AS_STATE,
    CONF_USE_FAN_ONLY_WORKAROUND,
    CONF_KEEP_LAST_KNOWN_ONLINE_STATE
)

_LOGGER = logging.getLogger(__name__)

# Override default scan interval?
SCAN_INTERVAL = datetime.timedelta(seconds=15)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    add_entities: AddEntitiesCallback,
) -> None:
    """Setup the climate platform for Midea Smart AC."""

    _LOGGER.info("Setting up climate platform.")

    # Get config and options data from entry
    config = config_entry.data
    options = config_entry.options

    # Fetch device from global data
    id = config.get(CONF_ID)
    device = hass.data[DOMAIN][id]

    # Query device capabilities
    _LOGGER.info("Querying device capabilities.")
    await hass.async_add_executor_job(device.get_capabilities)

    add_entities([
        MideaClimateACDevice(hass, device, options)
    ])


class MideaClimateACDevice(ClimateEntity):
    """Representation of a Midea climate AC device."""

    def __init__(self, hass, device, options: dict):
        """Initialize the climate device."""

        self.hass = hass
        self._device = device

        # Apply options
        self._device.prompt_tone = options.get(CONF_PROMPT_TONE)
        self._device.keep_last_known_online_state = options.get(
            CONF_KEEP_LAST_KNOWN_ONLINE_STATE)

        # Display on the AC should use the same unit as homeassistant
        self._device.fahrenheit = (
            hass.config.units.temperature_unit == TEMP_FAHRENHEIT)

        self._target_temperature_step = options.get(CONF_TEMP_STEP)
        self._include_off_as_state = options.get(CONF_INCLUDE_OFF_AS_STATE)
        self._use_fan_only_workaround = options.get(
            CONF_USE_FAN_ONLY_WORKAROUND)

        self._operation_list = device.supported_operation_modes
        if self._include_off_as_state:
            self._operation_list.append("off")

        self._fan_list = ac.fan_speed_enum.list()
        self._swing_list = device.supported_swing_modes

        self._changed = False

    async def apply_changes(self) -> None:
        if not self._changed:
            return
        await self.hass.async_add_executor_job(self._device.apply)
        await self.async_update_ha_state()
        self._changed = False

    async def async_update(self) -> None:
        """Retrieve latest state from the appliance if no changes made,
        otherwise update the remote device state."""
        if self._changed:
            await self.hass.async_add_executor_job(self._device.apply)
            self._changed = False
        elif not self._use_fan_only_workaround:
            await self.hass.async_add_executor_job(self._device.refresh)

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added."""
        await super().async_added_to_hass()

        # Populate data ASAP
        await self.async_update()

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {
                (DOMAIN, self._device.id)
            },
            "name": self.name,
            "manufacturer": "Midea",
        }

    @property
    def available(self) -> bool:
        """Checks if the appliance is available for commands."""
        return self._device.online

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        return SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE | SUPPORT_SWING_MODE | SUPPORT_PRESET_MODE

    @property
    def target_temperature_step(self) -> float:
        """Return the supported step of target temperature."""
        return self._target_temperature_step

    @property
    def hvac_modes(self) -> list:
        """Return the list of available operation modes."""
        return self._operation_list

    @property
    def fan_modes(self) -> list:
        """Return the list of available fan modes."""
        return self._fan_list

    @property
    def swing_modes(self) -> list:
        """List of available swing modes."""
        return self._swing_list

    @property
    def assumed_state(self) -> bool:
        """Assume state rather than refresh to workaround fan_only bug."""
        return self._use_fan_only_workaround

    @property
    def should_poll(self) -> bool:
        """Poll the appliance for changes, there is no notification capability in the Midea API"""
        return not self._use_fan_only_workaround

    @property
    def unique_id(self) -> str:
        return f"{self._device.id}"

    @property
    def name(self) -> str:
        """Return the name of the climate device."""
        return f"{DOMAIN}_{self._device.id}"

    @property
    def temperature_unit(self) -> str:
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def current_temperature(self) -> float:
        """Return the current temperature."""
        return self._device.indoor_temperature

    @property
    def target_temperature(self) -> float:
        """Return the temperature we try to reach."""
        return self._device.target_temperature

    @property
    def hvac_mode(self) -> str:
        """Return current operation ie. heat, cool, idle."""
        if self._include_off_as_state and not self._device.power_state:
            return "off"
        return self._device.operational_mode.name

    @property
    def fan_mode(self) -> str:
        """Return the fan setting."""
        return self._device.fan_speed.name

    @property
    def swing_mode(self) -> str:
        """Return the swing setting."""
        return self._device.swing_mode.name

    @property
    def is_on(self) -> bool:
        """Return true if the device is on."""
        return self._device.power_state

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperatures."""
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            # grab temperature from front end UI
            temp = kwargs.get(ATTR_TEMPERATURE)

            # round temperature to nearest .5
            temp = round(temp * 2) / 2

            # send temperature to unit
            self._device.target_temperature = temp
            self._changed = True
            await self.apply_changes()

    async def async_set_swing_mode(self, swing_mode) -> None:
        """Set swing mode."""
        self._device.swing_mode = ac.swing_mode_enum[swing_mode]
        self._changed = True
        await self.apply_changes()

    async def async_set_fan_mode(self, fan_mode) -> None:
        """Set fan mode."""
        """Fix key error when calling from HomeKit"""
        fan_mode = fan_mode.capitalize()
        self._device.fan_speed = ac.fan_speed_enum[fan_mode]
        self._changed = True
        await self.apply_changes()

    async def async_set_hvac_mode(self, hvac_mode) -> None:
        """Set hvac mode."""
        if self._include_off_as_state and hvac_mode == "off":
            self._device.power_state = False
        else:
            if self._include_off_as_state:
                self._device.power_state = True
            self._device.operational_mode = ac.operational_mode_enum[hvac_mode]
        self._changed = True
        await self.apply_changes()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        if preset_mode == PRESET_NONE:
            self._device.eco_mode = False
            self._device.turbo_mode = False
        elif preset_mode == PRESET_BOOST:
            self._device.eco_mode = False
            self._device.turbo_mode = True
        elif preset_mode == PRESET_ECO:
            self._device.turbo_mode = False
            self._device.eco_mode = True

        self._changed = True
        await self.apply_changes()

    @property
    def preset_modes(self) -> list:
        return [PRESET_NONE, PRESET_ECO, PRESET_BOOST]

    @property
    def preset_mode(self) -> str:
        if self._device.eco_mode:
            return PRESET_ECO
        elif self._device.turbo_mode:
            return PRESET_BOOST
        else:
            return PRESET_NONE

    async def async_turn_on(self) -> None:
        """Turn on."""
        self._device.power_state = True
        self._changed = True
        await self.apply_changes()

    async def async_turn_off(self) -> None:
        """Turn off."""
        self._device.power_state = False
        self._changed = True
        await self.apply_changes()

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        return 17

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        return 30
