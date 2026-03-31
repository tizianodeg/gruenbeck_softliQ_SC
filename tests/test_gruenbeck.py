"""Tests for the Gruenbeck SoftliQ integration."""

from __future__ import annotations

import asyncio
import unittest
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock, Mock

from aiohttp import ClientSession, ServerDisconnectedError
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.gruenbeck_softliQ_SC.button import (
    SoftQLinkButtonEntity,
    SoftQLinkButtonEntityDescription,
)
from custom_components.gruenbeck_softliQ_SC.config_flow import GruenBeckConfigFlow
from custom_components.gruenbeck_softliQ_SC.coordinator import (
    SoftQLinkDataUpdateCoordinator,
)
from custom_components.gruenbeck_softliQ_SC.select import (
    SELECT_DESCRIPTIONS,
    SoftQLinkSelectEntity,
)
from custom_components.gruenbeck_softliQ_SC.softQLinkMuxClient import (
    SoftQLinkMuxClient,
    SoftQLinkParseError,
    SoftQLinkResponseError,
)


def make_hass() -> HomeAssistant:
    """Build a typed Home Assistant test double."""
    return cast(HomeAssistant, SimpleNamespace(loop=asyncio.get_running_loop()))


def make_config_entry(title: str, host: str) -> ConfigEntry[Any]:
    """Build a typed config-entry test double."""
    return cast(
        ConfigEntry[Any],
        SimpleNamespace(
            title=title,
            data={CONF_HOST: host},
            async_on_unload=lambda _: None,
        ),
    )


def make_client_double(**kwargs: Any) -> SoftQLinkMuxClient:
    """Build a typed client test double."""
    return cast(SoftQLinkMuxClient, SimpleNamespace(**kwargs))


def make_coordinator_double(**kwargs: Any) -> SoftQLinkDataUpdateCoordinator:
    """Build a typed coordinator test double."""
    return cast(SoftQLinkDataUpdateCoordinator, SimpleNamespace(**kwargs))


class MockResponse:
    """Minimal aiohttp response mock."""

    def __init__(self, status: int, body: str) -> None:
        self.status = status
        self._body = body

    async def text(self) -> str:
        """Return the mocked response text."""
        return self._body

    async def __aenter__(self) -> "MockResponse":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


class SoftQLinkClientTests(unittest.IsolatedAsyncioTestCase):
    """Tests covering client transport behavior."""

    async def test_execute_mux_query_parses_successful_xml(self) -> None:
        session = AsyncMock(spec=ClientSession)
        session.post.return_value = MockResponse(
            200,
            "<root><D_Y_6>1.0</D_Y_6></root>",
        )
        client = SoftQLinkMuxClient("waterbox", session)

        result = await client._execute_mux_query(["D_Y_6"])

        self.assertEqual(result["D_Y_6"], "1.0")

    async def test_execute_mux_query_rejects_empty_payload(self) -> None:
        session = AsyncMock(spec=ClientSession)
        session.post.return_value = MockResponse(200, "")
        client = SoftQLinkMuxClient("waterbox", session)

        with self.assertRaises(SoftQLinkResponseError):
            await client._execute_mux_query(["D_Y_6"])

    async def test_execute_mux_query_rejects_non_200_response(self) -> None:
        session = AsyncMock(spec=ClientSession)
        session.post.return_value = MockResponse(503, "error")
        client = SoftQLinkMuxClient("waterbox", session)

        with self.assertRaises(SoftQLinkResponseError):
            await client._execute_mux_query(["D_Y_6"])

    async def test_execute_mux_query_rejects_invalid_xml(self) -> None:
        session = AsyncMock(spec=ClientSession)
        session.post.return_value = MockResponse(200, "<root>")
        client = SoftQLinkMuxClient("waterbox", session)

        with self.assertRaises(SoftQLinkParseError):
            await client._execute_mux_query(["D_Y_6"])

    async def test_execute_mux_query_rejects_unconfirmed_edit_value(self) -> None:
        session = AsyncMock(spec=ClientSession)
        session.post.return_value = MockResponse(
            200,
            "<root><D_C_5_1>0</D_C_5_1></root>",
        )
        client = SoftQLinkMuxClient("waterbox", session)

        with self.assertRaises(SoftQLinkResponseError):
            await client._execute_mux_query(
                [],
                edit_prop="D_C_5_1",
                edit_value="1",
                edit_result="1",
            )

    async def test_manual_regeneration_rejects_disconnect(self) -> None:
        session = AsyncMock(spec=ClientSession)
        session.post.side_effect = ServerDisconnectedError()
        client = SoftQLinkMuxClient("waterbox", session)

        with self.assertRaises(SoftQLinkResponseError):
            await client.start_manual_regeneration()


