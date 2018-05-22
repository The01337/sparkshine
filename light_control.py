from pytradfri import Gateway
from pytradfri.api.aiocoap_api import APIFactory
from pytradfri.error import PytradfriError

import asyncio
from asyncio import ensure_future


@asyncio.coroutine
def get_api(hostname, identity, psk):
    api_factory = APIFactory(host=hostname, psk_id=identity, psk=psk)

    return api_factory.request


@asyncio.coroutine
def get_lights(api):
    gateway = Gateway()

    devices_command = gateway.get_devices()
    devices_commands = yield from api(devices_command)
    devices = yield from api(devices_commands)

    return [dev for dev in devices if dev.has_light_control]


@asyncio.coroutine
def control_light(light, api, state_on=True):

    def observe_callback(updated_device):
        print("Received message for: %s" % updated_device.light_control.lights[0])

    def observe_err_callback(err):
        print('observe error:', err)

    observe_command = light.observe(
        observe_callback, observe_err_callback, duration=120)
    # Start observation as a second task on the loop.
    ensure_future(api(observe_command))
    # Yield to allow observing to start.
    yield from asyncio.sleep(0)

    if state_on:
        light.light_control.set_dimmer(100)
    else:
        light.light_control.set_dimmer(0)
