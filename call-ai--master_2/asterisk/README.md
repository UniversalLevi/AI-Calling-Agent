## Asterisk Lab Setup (Phase 2)

This folder contains minimal configs to simulate calls between a softphone and a bot endpoint.

Files:
- `sip.conf` – defines two peers: `1001` (bot), `1002` (softphone)
- `extensions.conf` – routes calls; call `1001` or `1002`

Copy to `/etc/asterisk/` (backup originals first), then reload:
```bash
sudo asterisk -rx "sip reload" && sudo asterisk -rx "dialplan reload"
```

Register your softphone (Zoiper/Linphone) as:
- User: 1002
- Password: set in `sip.conf`
- Domain: your Asterisk server IP

Call `1001` to reach the bot line. By default, this rings the bot peer. To actually bridge media to the local bot process, you can:

1) Write a small AGI/ARI app that captures audio and streams it via UDP/TCP to the Phase 1 bot, or
2) Run a SIP user agent (e.g., `pjsua`/`baresip`) on the same machine as the bot that registers as `1001` and exchanges RTP with Asterisk. Then connect that UA's audio to the bot via a local virtual audio device or programmatic pipe.

These integration choices are implementation-specific; this repo provides the call scaffolding to test end-to-end signaling with zero carrier cost.