class SoftQLinkCoordinatorTests(unittest.IsolatedAsyncioTestCase):
    """Tests covering coordinator behavior."""

    async def test_coordinator_wraps_client_errors(self) -> None:
        client = make_client_double(
            get_current_values=AsyncMock(side_effect=SoftQLinkResponseError("bad")),
            get_error_memory_values=AsyncMock(),
        )
        entry = make_config_entry("Softener", "waterbox")
        hass = make_hass()
        coordinator = SoftQLinkDataUpdateCoordinator(hass, entry, client)

        with self.assertRaises(UpdateFailed):
            await coordinator._async_update_data()

    async def test_set_active_button_action_updates_state_and_notifies(self) -> None:
        client = make_client_double(
            get_current_values=AsyncMock(return_value={}),
            get_error_memory_values=AsyncMock(return_value={}),
        )
        entry = make_config_entry("Softener", "waterbox")
        hass = make_hass()
        coordinator = SoftQLinkDataUpdateCoordinator(hass, entry, client)
        coordinator.async_update_listeners = Mock()

        coordinator.set_active_button_action("manual_regeneration")

        self.assertTrue(coordinator.button_action_in_progress)
        self.assertEqual(coordinator.active_button_key, "manual_regeneration")
        coordinator.async_update_listeners.assert_called_once()

        coordinator.async_update_listeners.reset_mock()

        coordinator.set_active_button_action(None)

        self.assertFalse(coordinator.button_action_in_progress)
        self.assertIsNone(coordinator.active_button_key)
        coordinator.async_update_listeners.assert_called_once()


class SoftQLinkConfigFlowTests(unittest.IsolatedAsyncioTestCase):
    """Tests covering config-flow behavior."""

    async def test_migrate_old_entry_recreates_entry_from_legacy_domain(self) -> None:
        flow = GruenBeckConfigFlow()
        async_remove = AsyncMock()
        async_add = AsyncMock()
        flow.hass = cast(
            HomeAssistant,
            SimpleNamespace(
                config_entries=SimpleNamespace(
                    async_remove=async_remove,
                    async_add=async_add,
                ),
            ),
        )
        flow.flow_id = "test-flow-id"

        old_entry = SimpleNamespace(
            entry_id="legacy-entry-id",
            title="Legacy Softener",
            version=1,
            data={
                CONF_HOST: "WaterBox.local",
                CONF_NAME: "Friendly Name",
            },
            options={"opt": "value"},
            source="user",
            unique_id=None,
            discovery_keys={},
            minor_version=0,
        )

        result = await flow._async_migrate_old_entry(old_entry)

        async_remove.assert_awaited_once_with("legacy-entry-id")
        async_add.assert_awaited_once()

        migrated_entry = async_add.await_args.args[0]
        self.assertEqual(migrated_entry.entry_id, "legacy-entry-id")
        self.assertEqual(migrated_entry.domain, "gruenbeck_softliq_sc")
        self.assertEqual(migrated_entry.unique_id, "waterbox.local")
        self.assertEqual(migrated_entry.data[CONF_HOST], "WaterBox.local")
        self.assertEqual(
            result["type"],
            FlowResultType.SHOW_PROGRESS_DONE,
        )


