#!/usr/bin/env python3
"""Two positional SG90 servos on Raspberry Pi 5 GPIO; no controller board."""

import argparse
from dataclasses import dataclass
import math
import os
import time


@dataclass(frozen=True)
class ServoConfig:
    gpio: int
    # These are nominal command angles, not measured shaft positions.
    min_angle: float = 0
    max_angle: float = 180
    min_pulse: float = 0.001
    max_pulse: float = 0.002
    # Start near the middle; adjust only after checking your mechanism.
    allowed_min: float = 60
    allowed_max: float = 120


# BCM GPIO numbers, NOT physical header pin numbers.
SERVOS = {
    1: ServoConfig(gpio=17),  # Physical pin 11.
    2: ServoConfig(gpio=27),  # Physical pin 13.
}

# Add names only after deciding their exact servo/angle meaning.
# Example (disabled): "forward plane": [{"servo": 1, "angle": 100}]
PRESETS = {}
SETTLE_SECONDS = 0.5  # A delay for travel, not position feedback.


class ServoController:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.config = dict(SERVOS)
        self._devices = {}
        self._factory = None
        self._closed = False
        pins = []
        for cfg in self.config.values():
            if type(cfg.gpio) is not int or not 2 <= cfg.gpio <= 27:
                raise ValueError("Use a BCM GPIO number between 2 and 27.")
            pins.append(cfg.gpio)
            numbers = (cfg.min_angle, cfg.max_angle, cfg.min_pulse,
                       cfg.max_pulse, cfg.allowed_min, cfg.allowed_max)
            if any(type(n) not in (int, float) or not math.isfinite(n) for n in numbers):
                raise ValueError("Servo calibration must contain finite numbers.")
            if not (cfg.min_angle <= cfg.allowed_min < cfg.allowed_max <= cfg.max_angle):
                raise ValueError("Allowed angles must lie within the calibrated range.")
            if not 0 < cfg.min_pulse < cfg.max_pulse < 0.020:
                raise ValueError("Servo pulse widths must be in seconds, below 0.020.")
        if len(set(pins)) != len(pins):
            raise ValueError("Each servo needs a different GPIO pin.")
        # No GPIO device is opened and no movement is commanded here.

    def catalog(self):
        """Give Qwen the available targets and limits, without touching GPIO."""
        return {
            "servos": [
                {"servo": sid, "minimum_angle": cfg.allowed_min,
                 "maximum_angle": cfg.allowed_max}
                for sid, cfg in self.config.items()
            ],
            "presets": PRESETS,
        }

    def validate_actions(self, actions):
        """Validate the ENTIRE list before any servo can be moved."""
        if not isinstance(actions, list) or len(actions) > 2:
            raise ValueError("Use at most two servo actions per request.")
        validated = []
        seen = set()
        for action in actions:
            if not isinstance(action, dict) or set(action) != {"servo", "angle"}:
                raise ValueError("Each action must contain only servo and angle.")
            sid, angle = action["servo"], action["angle"]
            if type(sid) is not int or sid not in self.config:
                raise ValueError("Choose servo 1 or servo 2.")
            if sid in seen:
                raise ValueError("Only one target angle per servo is allowed per request.")
            if type(angle) not in (int, float) or not math.isfinite(angle):
                raise ValueError("The angle must be a finite number.")
            cfg = self.config[sid]
            if not cfg.allowed_min <= angle <= cfg.allowed_max:
                raise ValueError(
                    f"Servo {sid} accepts {cfg.allowed_min:g} to {cfg.allowed_max:g} degrees."
                )
            seen.add(sid)
            validated.append({"servo": sid, "angle": float(angle)})
        return validated

    def _device(self, sid):
        if sid not in self._devices:
            try:
                from gpiozero import AngularServo
                from gpiozero.pins.lgpio import LGPIOFactory
            except ImportError as error:
                raise RuntimeError(
                    "Install gpiozero and lgpio in the Python environment used by ZOE."
                ) from error
            if self._factory is None:
                # Current GPIO Zero detects Pi 5 gpiochip0/gpiochip4 automatically.
                # An override is available for older OS/library combinations.
                chip = os.getenv("ZOE_GPIO_CHIP")
                self._factory = LGPIOFactory(**({"chip": int(chip)} if chip else {}))
            cfg = self.config[sid]
            self._devices[sid] = AngularServo(
                cfg.gpio, initial_angle=None,
                min_angle=cfg.min_angle, max_angle=cfg.max_angle,
                min_pulse_width=cfg.min_pulse, max_pulse_width=cfg.max_pulse,
                frame_width=0.020, pin_factory=self._factory,
            )
        return self._devices[sid]

    def rotate(self, servo, angle):
        """Send one absolute target angle; the servo holds it until exit."""
        if self._closed:
            raise RuntimeError("The servo controller has been closed.")
        action = self.validate_actions([{"servo": servo, "angle": angle}])[0]
        angle = action["angle"]
        if self.dry_run:
            print(f"DRY RUN: servo {servo} -> {angle:g} degrees; no GPIO output.", flush=True)
            return f"Simulation: servo {servo} would be commanded to {angle:g} degrees."
        self._device(servo).angle = angle
        time.sleep(SETTLE_SECONDS)
        # An SG90 provides no shaft-position feedback to this program.
        return f"Servo {servo} commanded to {angle:g} degrees."

    def close(self):
        """Stop pulses and release GPIO; this does not return servos to center."""
        self._closed = True
        devices, self._devices = self._devices, {}
        for device in devices.values():
            try:
                device.close()
            except Exception as error:
                print(f"GPIO cleanup error: {error}", flush=True)
        if self._factory is not None:
            factory, self._factory = self._factory, None
            factory.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("servo", type=int, choices=(1, 2))
    parser.add_argument("angle", type=float, help="Absolute target angle in degrees.")
    parser.add_argument("--dry-run", action="store_true", help="Print only; do not access GPIO.")
    args = parser.parse_args()
    try:
        with ServoController(dry_run=args.dry_run) as servos:
            print(servos.rotate(args.servo, args.angle))
            if not args.dry_run:
                input("Holding the target. Press Enter to release GPIO and exit: ")
        return 0
    except (KeyboardInterrupt, EOFError):
        return 0
    except Exception as error:
        print(f"Servo error: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
