"""MUX interface of Gruenbeck SoftQLink Water Softener."""

import asyncio
from dataclasses import dataclass
from enum import StrEnum
import logging
from decimal import Decimal
from typing import TypeAlias

from aiohttp import ClientError, ClientSession, ClientTimeout, ServerDisconnectedError
import defusedxml.ElementTree as defET
import homeassistant.util.dt as dt_util
from xml.etree.ElementTree import ParseError

from .const import REQUEST_TIMEOUT, TOTAL_CONSUMPTION

_LOGGER = logging.getLogger(__name__)
SoftQLinkValue: TypeAlias = str | Decimal

SOFTWARE_VERSION_PROP = "D_Y_6"
SOFTENER_TYPE_PROP = "D_F_4"
MC_SYSTEM_TYPE_PROP = "D_F_6"
SC_SOFTWARE_MAJOR_VERSION = "V01"
MC_SOFTWARE_MAJOR_VERSION = "V02"
UNKNOWN_MODEL = "Unknown Device"
MODE_PROP = "D_C_5_1"
MANUAL_REGENERATION_PROP = "D_B_1"
RESET_ERROR_MEMORY_PROP = "D_M_3_3"


class ModelFamily(StrEnum):
    """Supported softener model families."""

    SC = "SC"
    MC = "MC"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class QuerySpec:
    """Properties and protected code required for one MUX operation."""

    props: tuple[str, ...] = ()
    code: str = ""


@dataclass(frozen=True)
class ModelDescriptor:
    """Resolved model-specific query behavior."""

    family: ModelFamily
    display_model: str
    current_values: QuerySpec
    error_memory: QuerySpec
    reset_error_memory: QuerySpec


DEFAULT_CURRENT_VALUES_SPEC = QuerySpec(
    props=(
        "D_A_1_1",
        "D_A_1_2",
        "D_A_1_3",
        MODE_PROP,
        "D_A_1_7",
        "D_A_2_1",
        "D_A_2_2",
        "D_A_2_3",
        "D_A_3_1",
        "D_A_3_2",
        "D_Y_1",
        "D_Y_3",
        "D_Y_5",
        SOFTWARE_VERSION_PROP,
        "D_Y_10_1",
        "D_D_1",
        MANUAL_REGENERATION_PROP,
    )
)
SOFTWARE_VERSION_QUERY_SPEC = QuerySpec(props=(SOFTWARE_VERSION_PROP,))
SOFTENER_TYPE_QUERY_SPEC = QuerySpec(props=(SOFTENER_TYPE_PROP,), code="290")
MC_SYSTEM_TYPE_QUERY_SPEC = QuerySpec(props=(MC_SYSTEM_TYPE_PROP,), code="290")
MODE_WRITE_QUERY_SPEC = QuerySpec(props=(MODE_PROP,))
MANUAL_REGENERATION_QUERY_SPEC = QuerySpec(props=(MANUAL_REGENERATION_PROP,))
SC_MODEL_NAMES = {
    "1": "softliQ:SC18",
    "2": "softliQ:SC23",
}
MC_MODEL_NAMES = {
    "1": "softliQ:MC32",
    "2": "softliQ:MC38",
}
SC_DESCRIPTOR = ModelDescriptor(
    family=ModelFamily.SC,
    display_model=UNKNOWN_MODEL,
    current_values=DEFAULT_CURRENT_VALUES_SPEC,
    error_memory=QuerySpec(
        props=("D_K_3", "D_K_2", "D_K_5", "D_K_8", "D_K_9", "D_K_10_1"),
        code="245",
    ),
    reset_error_memory=QuerySpec(props=(RESET_ERROR_MEMORY_PROP,), code="189"),
)
MC_DESCRIPTOR = ModelDescriptor(
    family=ModelFamily.MC,
    display_model=UNKNOWN_MODEL,
    current_values=DEFAULT_CURRENT_VALUES_SPEC,
    error_memory=QuerySpec(
        props=("D_K_3", "D_K_2", "D_K_5", "D_K_8", "D_K_9", "D_K_10_1"),
        code="005",
    ),
    reset_error_memory=QuerySpec(props=(RESET_ERROR_MEMORY_PROP,), code="005"),
)


class SoftQLinkClientError(Exception):
    """Base exception for SoftQLink client failures."""


class SoftQLinkTimeoutError(SoftQLinkClientError):
    """The device did not answer within the request timeout."""


class SoftQLinkResponseError(SoftQLinkClientError):
    """The device returned an invalid response."""


class SoftQLinkParseError(SoftQLinkClientError):
    """The device returned malformed XML."""


