"""Support for Xiaomi airpurifier pro H."""
import logging
import asyncio

from homeassistant.components.fan import PLATFORM_SCHEMA, FanEntity
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_MODE,
    CONF_HOST,
    CONF_NAME,
    CONF_TOKEN,
)
from .const import (
    DOMAIN,
    SERVICE_SET_BUZZER_OFF,
    SERVICE_SET_BUZZER_ON,
    SERVICE_SET_CHILD_LOCK_OFF,
    SERVICE_SET_CHILD_LOCK_ON,
    SERVICE_SET_FAN_LEVEL,
    SERVICE_SET_FAVORITE_LEVEL,
    SERVICE_SET_LED_BRIGHTNESS,
    SERVICE_SET_MODE,
    SERVICE_SET_SPEED,
)
from homeassistant.exceptions import PlatformNotReady
import homeassistant.helpers.config_validation as cv

import voluptuous as vol
from miio import Device, DeviceException

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Xiaomi Miio Device"
DATA_KEY = "fan.xiaomi_airpurifierProH"

REQUIREMENTS = ['python-miio>=0.4.8']

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_TOKEN): vol.All(str, vol.Length(min=32, max=32)),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    },
    extra=vol.ALLOW_EXTRA,
)

# Air Purifier
ATTR_POWER = "power"
ATTR_SPEED = "speed"
ATTR_TEMPERATURE = "temperature"
ATTR_HUMIDITY = "humidity"
ATTR_AIR_QUALITY_INDEX = "aqi"
ATTR_FILTER_HOURS_USED = "filter_hours_used"
ATTR_FILTER_LIFE = "filter_life_remaining"
ATTR_FAVORITE_LEVEL = "favorite_level"
ATTR_BUZZER = "buzzer"
ATTR_CHILD_LOCK = "child_lock"
ATTR_LED = "led"
ATTR_LED_BRIGHTNESS = "led_brightness"
ATTR_AVERAGE_AIR_QUALITY_INDEX = "average_aqi"
ATTR_PURIFY_VOLUME = "purify_volume"
ATTR_BRIGHTNESS = "led_brightness"
ATTR_LEVEL = "fan_level"
ATTR_MOTOR_SPEED = "motor_speed"
ATTR_ILLUMINANCE = "illuminance"
ATTR_FILTER_RFID_PRODUCT_ID = "filter_rfid_product_id"
ATTR_FILTER_RFID_TAG = "filter_rfid_tag"
ATTR_FILTER_TYPE = "filter_type"
ATTR_LEARN_MODE = "learn_mode"
ATTR_SLEEP_TIME = "sleep_time"
ATTR_SLEEP_LEARN_COUNT = "sleep_mode_learn_count"
ATTR_EXTRA_FEATURES = "extra_features"
ATTR_FEATURES = "features"
ATTR_TURBO_MODE_SUPPORTED = "turbo_mode_supported"
ATTR_AUTO_DETECT = "auto_detect"
ATTR_SLEEP_MODE = "sleep_mode"
ATTR_VOLUME = "volume"
ATTR_USE_TIME = "use_time"
ATTR_BUTTON_PRESSED = "button_pressed"

AVAILABLE_ATTRIBUTES_AIRPURIFIER_PROH = {
    ATTR_POWER: "power",
    ATTR_LEVEL: "fan_level",
    ATTR_MODE: "mode",
    ATTR_HUMIDITY: "humidity",
    ATTR_TEMPERATURE: "temperature",
    ATTR_AIR_QUALITY_INDEX: "aqi",
    ATTR_FILTER_LIFE: "filter_life_remaining",
    ATTR_FILTER_HOURS_USED: "filter_hours_used",
    ATTR_BUZZER: "buzzer",
    ATTR_BRIGHTNESS: "led_brightness",
    ATTR_CHILD_LOCK: "child_lock",
    ATTR_FAVORITE_LEVEL: "favorite_level",
    ATTR_USE_TIME: "use_time",
    ATTR_PURIFY_VOLUME: "purify_volume",
    ATTR_AVERAGE_AIR_QUALITY_INDEX: "average_aqi",
    ATTR_MOTOR_SPEED: "motor_speed",
}

