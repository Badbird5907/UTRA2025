# Baylee

This is team `Something interesting.`'s UTRAHacks 2025 Submission (code)!

We won the MLH award for best use of gen ai!

[Devpost](https://devpost.com/software/baylee) | [UTRA Hacks 2025](https://utra-hacks-2025.devpost.com/)


## Architecture
Baylee works in kind of a microservice-like architecture.
- `ioserver` runs as a systemd service on a raspberry pi, and exposes a websocket to control it.
- `brain` runs as a node server on a laptop, and listens to redis pub/sub messages. This service controlls prompting AI models (locally)
- `scribe` runs on either a laptop or the pi, and runs [OpenAI's Whisper](https://github.com/openai/whisper) model on CUDA or CPU.
- `Realsense` runs on either a laptop or the pi, and connects to a [Intel Realsense](https://www.intelrealsense.com/) depth camera to preform AI stuff.
