import uuid
from typing import Any, ClassVar, Dict, Mapping, Optional, Sequence, Tuple

import aiohttp
from typing_extensions import Self
from viam.components.component_base import ComponentBase
from viam.components.switch import *
from viam.logging import getLogger
from viam.proto.app.robot import ComponentConfig
from viam.proto.common import Geometry, ResourceName
from viam.resource.base import ResourceBase
from viam.resource.easy_resource import EasyResource
from viam.resource.types import Model, ModelFamily
from viam.utils import ValueTypes, struct_to_dict

LOGGER = getLogger(__name__)
GOVEE_BASE_URL = "https://openapi.api.govee.com/router/api/v1"


class SmartPlug(Switch, EasyResource):
    MODEL: ClassVar[Model] = Model(
        ModelFamily("viam-labs", "govee-devices"), "smart-plug"
    )

    api_key: str = ""
    device_id: str = ""
    sku: str = ""
    is_on: bool = False

    @classmethod
    def new(
        cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ) -> Self:
        return super().new(config, dependencies)

    @classmethod
    def validate_config(
        cls, config: ComponentConfig
    ) -> Tuple[Sequence[str], Sequence[str]]:
        attrs = struct_to_dict(config.attributes)
        for key in ["api_key", "device_id", "sku"]:
            val = attrs.get(key)
            if not val or not isinstance(val, str) or not val.strip():
                raise ValueError(
                    f"'{key}' is required in config attributes and must be a non-empty string"
                )
        return [], []

    def reconfigure(
        self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ):
        LOGGER.info("SmartPlug reconfigure called")
        try:
            attrs = struct_to_dict(config.attributes)
            LOGGER.info(f"SmartPlug reconfigure attrs={attrs}")
            self.api_key = str(attrs.get("api_key", "")).strip()
            self.device_id = str(attrs.get("device_id", "")).strip()
            self.sku = str(attrs.get("sku", "")).strip()
            self.is_on = False

            missing = [k for k in ["api_key", "device_id", "sku"] if not getattr(self, k)]
            if missing:
                raise ValueError(f"Missing required config attributes: {', '.join(missing)}")

            LOGGER.info(f"SmartPlug configured: sku={self.sku}, device={self.device_id}")
        except Exception as e:
            LOGGER.error(f"SmartPlug reconfigure failed: {e}")
            raise

        LOGGER.info(f"SmartPlug configured: sku={self.sku}, device={self.device_id}")

    async def _govee_request(
        self, method: str, path: str, json_body: dict = None, params: dict = None
    ) -> dict:
        url = f"{GOVEE_BASE_URL}{path}"
        headers = {
            "Govee-API-Key": self.api_key,
            "Content-Type": "application/json",
        }
        LOGGER.info(f"Govee API {method} {url} body={json_body} params={params}")
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method, url, headers=headers, json=json_body, params=params
            ) as resp:
                body = await resp.text()
                LOGGER.info(f"Govee API response: status={resp.status} body={body}")
                if resp.status != 200:
                    raise Exception(
                        f"Govee API error (HTTP {resp.status}): {body}"
                    )
                data = await resp.json(content_type=None)
                if data.get("code") != 200:
                    raise Exception(
                        f"Govee API error code {data.get('code')}: {data.get('message', 'unknown')}"
                    )
                return data

    async def _send_control_command(self, turn_on: bool) -> None:
        body = {
            "requestId": str(uuid.uuid4()),
            "payload": {
                "sku": self.sku,
                "device": self.device_id,
                "capability": {
                    "type": "devices.capabilities.on_off",
                    "instance": "powerSwitch",
                    "value": 1 if turn_on else 0,
                },
            },
        }
        await self._govee_request("POST", "/device/control", json_body=body)
        self.is_on = turn_on
        LOGGER.info(f"SmartPlug {self.device_id}: turned {'on' if turn_on else 'off'}")

    async def _get_device_state(self) -> bool:
        params = {"device": self.device_id, "sku": self.sku}
        data = await self._govee_request("GET", "/device/state", params=params)
        capabilities = data.get("payload", {}).get("capabilities", [])
        for cap in capabilities:
            if (
                cap.get("type") == "devices.capabilities.on_off"
                and cap.get("instance") == "powerSwitch"
            ):
                state_value = cap.get("state", {}).get("value", 0)
                return state_value == 1
        LOGGER.warning("Could not find power state in device response, assuming off")
        return False

    async def get_position(
        self,
        *,
        extra: Optional[Mapping[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> int:
        try:
            self.is_on = await self._get_device_state()
        except Exception as e:
            LOGGER.warning(f"Failed to query device state, using cached value: {e}")
        return 1 if self.is_on else 0

    async def set_position(
        self,
        position: int,
        *,
        extra: Optional[Mapping[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> None:
        if position not in (0, 1):
            raise ValueError(f"Invalid position {position}: must be 0 (off) or 1 (on)")
        await self._send_control_command(turn_on=(position == 1))

    async def get_number_of_positions(
        self,
        *,
        extra: Optional[Mapping[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> Tuple[int, Sequence[str]]:
        return 2, ["off", "on"]

    async def do_command(
        self,
        command: Mapping[str, ValueTypes],
        *,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> Mapping[str, ValueTypes]:
        result = {}
        for name, args in command.items():
            if name == "toggle_on":
                try:
                    await self._send_control_command(turn_on=True)
                    result["toggle_on"] = self.is_on
                except Exception as e:
                    result["toggle_on"] = f"Error: {str(e)}"

            if name == "toggle_off":
                try:
                    await self._send_control_command(turn_on=False)
                    result["toggle_off"] = self.is_on
                except Exception as e:
                    result["toggle_off"] = f"Error: {str(e)}"

            if name == "toggle_switch":
                try:
                    current_state = await self._get_device_state()
                    new_state = not current_state
                    await self._send_control_command(turn_on=new_state)
                    result["toggle_switch"] = self.is_on
                except Exception as e:
                    result["toggle_switch"] = f"Error: {str(e)}"

        return result

    async def get_geometries(
        self, *, extra: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None
    ) -> Sequence[Geometry]:
        return []