OPERATION_MODES_AIRPURIFIER_PROH = [
    "Auto",
    "Silent",
    "Favorite",
    "Medium",
    "High",
    "Strong",
]

SUCCESS = ["ok"]

FEATURE_SET_BUZZER = 1
FEATURE_SET_LED = 2
FEATURE_SET_CHILD_LOCK = 4
FEATURE_SET_LED_BRIGHTNESS = 8
FEATURE_SET_FAVORITE_LEVEL = 16
FEATURE_SET_AUTO_DETECT = 32
FEATURE_SET_LEARN_MODE = 64
FEATURE_SET_VOLUME = 128
FEATURE_RESET_FILTER = 256
FEATURE_SET_EXTRA_FEATURES = 512
FEATURE_SET_TARGET_HUMIDITY = 1024
FEATURE_SET_DRY = 2048

FEATURE_FLAGS_AIRPURIFIER = (
        FEATURE_SET_BUZZER
        | FEATURE_SET_CHILD_LOCK
        | FEATURE_SET_LED
        | FEATURE_SET_LED_BRIGHTNESS
        | FEATURE_SET_FAVORITE_LEVEL
        | FEATURE_SET_LEARN_MODE
        | FEATURE_RESET_FILTER
        | FEATURE_SET_EXTRA_FEATURES
)

FEATURE_FLAGS_AIRPURIFIER_PRO = (
        FEATURE_SET_CHILD_LOCK
        | FEATURE_SET_LED
        | FEATURE_SET_FAVORITE_LEVEL
        | FEATURE_SET_AUTO_DETECT
        | FEATURE_SET_VOLUME
)

_MAPPING = {
    # Air Purifier (siid=2)
    "power":  {"did": "power", "siid": 2, "piid": 2},
    # Level 0-3 0-Silent 1-Level1 2-Level2 3-Level3
    "fan_level": {"did": "fan_level", "siid": 2, "piid": 4},
    # mode 0-Auto 1-Silent 2-Favorite 3-Manu
    "mode":  {"did": "mode", "siid": 2, "piid": 5},
    # Environment (siid=3)
    "humidity":  {"did": "humidity", "siid": 3, "piid": 7},
    "temperature":  {"did": "temperature", "siid": 3, "piid": 8},
    "aqi":  {"did": "aqi", "siid": 3, "piid": 6},
    # Filter (siid=4)
    "filter_life_remaining":  {"did": "filter_life_remaining", "siid": 4, "piid": 3},
    "filter_hours_used":  {"did": "filter_hours_used", "siid": 4, "piid": 5},
    # Alarm (siid=5) 0-off 50-on
    "buzzer":  {"did": "buzzer", "siid": 5, "piid": 2},
    # Indicator Light (siid=6) 0-Light 1-Gleam 2-Off
    "led_brightness":  {"did": "led_brightness", "siid": 6, "piid": 1},
    # Physical Control Locked (siid=7)
    "child_lock":  {"did": "child_lock", "siid": 7, "piid": 1},
    # Motor Speed (siid=10) 1-10
    "favorite_level":  {"did": "favorite_level", "siid": 10, "piid": 10},
    # 460-1530
    "set_favorite_rpm":  {"did": "set_favorite_rpm", "siid": 10, "piid": 7},
    # 460-1530
    "motor_speed":  {"did": "motor_speed", "siid": 10, "piid": 8},
    # Use time (siid=12)
    "use_time":  {"did": "use_time", "siid": 12, "piid": 1},
    # AQI (siid=13)
    "purify_volume":  {"did": "purify_volume", "siid": 13, "piid": 1},
    "average_aqi":  {"did": "average_aqi", "siid": 13, "piid": 2},
}
AIRPURIFIER_SERVICE_SCHEMA = vol.Schema({vol.Optional(ATTR_ENTITY_ID): cv.entity_ids})

