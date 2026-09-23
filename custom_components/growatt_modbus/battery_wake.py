"""APX wake pulse for MIN TL-XH inverters.

The APX power module can be woken by the inverter's WAKE line. Growatt's cloud
charging schedule appears to assert that line, while changing priority register
3018 alone does not. This module contains the protocol sequence only; the button
platform decides where it is exposed.
"""
from __future__ import annotations

import time
from collections.abc import Callable

from .growatt_modbus import ModbusWriteError

VPP_CONTROL_AUTHORITY = 30100
VPP_REMOTE_POWER_ENABLE = 30407
VPP_REMOTE_POWER_DURATION = 30408

WAKE_DURATION_MINUTES = 1
WAKE_POWER_PERCENT = 5
# VPP 2.01 on MIN TL-XH accepts 0/1 here. Mode 2 belongs to VPP 2.03 and is
# silently normalised back to 1 by this firmware.
WAKE_AC_CHARGE_MODE = 1
WAKE_PULSE_SECONDS = 12


class BatteryWakeError(Exception):
    """The APX wake sequence could not be completed safely."""


def _read_exact(client, start: int, count: int) -> list[int]:
    """Read an exact VPP block or fail before changing inverter state."""
    values = client.read_holding_registers(start, count)
    if values is None or len(values) < count:
        raise BatteryWakeError(
            f"VPP registers {start}-{start + count - 1} are not available on this firmware"
        )
    return [int(value) for value in values[:count]]


def wake_apx_battery(
    client,
    pulse_seconds: int = WAKE_PULSE_SECONDS,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> None:
    """Request a short low-power charge, then restore the previous VPP state.

    The pulse is deliberately small and bounded. Register 30408 is set to one
    minute as a second safety limit if the explicit 30407 clear cannot be sent.
    Existing VPP control is paused for the pulse and restored afterwards.
    """
    original_authority: int | None = None
    original_remote: list[int] | None = None
    cleanup_required = False
    operation_error: BatteryWakeError | None = None

    try:
        with client.write_batch("MIN TL-XH APX wake start"):
            original_authority = _read_exact(client, VPP_CONTROL_AUTHORITY, 1)[0]
            original_remote = _read_exact(client, VPP_REMOTE_POWER_ENABLE, 4)

            if original_remote[0] != 0:
                # Deselect the active direct branch before replacing its parameters.
                # The original selector and parameters are restored after the pulse.
                cleanup_required = True
                if not client.write_register(
                    VPP_REMOTE_POWER_ENABLE,
                    0,
                    bypass_rate_limit=True,
                ):
                    raise BatteryWakeError(
                        "Active VPP remote power control could not be paused"
                    )

            # From the first write onward, cleanup is required even if a response
            # is lost: the inverter may have accepted a write the client did not see.
            cleanup_required = True

            if original_authority != 1 and not client.write_register(
                VPP_CONTROL_AUTHORITY,
                1,
            ):
                raise BatteryWakeError("The inverter rejected VPP control authority")

            # Set duration, power and AC charge mode atomically before selecting
            # the direct-power branch. The deliberately small five-percent pulse
            # is intended only to request a wake, not to perform a charging cycle.
            if not client.write_registers(
                VPP_REMOTE_POWER_DURATION,
                [WAKE_DURATION_MINUTES, WAKE_POWER_PERCENT, WAKE_AC_CHARGE_MODE],
            ):
                raise BatteryWakeError("The inverter rejected the APX wake parameters")

            if not client.write_register(VPP_REMOTE_POWER_ENABLE, 1):
                raise BatteryWakeError("The inverter rejected the APX wake command")

        sleep_fn(pulse_seconds)
    except BatteryWakeError as exc:
        operation_error = exc
    except ModbusWriteError as exc:
        operation_error = BatteryWakeError(f"Modbus rejected the APX wake sequence: {exc}")
    except Exception as exc:
        operation_error = BatteryWakeError(f"APX wake sequence failed: {exc}")

    cleanup_errors: list[str] = []
    if cleanup_required and original_remote is not None:
        remote_cleared = False
        try:
            with client.write_batch("MIN TL-XH APX wake release"):
                # Deselect the wake command before restoring the old parameters. This
                # clear is part of the same user command, so the normal 30-second
                # anti-oscillation cooldown must not veto it (#400).
                try:
                    remote_cleared = bool(
                        client.write_register(
                            VPP_REMOTE_POWER_ENABLE,
                            0,
                            bypass_rate_limit=True,
                        )
                    )
                    if not remote_cleared:
                        cleanup_errors.append(
                            "register 30407 could not be cleared; its command remains "
                            "limited to 5% for at most one minute"
                        )
                except ModbusWriteError as exc:
                    cleanup_errors.append(
                        "register 30407 could not be cleared; its command remains "
                        f"limited to 5% for at most one minute: {exc}"
                    )

                # Restore the old parameters only after the direct branch is known to
                # be deselected. If 30407 could not be cleared, retaining the small,
                # one-minute command is safer than reinstating a larger old setpoint.
                if remote_cleared:
                    parameters_restored = False
                    try:
                        parameters_restored = bool(
                            client.write_registers(
                                VPP_REMOTE_POWER_DURATION,
                                original_remote[1:4],
                            )
                        )
                        if not parameters_restored:
                            cleanup_errors.append(
                                "VPP parameters 30408-30410 could not be restored"
                            )
                    except ModbusWriteError as exc:
                        cleanup_errors.append(
                            f"VPP parameters 30408-30410 could not be restored: {exc}"
                        )

                    # Re-select the previous branch only after its parameters are back.
                    # Otherwise an old direct-power branch could be re-enabled with the
                    # wake setpoint still behind it.
                    if parameters_restored:
                        try:
                            selector_restored = client.write_register(
                                VPP_REMOTE_POWER_ENABLE,
                                int(original_remote[0]),
                                bypass_rate_limit=True,
                            )
                            if not selector_restored:
                                cleanup_errors.append(
                                    "VPP branch selector could not be restored"
                                )
                        except ModbusWriteError as exc:
                            cleanup_errors.append(
                                f"VPP branch selector could not be restored: {exc}"
                            )

                # Restore authority last. If it was originally zero, this also removes
                # authority from any bounded wake command that could not be cleared.
                try:
                    authority_restored = client.write_register(
                        VPP_CONTROL_AUTHORITY,
                        int(original_authority),
                        bypass_rate_limit=True,
                    )
                    if not authority_restored:
                        cleanup_errors.append(
                            "VPP control authority could not be restored"
                        )
                except ModbusWriteError as exc:
                    cleanup_errors.append(
                        f"VPP control authority could not be restored: {exc}"
                    )
        except ModbusWriteError as exc:
            cleanup_errors.append(f"wake release batch could not start: {exc}")

    if cleanup_errors:
        cleanup_message = "; ".join(cleanup_errors)
        if operation_error is not None:
            raise BatteryWakeError(
                f"{operation_error}; cleanup also failed: {cleanup_message}"
            ) from operation_error
        raise BatteryWakeError(f"Could not fully release the APX wake pulse: {cleanup_message}")

    if operation_error is not None:
        raise operation_error
