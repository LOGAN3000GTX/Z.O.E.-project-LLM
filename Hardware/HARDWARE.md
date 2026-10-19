# ZOE Hardware

[Back to the project overview](README.md)

ZOE uses a Raspberry Pi as its main computer, a USB speakerphone for voice interaction, two servos for movement, RGB lighting and an IMX500 camera. The electronics are being integrated with a custom aircraft enclosure and support stand.

The latest confirmed functional update is **16 October 2026**: servos respond to requests, RGB and sound work, and the camera hardware works. Image interpretation remains pending until a vision model is connected.

## Electronics Overview

| Component | Role in ZOE | Interface used or prepared | Current status |
|---|---|---|---|
| Raspberry Pi 5, 8 GB RAM | Runs the application, local language model and speech-recognition software | USB, camera connector and GPIO | Operating |
| Jabra Speak2 55 MS | Records commands and plays Betty replies and audio | USB audio | Recording and playback working |
| Two SG90 servos | Provide independent movement for the two canards | GPIO control signals in the saved implementation | Respond to requests; final linkage calibration pending |
| RGB LEDs | Provide colour and engine-light effects | GPIO-controlled RGB channels | RGB control working; final module count and wiring to be documented |
| Raspberry Pi AI Camera with IMX500 | Captures images for the perception subsystem | Camera ribbon connection | Hardware working; vision model not yet connected |

The aircraft design reserves **two RGB mounting positions**, one in each engine housing. This describes the mechanical layout, rather than a verified count of independently controlled lighting channels in the final assembly.

## Main Computer

### Raspberry Pi 5

The Raspberry Pi 5 with 8 GB RAM coordinates the prototype. It runs:

- Qwen2.5:3b through Ollama for conversation and structured command generation
- whisper.cpp for speech recognition
- The Python application that validates and executes device commands
- Camera capture and the prepared image-analysis interface
- Audio recording and playback tools

The local language model returns a proposed action. Python checks its structure and permitted arguments before calling the appropriate hardware module.

Local language-model inference runs on the Raspberry Pi CPU. An external AI accelerator is not part of the current project configuration or planned additions.

Dynamic Betty speech currently uses the Fish Audio online service. Running Qwen locally therefore does not make the entire voice pipeline offline.

## Voice Interface

### Jabra Speak2 55 MS

The Jabra speakerphone provides both the microphone and speaker through USB. It records spoken requests and plays generated replies and sound effects.

The saved application selects the ALSA device `plughw:CARD=MS,DEV=0`. Its recording path uses 48 kHz audio, followed by conversion to 16 kHz for Whisper.

Recording and playback have been confirmed. Some complete commands and individual words are still recognised incorrectly, so speech-input reliability remains an integration task.

## Actuation

### Two SG90 Servos

Two SG90 servos are used for the two independent canard mechanisms. Their control logic is separated into `servo_control.py`, which exposes validated movement commands to the main application.

The saved configuration is:

| Channel | BCM GPIO | Physical header pin | Permitted command range |
|---|---:|---:|---|
| Servo 1 | 17 | 11 | 60–120 degrees |
| Servo 2 | 27 | 13 | 60–120 degrees |

These values describe the saved software configuration. They must be checked against the actual operating build before being used as an assembly wiring reference.

Servos now respond to requests. The permitted command range is an initial software limit, not a measured range of canard movement. The final linkage requires neutral-position calibration and loaded-motion tests. There is no independent position-feedback sensor in the current servo module.

## Lighting

### RGB Engine Lights

RGB lighting gives the aircraft visible responses to colour and engine-effect commands. The software work includes static colours, on/off control and pulsing engine modes.

The CAD design places a light in each engine housing and provides cable passages toward the central compartment and support tube. RGB control is working on the prototype.

The exact LED-module model, common-anode or common-cathode arrangement, resistor or driver components, and final GPIO allocation still need to be recorded from the assembled circuit. These details should be added before publishing a reproducible wiring diagram.

Lighting commands are handled separately from servo requests. A correction was supplied to prevent a selected RGB command from also executing servo actions; this remains an important hardware regression test.

## Camera

### Raspberry Pi AI Camera with IMX500

The IMX500 camera supplies image capture for ZOE. Its housing and mounting points are included in the aircraft CAD, with the camera tilted 15 degrees upward.

Camera hardware operation is confirmed. The prepared software captures a fresh image and provides a separate path for sending it to an image-capable model. The operating build does not yet have that vision model connected.

Qwen2.5:3b is used for text conversation and commands in this project. Image interpretation is a separate integration step; a working camera alone does not mean that ZOE can describe its surroundings.

## Planned Additions

These items are tracked separately from the demonstrated functions above.

| Item | Intended role | Integration status |
|---|---|---|
| VL53L0X rangefinder | Distance readings that ZOE can report | Planned integration; no completed measurement workflow reported |
| ESP32 over USB | Alternative controller for servos, lighting and sensors if required by the final layout | Discussed option; the saved servo implementation uses direct Raspberry Pi GPIO |

A powered yaw mechanism, thermal sensing, radar and battery operation remain later project work. Vision-model integration will be evaluated using the current Raspberry Pi and camera setup.

## Power and Assembly Documentation

The integration plan separates the Raspberry Pi supply from actuator power. The final power-supply models, ratings, distribution wiring and measured current draw have not yet been recorded in a complete assembly specification.

Before the hardware can be reproduced reliably, the project documentation needs:

- A photograph and labelled wiring diagram of the operating circuit
- Exact power-supply and RGB-module models
- Final GPIO assignments and connector labels
- Servo calibration values for the assembled canards
- Physical checks of cable routing, camera clearance and service access
- Measurements of idle and combined operating loads

The existing [system workflow diagram](docs/images/zoe-llm-workflow.png) explains how information moves through ZOE. It is not an electrical wiring diagram.