class SoftQLinkEntityTests(unittest.IsolatedAsyncioTestCase):
    """Tests covering entity state updates and identifiers."""

    async def test_select_refreshes_and_tracks_option(self) -> None:
        set_mode = AsyncMock()
        request_refresh = AsyncMock()
        coordinator = make_coordinator_double(
            data={"D_C_5_1": "2"},
            config_entry=make_config_entry("Softener", "waterbox"),
            client=make_client_double(
                model="softliQ:SC18",
                sw_version="1.0",
                set_mode=set_mode,
            ),
            async_request_refresh=request_refresh,
        )
        entity = SoftQLinkSelectEntity(coordinator, SELECT_DESCRIPTIONS[0])

        self.assertEqual(entity.current_option, "2")

        await entity.async_select_option("1")

        set_mode.assert_awaited_once_with("1")
        request_refresh.assert_awaited_once()

    async def test_button_and_select_keep_legacy_unique_ids(self) -> None:
        coordinator = make_coordinator_double(
            data={"D_B_1": "0", "D_C_5_1": "0"},
            config_entry=make_config_entry("Friendly Name", "WaterBox"),
            client=make_client_double(model="softliQ:SC18", sw_version="1.0"),
            async_request_refresh=AsyncMock(),
            button_action_in_progress=False,
            active_button_key=None,
            last_update_success=True,
        )

        button = SoftQLinkButtonEntity(
            coordinator,
            cast(
                SoftQLinkButtonEntityDescription,
                SimpleNamespace(
                    key="manual_regeneration",
                    translation_key="manual_regeneration",
                ),
            ),
        )
        select = SoftQLinkSelectEntity(coordinator, SELECT_DESCRIPTIONS[0])

        self.assertEqual(button.unique_id, "friendly name-manual_regeneration")
        self.assertEqual(select.unique_id, "friendly name-d_c_5_1")
        device_info = cast(dict[str, object], button.device_info)
        identifiers = cast(set[tuple[str, str]], device_info["identifiers"])
        self.assertEqual(
            next(iter(identifiers)),
            ("gruenbeck_softliq_sc", "Friendly Name"),
        )

    async def test_button_press_sets_busy_state_and_clears_it_after_refresh(self) -> None:
        start_manual_regeneration = AsyncMock()
        update_listeners = Mock()
        coordinator = make_coordinator_double(
            data={"D_B_1": "0"},
            config_entry=make_config_entry("Softener", "waterbox"),
            client=make_client_double(
                model="softliQ:SC18",
                sw_version="1.0",
                start_manual_regeneration=start_manual_regeneration,
            ),
            async_request_refresh=AsyncMock(),
            button_action_in_progress=False,
            active_button_key=None,
            last_update_success=True,
            async_update_listeners=update_listeners,
        )

        def set_active_button_action(button_key: str | None) -> None:
            coordinator.button_action_in_progress = button_key is not None
            coordinator.active_button_key = button_key
            coordinator.async_update_listeners()

        coordinator.set_active_button_action = set_active_button_action
        entity = SoftQLinkButtonEntity(
            coordinator,
            cast(
                SoftQLinkButtonEntityDescription,
                SimpleNamespace(
                    key="manual_regeneration",
                    translation_key="manual_regeneration",
                ),
            ),
        )
        other_button = SoftQLinkButtonEntity(
            coordinator,
            cast(
                SoftQLinkButtonEntityDescription,
                SimpleNamespace(
                    key="reset_error_memory",
                    translation_key="reset_error_memory",
                ),
            ),
        )

        refresh_started = asyncio.Event()
        allow_refresh_to_finish = asyncio.Event()

        async def blocking_refresh() -> None:
            refresh_started.set()
            await allow_refresh_to_finish.wait()

        coordinator.async_request_refresh.side_effect = blocking_refresh

        press_task = asyncio.create_task(entity.async_press())
        await refresh_started.wait()

        self.assertTrue(coordinator.button_action_in_progress)
        self.assertFalse(entity.available)
        self.assertFalse(other_button.available)
        start_manual_regeneration.assert_awaited_once()

        allow_refresh_to_finish.set()
        await press_task

        self.assertFalse(coordinator.button_action_in_progress)
        self.assertIsNone(coordinator.active_button_key)
        self.assertTrue(entity.available)
        self.assertTrue(other_button.available)
        self.assertEqual(update_listeners.call_count, 2)

    async def test_button_press_clears_busy_state_after_failure(self) -> None:
        reset_error_memory = AsyncMock(side_effect=RuntimeError("boom"))
        coordinator = make_coordinator_double(
            data={"D_B_1": "0"},
            config_entry=make_config_entry("Softener", "waterbox"),
            client=make_client_double(
                model="softliQ:SC18",
                sw_version="1.0",
                reset_error_memory=reset_error_memory,
            ),
            async_request_refresh=AsyncMock(),
            button_action_in_progress=False,
            active_button_key=None,
            last_update_success=True,
            async_update_listeners=Mock(),
        )

        def set_active_button_action(button_key: str | None) -> None:
            coordinator.button_action_in_progress = button_key is not None
            coordinator.active_button_key = button_key
            coordinator.async_update_listeners()

        coordinator.set_active_button_action = set_active_button_action
        entity = SoftQLinkButtonEntity(
            coordinator,
            cast(
                SoftQLinkButtonEntityDescription,
                SimpleNamespace(
                    key="reset_error_memory",
                    translation_key="reset_error_memory",
                ),
            ),
        )

        with self.assertRaises(RuntimeError):
            await entity.async_press()

        self.assertFalse(coordinator.button_action_in_progress)
        self.assertIsNone(coordinator.active_button_key)
        self.assertTrue(entity.available)

    async def test_button_press_clears_busy_state_when_refresh_fails(self) -> None:
        start_manual_regeneration = AsyncMock()
        request_refresh = AsyncMock(side_effect=RuntimeError("refresh failed"))
        coordinator = make_coordinator_double(
            data={"D_B_1": "0"},
            config_entry=make_config_entry("Softener", "waterbox"),
            client=make_client_double(
                model="softliQ:SC18",
                sw_version="1.0",
                start_manual_regeneration=start_manual_regeneration,
            ),
            async_request_refresh=request_refresh,
            button_action_in_progress=False,
            active_button_key=None,
            last_update_success=True,
            async_update_listeners=Mock(),
        )

        def set_active_button_action(button_key: str | None) -> None:
            coordinator.button_action_in_progress = button_key is not None
            coordinator.active_button_key = button_key
            coordinator.async_update_listeners()

        coordinator.set_active_button_action = set_active_button_action
        entity = SoftQLinkButtonEntity(
            coordinator,
            cast(
                SoftQLinkButtonEntityDescription,
                SimpleNamespace(
                    key="manual_regeneration",
                    translation_key="manual_regeneration",
                ),
            ),
        )

        with self.assertRaises(RuntimeError):
            await entity.async_press()

        start_manual_regeneration.assert_awaited_once()
        request_refresh.assert_awaited_once()
        self.assertFalse(coordinator.button_action_in_progress)
        self.assertIsNone(coordinator.active_button_key)
        self.assertTrue(entity.available)

    async def test_button_press_rejects_second_action_while_busy(self) -> None:
        coordinator = make_coordinator_double(
            data={"D_B_1": "0"},
            config_entry=make_config_entry("Softener", "waterbox"),
            client=make_client_double(
                model="softliQ:SC18",
                sw_version="1.0",
                reset_error_memory=AsyncMock(),
            ),
            async_request_refresh=AsyncMock(),
            button_action_in_progress=True,
            active_button_key="manual_regeneration",
            last_update_success=True,
        )

        entity = SoftQLinkButtonEntity(
            coordinator,
            cast(
                SoftQLinkButtonEntityDescription,
                SimpleNamespace(
                    key="reset_error_memory",
                    translation_key="reset_error_memory",
                ),
            ),
        )

        with self.assertRaises(HomeAssistantError):
            await entity.async_press()

        self.assertTrue(coordinator.button_action_in_progress)
        self.assertEqual(coordinator.active_button_key, "manual_regeneration")

    async def test_manual_regeneration_stays_unavailable_when_device_reports_running(
        self,
    ) -> None:
        coordinator = make_coordinator_double(
            data={"D_B_1": "1"},
            config_entry=make_config_entry("Softener", "waterbox"),
            client=make_client_double(model="softliQ:SC18", sw_version="1.0"),
            async_request_refresh=AsyncMock(),
            button_action_in_progress=False,
            active_button_key=None,
            last_update_success=True,
        )

        entity = SoftQLinkButtonEntity(
            coordinator,
            cast(
                SoftQLinkButtonEntityDescription,
                SimpleNamespace(
                    key="manual_regeneration",
                    translation_key="manual_regeneration",
                ),
            ),
        )

        self.assertFalse(entity.available)