class SoftQLinkMuxClient:
    """Encapsulates the http communication to the SoftQLink."""

    _timeout = ClientTimeout(total=REQUEST_TIMEOUT)

    @staticmethod
    async def create(host: str, session: ClientSession) -> "SoftQLinkMuxClient":
        """Create generates a client and initialize the connection."""
        client = SoftQLinkMuxClient(host, session)
        await client._init()
        return client

    def __init__(self, host: str, session: ClientSession):
        """Initialize."""
        self.session = session
        self.host = host
        self.client_id = 2444
        self.connected = False
        self.total_consumption: Decimal = Decimal("0")
        self.last_flow = ""
        self.last_update = dt_util.utcnow()
        self._lock = asyncio.Lock()
        self.sw_version = ""
        self.model = ""
        self.model_family = ModelFamily.UNKNOWN
        self._model_descriptor = SC_DESCRIPTOR

    async def _init(self):
        """Initialize Software Version and Model from the SoftQLink Device."""
        self.sw_version = await self._get_software_version()
        self._model_descriptor = self._resolve_model_descriptor(self.sw_version)
        self.model_family = self._model_descriptor.family
        self.model = await self._resolve_model_name()
        if self.model:
            self.connected = True

    async def _get_software_version(self) -> str:
        result = await self._execute_mux_query(
            props=list(SOFTWARE_VERSION_QUERY_SPEC.props),
            code=SOFTWARE_VERSION_QUERY_SPEC.code,
        )
        software_value = result.get(SOFTWARE_VERSION_PROP)
        if isinstance(software_value, str):
            return software_value
        return ""

    async def _get_model_name(
        self,
        query_spec: QuerySpec,
        prop: str,
        model_names: dict[str, str],
    ) -> str:
        """Resolve a model name from a protected type/system register."""
        result = await self._execute_mux_query(
            props=list(query_spec.props),
            code=query_spec.code,
        )
        type_value = result.get(prop)
        if isinstance(type_value, str):
            return model_names.get(type_value, UNKNOWN_MODEL)
        return ""

    def _resolve_model_descriptor(self, sw_version: str) -> ModelDescriptor:
        """Resolve the model-specific query mapping from the software version."""
        if sw_version.startswith(SC_SOFTWARE_MAJOR_VERSION):
            return SC_DESCRIPTOR
        if sw_version.startswith(MC_SOFTWARE_MAJOR_VERSION):
            return MC_DESCRIPTOR
        return ModelDescriptor(
            family=ModelFamily.UNKNOWN,
            display_model=UNKNOWN_MODEL,
            current_values=SC_DESCRIPTOR.current_values,
            error_memory=SC_DESCRIPTOR.error_memory,
            reset_error_memory=SC_DESCRIPTOR.reset_error_memory,
        )

    async def _resolve_model_name(self) -> str:
        """Resolve the device model string exposed to Home Assistant."""
        if self.model_family == ModelFamily.MC:
            return await self._get_model_name(
                MC_SYSTEM_TYPE_QUERY_SPEC,
                MC_SYSTEM_TYPE_PROP,
                MC_MODEL_NAMES,
            )
        if self.model_family == ModelFamily.SC:
            return await self._get_model_name(
                SOFTENER_TYPE_QUERY_SPEC,
                SOFTENER_TYPE_PROP,
                SC_MODEL_NAMES,
            )
        return UNKNOWN_MODEL

    async def get_error_memory_values(self) -> dict[str, SoftQLinkValue]:
        """Get error-memory-related values from the model-specific protected area."""
        last_error_code = "D_K_10_1"
        query_spec = self._model_descriptor.error_memory
        result = await self._execute_mux_query(
            props=list(query_spec.props),
            code=query_spec.code,
        )
        self._split_error_code_and_age(result, last_error_code)
        return result

    async def get_current_values(self) -> dict[str, SoftQLinkValue]:
        """Get current values e.g D_A_?, D_Y_? and D_D_?."""
        query_spec = self._model_descriptor.current_values
        return await self._execute_mux_query(
            props=list(query_spec.props),
            code=query_spec.code,
        )

    async def set_mode(self, mode: str) -> dict[str, SoftQLinkValue]:
        """Set the device mode."""
        return await self._execute_mux_query(
            list(MODE_WRITE_QUERY_SPEC.props),
            edit_prop=MODE_PROP,
            edit_value=mode,
            edit_result=mode,
        )

    async def start_manual_regeneration(self) -> None:
        """Trigger a manual regeneration cycle."""
        await self._execute_mux_query(
            list(MANUAL_REGENERATION_QUERY_SPEC.props),
            edit_prop=MANUAL_REGENERATION_PROP,
            edit_value="1",
            edit_result="1",
        )

    async def reset_error_memory(self) -> None:
        """Reset the error memory using the model-specific protected area."""
        query_spec = self._model_descriptor.reset_error_memory
        await self._execute_mux_query(
            list(query_spec.props),
            code=query_spec.code,
            edit_prop=RESET_ERROR_MEMORY_PROP,
            edit_value="1",
            edit_result="0",
        )

    async def _execute_mux_query(
        self,
        props: list[str],
        code: str = "",
        edit_prop: str = "",
        edit_value: str = "",
        edit_result: str = "",
    ) -> dict[str, SoftQLinkValue]:
        """Execute a mux query and parse the XML response."""
        query = self._generate_query(props, edit_prop, edit_value, code)
        xml = await self._post_query(query, expect_xml=True)
        result = self._parse_xml_to_dict(xml)
        if edit_result:
            self._validate_expected_value(result, edit_prop, edit_result)
        return result

    async def _post_query(
        self,
        query: str,
        *,
        expect_xml: bool,
    ) -> str:
        """POST a query to the device and return the raw body."""
        async with self._lock:
            url = f"http://{self.host}/mux_http"
            max_retry = 5
            for retry in range(1, max_retry + 1):
                try:
                    async with self.session.post(
                        url,
                        timeout=self._timeout,
                        data=query,
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                    ) as response:
                        body = await response.text()
                        if response.status != 200:
                            raise SoftQLinkResponseError(
                                f"Unexpected HTTP status {response.status}"
                            )
                        if expect_xml and not body:
                            raise SoftQLinkResponseError(
                                "Mux server returned an empty payload"
                            )
                        return body
                except ServerDisconnectedError:
                    last_error = SoftQLinkResponseError(
                        "Device disconnected unexpectedly"
                    )
                except TimeoutError:
                    last_error = SoftQLinkTimeoutError("Request to SoftQLink timed out")
                except ClientError as err:
                    last_error = SoftQLinkResponseError(str(err))
                except SoftQLinkClientError as err:
                    last_error = err
                _LOGGER.debug(
                    "Failed to execute '%s' on '%s' %s times: %s",
                    query,
                    url,
                    retry,
                    last_error,
                )
                if retry == max_retry:
                    raise last_error
            raise SoftQLinkResponseError("Mux server did not return a valid response")

    def _generate_query(
        self,
        props: list[str],
        edit_prop: str,
        edit_value: str,
        code: str,
    ) -> str:
        show_props = list(props)
        if edit_prop and edit_prop not in show_props:
            show_props.append(edit_prop)

        clientId = f"id={self.client_id}"
        show = f"&show={'|'.join(show_props)}"
        edit = ""
        if code:
            code = f"&code={code}"
        if edit_prop:
            edit = f"&edit={edit_prop}>{edit_value}"
        query = f"{clientId}{code}{edit}{show}~"
        return query

    def _calculate_total(self, flow: str) -> None:
        if self.last_flow:
            now = dt_util.utcnow()
            elapsed_time = (now - self.last_update).total_seconds()
            area = Decimal(flow) * Decimal(elapsed_time)
            self.total_consumption += area / (60 * 60)
        self.last_flow = flow
        self.last_update = dt_util.utcnow()

    def _parse_xml_to_dict(self, xml_data: str) -> dict[str, SoftQLinkValue]:
        try:
            root = defET.fromstring(xml_data)
        except ParseError as err:
            raise SoftQLinkParseError("Mux server returned malformed XML") from err

        data_dict: dict[str, SoftQLinkValue] = {}
        for elem in root:
            if elem.tag != "code":
                data_dict[elem.tag] = (elem.text or "").strip()
                if elem.tag == "D_A_1_1":
                    self._calculate_total(str(data_dict[elem.tag]))
        data_dict[TOTAL_CONSUMPTION] = round(self.total_consumption, 4)
        return data_dict

    def _validate_expected_value(
        self,
        data: dict[str, SoftQLinkValue],
        prop: str,
        expected_value: str,
    ) -> None:
        """Validate that the device echoed the expected value."""
        actual_value = data.get(prop)
        if actual_value != expected_value:
            raise SoftQLinkResponseError(
                f"Expected {prop}={expected_value}, got {actual_value!r}"
            )

    def _split_error_code_and_age(
        self,
        data: dict[str, SoftQLinkValue],
        error_code_key: str,
    ) -> None:
        """Split a combined error code like ``E4_12h`` into code and age fields."""
        error_code = data.get(error_code_key)
        if not isinstance(error_code, str) or "_" not in error_code:
            return

        code_and_age = error_code.split("_", maxsplit=1)
        data[error_code_key] = code_and_age[0]
        data[f"{error_code_key}_Hours"] = code_and_age[1].replace("h", "")
