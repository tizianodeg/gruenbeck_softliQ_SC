"""MUX interface of Gruenbeck SoftQLink Water Softener."""
import asyncio
import logging

from aiohttp import ClientSession, ClientTimeout, ServerDisconnectedError
import defusedxml.ElementTree as defET
from decimal import Decimal
import homeassistant.util.dt as dt_util

from .const import TOTAL_CONSUMPTION

_LOGGER = logging.getLogger(__name__)


class SoftQLinkMuxClient:
    """Encapsulates the http communication to the SoftQLink."""

    @staticmethod
    async def create(host: str, session: ClientSession):
        """Create generates a client and initialize the connection."""
        client = SoftQLinkMuxClient(host, session)
        await client._init()
        return client

    def __init__(self, host: str, session: ClientSession):
        """Initialize."""
        self.session = session
        self.host = host
        self.clientId = 2444
        self.connected = False
        self.total_consumption = 0
        self.lastFlow = 0
        self.last_update = dt_util.utcnow()
        self._lock = asyncio.Lock()

    async def _init(self):
        """Initialize Software Version and Model from the SoftQLink Device."""
        self.sw_version = await self.__getSoftwareVersion()
        self.model = await self.__getSoftenerType()
        if self.model:
            self.connected = True

    async def __getSoftenerType(self) -> str:
        typecode = "D_F_4"
        result = await self._executeMuxQuery(props=[typecode], code="290")
        if typecode in result:
            match result[typecode]:
                case "1":
                    return "softliQ:SC18"
                case "2":
                    return "softliQ:SC23"
                case _:
                    return "Unknown Device"
        return ""

    async def __getSoftwareVersion(self) -> str:
        softwareCode = "D_Y_6"
        result = await self._executeMuxQuery(props=[softwareCode])
        if softwareCode in result:
            return result[softwareCode]
        return ""

    async def getMeterValues(self) -> dict[str, str]:
        """Get some basic meter values e.g. D_K_?."""
        lastErrorCode = "D_K_10_1"
        result = await self._executeMuxQuery(
            props=["D_K_3", "D_K_2", "D_K_5",  "D_K_8", "D_K_9", lastErrorCode], code="245"
        )
        if lastErrorCode in result:
            errorcode = result[lastErrorCode]
            if errorcode.find("_") > -1:
                codeAndDay = errorcode.split("_")
                result[lastErrorCode] = codeAndDay[0]
                result[f"{lastErrorCode}_Hours"] = codeAndDay[1].replace("h", "")
        return result

    async def getCurrentValues(self) -> dict[str, str]:
        """Get current values e.g D_A_?, D_Y_? and D_D_?."""
        return await self._executeMuxQuery(
            props=[
                "D_A_1_1",
                "D_A_1_2",
                "D_A_1_3",
                "D_C_5_1",
                "D_A_1_7",
                "D_A_2_1",
                "D_A_2_2",
                "D_A_2_3",
                "D_A_3_1",
                "D_A_3_2",
                "D_Y_1",
                "D_Y_3",
                "D_Y_5",
                "D_Y_6",
                "D_D_1",
            ]
        )

    async def setMode(self, mode):
        """Set a parameter"""
        return await self._executeMuxQuery([],"","D_C_5_1", mode)

    async def startManualRegeneration(self) -> None:
        """Trigger a manual regeneration cycle."""
        async with self._lock:
            query = "id=0000&edit=D_B_1>1&show=D_B_1~"
            url = f"http://{self.host}/mux_http"
            try:
                async with self.session.post(
                    url,
                    timeout=ClientTimeout(5000),
                    data=query,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                ) as response:
                    await response.text()
            except ServerDisconnectedError:
                pass  # Device closes connection after accepting command
            except Exception as e:
                _LOGGER.error("Manual regeneration failed: %s", e)
                raise

    async def resetErrorMemory(self) -> None:
        """Reset the error memory."""
        async with self._lock:
            query = "id=0000&edit=D_M_3_3>1&code=189&show=D_M_3_3~"
            url = f"http://{self.host}/mux_http"
            try:
                async with self.session.post(
                    url,
                    timeout=ClientTimeout(5000),
                    data=query,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                ) as response:
                    await response.text()
            except ServerDisconnectedError:
                pass  # Device closes connection after accepting command
            except Exception as e:
                _LOGGER.error("Error memory reset failed: %s", e)
                raise

    async def resetErrorMemory(self) -> None:
        """Reset the error memory (Mux code 189)."""
        async with self._lock:
            _LOGGER.warning("Gruenbeck: resetErrorMemory called")
            query = "id=0000&code=189&show=~"
            url = f"http://{self.host}/mux_http"
            try:
                async with self.session.post(
                    url,
                    timeout=ClientTimeout(5000),
                    data=query,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                ) as response:
                    body = await response.text()
                    _LOGGER.info(
                        "Gruenbeck: error memory reset response (HTTP %s): %s",
                        response.status, body,
                    )
            except ServerDisconnectedError:
                _LOGGER.warning("Gruenbeck: error reset sent (device disconnected)")
            except Exception as e:
                _LOGGER.error("Gruenbeck: error reset failed: %s", e)
                raise

    async def _executeMuxQuery(
        self, props: list[str], code: str = "", editProp:str="", editValue:str=""
    ) -> dict[str, str]:
        async with self._lock:
            retry = 0
            maxRetry = 5
            success = False
            query = self.__generateQuery(props, editProp, editValue, code)
            url = f"http://{self.host}/mux_http"
            result: dict[str, str] = {}
            while not success and retry < maxRetry:
                retry += 1
                try:
                    async with self.session.post(
                        url,
                        timeout=ClientTimeout(5000),
                        data=query,
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                    ) as response:
                        if response.status == 200:
                            await asyncio.sleep(0.001)
                            xml = await response.text()
                            if xml:
                                result = self.__parse_xml_to_dict(xml)
                                success = True
                            else:
                                _LOGGER.debug(
                                    "Empty result for '%s' on '%s' %s-times",
                                    query, url, retry,
                                )
                except Exception as e:
                    _LOGGER.debug(
                        "Failed to execute '%s' on '%s' %s-times Error: '%s'",
                        query, url, retry, e,
                    )
                    if retry < maxRetry:
                        continue
                    else:
                        raise
            if not success:
                raise Exception("Mux server did not return a valid content")
            return result


    def __generateQuery(self, props, editProp, editValue ,code):
        clientId = f"id={self.clientId}"
        show = f"&show={'|'.join(props)}"
        edit = ""
        if code:
            code = f"&code={code}"
        if editProp:
            edit = f"&edit={editProp}>{editValue}"
        query = f"{clientId}{code}{edit}{show}~"
        return query
    
    def __calculate_total__(self, flow, data_dict):
        if self.lastFlow:
            now = dt_util.utcnow()
            elapsed_time = (now - self.last_update).total_seconds()
            area = Decimal(flow) * Decimal(elapsed_time)
            self.total_consumption += area / (60 * 60)
        self.lastFlow = flow
        self.last_update = dt_util.utcnow()

    def __parse_xml_to_dict(self, xml_data):
        root = defET.fromstring(xml_data)
        data_dict = {} 
        for elem in root:
            if elem.tag != "code":
                data_dict[elem.tag] = (elem.text or "").strip()
                if elem.tag == "D_A_1_1":
                    self.__calculate_total__(data_dict[elem.tag], data_dict)
        data_dict[TOTAL_CONSUMPTION] = round(self.total_consumption, 4)
        return data_dict