SERVICE_SCHEMA_MODE = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {vol.Required(ATTR_MODE): vol.All(vol.Coerce(int), vol.Clamp(min=0, max=3))}
)

SERVICE_SCHEMA_LED_BRIGHTNESS = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {vol.Required(ATTR_BRIGHTNESS): vol.All(vol.Coerce(int), vol.Clamp(min=0, max=2))},[1]
)

SERVICE_SCHEMA_FAN_LEVEL = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {
        vol.Required(ATTR_LEVEL): vol.All(vol.Coerce(int), vol.Clamp(min=0, max=3)),
    }
)

SERVICE_SCHEMA_FAVORITE_LEVEL = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {vol.Required(ATTR_FAVORITE_LEVEL): vol.All(vol.Coerce(int), vol.Clamp(min=1, max=10))}
)

SERVICE_TO_METHOD = {
    SERVICE_SET_BUZZER_ON: {"method": "async_set_buzzer_on"},
    SERVICE_SET_BUZZER_OFF: {"method": "async_set_buzzer_off"},
    SERVICE_SET_MODE: {
        "method": "async_set_mode",
        "schema": SERVICE_SCHEMA_MODE,},
    SERVICE_SET_CHILD_LOCK_ON: {"method": "async_set_child_lock_on"},
    SERVICE_SET_CHILD_LOCK_OFF: {"method": "async_set_child_lock_off"},
    SERVICE_SET_LED_BRIGHTNESS: {
        "method": "async_set_led_brightness",
        "schema": SERVICE_SCHEMA_LED_BRIGHTNESS,
    },
    SERVICE_SET_FAN_LEVEL: {
        "method": "async_set_fan_level",
        "schema": SERVICE_SCHEMA_FAN_LEVEL,
    },
    SERVICE_SET_FAVORITE_LEVEL: {
        "method": "async_set_favorite_level",
        "schema": SERVICE_SCHEMA_FAVORITE_LEVEL,
    },
}


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Perform the setup for Xiaomi Airpurifier."""
    if DATA_KEY not in hass.data:
        hass.data[DATA_KEY] = {}

    host = config.get(CONF_HOST)
    name = config.get(CONF_NAME)
    token = config.get(CONF_TOKEN)

    _LOGGER.info("Initializing Xiaomi airpurifier pro H with host %s (token %s...)", host, token[:5])

    devices = []
    try:
        device = Device(host, token)
        airPurifierproH = AirPurifierproH(device, name)
    except DeviceException:
        _LOGGER.exception('Fail to setup Xiaomi airpurifier pro H')
        raise PlatformNotReady

    hass.data[DATA_KEY][host] = airPurifierproH
    async_add_entities([airPurifierproH], update_before_add=True)

    async def async_service_handler(service):
        """Map services to methods on XiaomiAirPurifier."""
        method = SERVICE_TO_METHOD.get(service.service)
        params = {
            key: value for key, value in service.data.items() if key != ATTR_ENTITY_ID
        }
        entity_ids = service.data.get(ATTR_ENTITY_ID)
        if entity_ids:
            devices = [
                device
                for device in hass.data[DATA_KEY].values()
                if device.entity_id in entity_ids
            ]
        else:
            devices = hass.data[DATA_KEY].values()

        update_tasks = []
        for device in devices:
            if not hasattr(device, method["method"]):
                continue
            await getattr(device, method["method"])(**params)
            update_tasks.append(device.async_update_ha_state(True))

        if update_tasks:
            await asyncio.wait(update_tasks)

    for air_purifier_service in SERVICE_TO_METHOD:
        schema = SERVICE_TO_METHOD[air_purifier_service].get(
            "schema", AIRPURIFIER_SERVICE_SCHEMA
        )
        hass.services.async_register(
            DOMAIN, air_purifier_service, async_service_handler, schema=schema
        )


class AirPurifierproH(FanEntity):
    """Representation of a XiaomiWaterPurifier."""

    def __init__(self, device, name):
        """Initialize the XiaomiWaterPurifier."""
        self._device = device
        self._name = name
        self._data = None
        self._available = False
        self._speed_list = OPERATION_MODES_AIRPURIFIER_PROH
        self._available_attributes = AVAILABLE_ATTRIBUTES_AIRPURIFIER_PROH
        self._state = None
        self._state_attrs = {}
        self._device_features = FEATURE_SET_CHILD_LOCK
        self.parse_data()

        self._state_attrs.update(
            {attribute: None for attribute in self._available_attributes}
        )
    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return 'mdi:air-purifier'

    @property
    def is_on(self):
        return self._state

    @property
    def speed_list(self) -> list:
        """Get the list of available speeds."""
        return self._speed_list


    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        return self._state_attrs

    @property
    def speed(self):
        """Return the current speed."""
        if self._state:
            return self._state_attrs["speed"]
        return None

    def parse_data(self):
        """Parse data."""
        try:
            # data = {}
            # data["humidity"] = self._device.send('get_properties', [{"did": "humidity", **_MAPPING["humidity"]}])[0][
            #     "value"]
            # data["temperature"] = self._device.send('get_properties', [{"did": "temperature", **_MAPPING["temperature"]}])[0]["value"]
            # data["fan_level"] = self._device.send('get_properties', [{"did": "fan_level", **_MAPPING["fan_level"]}])[0][
            #     "value"]
            # data["child_lock"] = self._device.send('get_properties', [{"did": "child_lock", **_MAPPING["child_lock"]}])[0]["value"]
            # self._state = self._device.send('get_properties', [{"did": "power", **_MAPPING["power"]}])[0]["value"]
            # data["aqi"] = self._device.send('get_properties', [{"did": "aqi", **_MAPPING["aqi"]}])[0]["value"]
            # data["average_aqi"] = self._device.send('get_properties', [{"did": "average_aqi", **_MAPPING["average_aqi"]}])[0]["value"]
            # data["mode"] = self._device.send('get_properties', [{"did": "mode", **_MAPPING["mode"]}])[0]["value"]
            # data["led"] = self._device.send('get_properties', [{"did": "led", **_MAPPING["led"]}])[0]["value"]
            # data["led_brightness"] = self._device.send('get_properties', [{"did": "led_brightness", **_MAPPING["led_brightness"]}])[0]["value"]
            # # data["buzzer"] = self._device.send('get_properties', [{"did": "buzzer", **_MAPPING["buzzer"]}])[0]["value"]
            # data["motor_speed"] = self._device.send('get_properties', [{"did": "motor_speed", **_MAPPING["motor_speed"]}])[0]["value"]
            # data["purify_volume"] = self._device.send('get_properties', [{"did": "purify_volume", **_MAPPING["purify_volume"]}])[0]["value"]
            # data["filter_life_remaining"] = self._device.send('get_properties', [{"did": "filter_life_remaining", **_MAPPING["filter_life_remaining"]}])[0]["value"]
            # data["filter_hours_used"] = self._device.send('get_properties', [{"did": "filter_hours_used", **_MAPPING["filter_hours_used"]}])[0]["value"]
            # data["use_time"] = self._device.send('get_properties', [{"did": "use_time", **_MAPPING["use_time"]}])[0]["value"]
            # data["favorite_level"] = self._device.send('get_properties', [{"did": "favorite_level", **_MAPPING["favorite_level"]}])[0]["value"]
            values = {}
            for prop in self._available_attributes:
                val = self._device.send("get_properties", [_MAPPING[prop]])
                values[prop] = val[0]["value"]
            result = Dict2Obj(values)
            self._state = result["power"]
            if (result["buzzer"] == 0):
                result["buzzer"] = "Off"
            else:
                result["buzzer"] = "On"
            if (result["led_brightness"] == 0):
                result["led_brightness"] = "Light"
            if (result["led_brightness"] == 1):
                result["led_brightness"] = "Gleam"
            if (result["led_brightness"] == 2):
                result["led_brightness"] = "Off"
            if (result["mode"] == 0):
                result["mode"] = "Auto"
            if (result["mode"] == 1):
                result["mode"] = "Silent"
            if (result["mode"] == 2):
                result["mode"] = "Favorite"
            if (result["mode"] == 3):
                result["mode"] = "Manual"
            if(result["fan_level"] == 0):
                result["speed"] = result["mode"]
            if (result["fan_level"] == 1):
                result["speed"] = "Medium"
                result["fan_level"] = "Medium"
            if (result["fan_level"] == 2):
                result["speed"] = "High"
                result["fan_level"] = "High"
            if (result["fan_level"] == 3):
                result["speed"] = "Strong"
                result["fan_level"] = "Strong"
            self._state_attrs.update(result)
        except DeviceException:
            _LOGGER.exception('Fail to get_properties from Xiaomi airpurifier pro H')
            self._data = None
            raise PlatformNotReady

    def update(self):
        """Get the latest data and updates the states."""
        self.parse_data()

    async def async_turn_on(self, speed: str = None, **kwargs):
        if speed:
            result = await self.set_fan_mode(speed)
        else:
            """Turn the device on."""
            result = self._device.send('set_properties', [{**_MAPPING["power"],"value": True}])
        if result:
            self._state = True

    async def async_turn_off(self, **kwargs):
        """Turn the device off."""
        result = self._device.send('set_properties', [{**_MAPPING["power"],"value": False}])
        if result:
            self._state = False

    async def async_set_child_lock_on(self):
        """Turn the child lock on."""
        if not self._state:
            return
        self._device.send('set_properties', [{**_MAPPING["child_lock"],"value": True}])

    async def async_set_child_lock_off(self):
        """Turn the child lock off."""
        if not self._state:
            return
        self._device.send('set_properties', [{**_MAPPING["child_lock"],"value": False}])

    async def async_set_buzzer_on(self):
        if not self._state:
            return
        self._device.send('set_properties', [{**_MAPPING["buzzer"], "value": 50}])

    async def async_set_buzzer_off(self):
        if not self._state:
            return
        self._device.send('set_properties', [{**_MAPPING["buzzer"], "value": 0}])

    def set_led_brightness(self, led_brightness: int = 2) -> None:
        """Set the speed of the fan."""
        raise NotImplementedError()

    async def async_set_led_brightness(self, led_brightness: int = 2):
        if not self._state:
            return
        self._device.send('set_properties', [{**_MAPPING["led_brightness"], "value": led_brightness}])

    async def async_set_fan_level(self, fan_level):
        if not self._state:
            return
        self._device.send('set_properties', [{**_MAPPING["fan_level"], "value": fan_level}])

    def set_speed(self, speed: str) -> None:
        """Set the speed of the fan."""
        raise NotImplementedError()

    async def async_set_speed(self, speed: str):
        print(speed)
        """Set the speed of the fan."""
        if speed == 'Medium':
            result = await self.async_set_fan_level(1)
        if speed == 'High':
            result = await self.async_set_fan_level(2)
        if speed == 'Strong':
            result = await self.async_set_fan_level(3)

    async def async_set_favorite_level(self, favorite_level):
        if not self._state:
            return
        self._device.send('set_properties', [{**_MAPPING["favorite_level"], "value": favorite_level}])

    async def async_set_mode(self, mode):
        if not self._state:
            return
        self._device.send('set_properties', [{**_MAPPING["mode"], "value": mode}])

    async def set_fan_mode(self, type):
        if type == 'Auto':
            result = await self.async_set_mode(0)
        if type == 'Silent':
            result = await self.async_set_mode(1)
        if type == 'Favorite':
            result = await self.async_set_mode(2)
        if type == 'Medium':
            result = await self.async_set_fan_level(1)
        if type == 'High':
            result = await self.async_set_fan_level(2)
        if type == 'Strong':
            result = await self.async_set_fan_level(3)

class Dict2Obj(dict):
    def __init__(self, *args, **kwargs):
        super(Dict2Obj, self).__init__(*args, **kwargs)

    def __getattr__(self, key):
        value = self[key]
        if isinstance(value, dict):
            value = Dict2Obj(value)
        return value