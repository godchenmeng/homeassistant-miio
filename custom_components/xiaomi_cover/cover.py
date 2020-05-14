"""Support for Xiaomi airpurifier pro H."""
import logging
import asyncio

from homeassistant.components.cover import PLATFORM_SCHEMA, ATTR_POSITION, CoverDevice
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_HOST,
    CONF_NAME,
    CONF_TOKEN,
)
from .const import (
    DOMAIN,
    SERVICE_SET_COVER_POSITION,
    SERVICE_OPEN_COVER,
    SERVICE_STOP_COVER,
    SERVICE_CLOSE_COVER,
)
from homeassistant.exceptions import PlatformNotReady
import homeassistant.helpers.config_validation as cv

import voluptuous as vol
from miio import Device, DeviceException

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Xiaomi Miio Device"
DATA_KEY = "cover.xiaomi_cover"

REQUIREMENTS = ['python-miio>=0.4.8']

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_TOKEN): vol.All(str, vol.Length(min=32, max=32)),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    },
    extra=vol.ALLOW_EXTRA,
)

SUCCESS = ["ok"]

SERVICE_SCHEMA = vol.Schema({vol.Optional(ATTR_ENTITY_ID): cv.entity_ids})

SERVICE_TO_METHOD = {
    SERVICE_SET_COVER_POSITION: {"method": "async_set_cover_position"},
    SERVICE_OPEN_COVER: {"method": "async_open_cover"},
    SERVICE_CLOSE_COVER: {"method": "async_close_cover",},
    SERVICE_STOP_COVER: {"method": "async_stop_cover",},
}

def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Perform the setup for Xiaomi Cover."""
    if DATA_KEY not in hass.data:
        hass.data[DATA_KEY] = {}

    host = config.get(CONF_HOST)
    name = config.get(CONF_NAME)
    token = config.get(CONF_TOKEN)

    _LOGGER.info("Initializing Xiaomi Curtain with host %s (token %s...)", host, token[:5])

    try:
        device = Device(host, token)
        cover = Cover(device, name)
    except DeviceException:
        _LOGGER.exception('Fail to setup Xiaomi Curtain')
        raise PlatformNotReady

    hass.data[DATA_KEY][host] = cover
    async_add_entities([cover], update_before_add=True)

    async def async_service_handler(service):
        """Map services to methods on XiaoMiCurtain."""
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

    for cover_service in SERVICE_TO_METHOD:
        schema = SERVICE_TO_METHOD[cover_service].get("schema", SERVICE_SCHEMA)
        hass.services.async_register(
            DOMAIN, cover_service, async_service_handler, schema=schema
        )

class Cover(CoverDevice):
    """Representation of a XiaoMiCurtain."""
    def __init__(self, device, name):
        """Initialize the XiaoMiCurtain."""
        self._device = device
        self._name = name
        self._pos = 0
        self.parse_data()

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def current_cover_position(self):
        """Return the current position of the cover."""
        return self._pos

    @property
    def is_closed(self):
        """Return if the cover is closed."""
        return self.current_cover_position <= 0

    def async_close_cover(self, **kwargs):
        """Close the cover."""
        self._device.send('setOperation','[0]')

    def async_open_cover(self, **kwargs):
        """Open the cover."""
        self._device.send('setOperation','[2]')

    def async_stop_cover(self, **kwargs):
        """Stop the cover."""
        self._device.send('setOperation','[1]')

    def async_set_cover_position(self, **kwargs):
        """Move the cover to a specific position."""
        position = kwargs.get(ATTR_POSITION)
        self._device.send('setPosition',[position])

    def parse_data(self):
        val = self._device.send("get_prop", "[0,1,2]")
        self._pos = val[1]

    async def async_update(self):
        """Get the latest data and updates the states."""
        self.parse_data()