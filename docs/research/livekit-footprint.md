# LiveKit self-hosting footprint for 6 participants

Ticket: [#7](https://github.com/george-vrancianu/aequate/issues/7) (part of #1). Researched 2026-10-08 against LiveKit docs (rendered 2026-10-08), `livekit/livekit` master, `livekit/client-sdk-js` main, `livekit/mediatransportutil`, `livekit/deploy`, `livekit/livekit-helm`, `livekit/livekit-cli` and the coturn README.

**Question.** What does self-hosted LiveKit need for 2 to 6 participants with video, voice and screen share? This covers CPU and bandwidth per participant, simulcast settings, whether coturn is needed, ports, the minimum VPS, the audio-only fallback, screen share cost and deployment options.

Scenario assumed throughout: one room, one tutor and up to 5 students. Everyone publishes camera and mic, and at most one screen share runs at a time. This matches the Aequate customer in `docs/handoff.md` section 1.

---

## 1. What LiveKit itself publishes about sizing

- The docs say LiveKit's scalability "is bound by CPU and bandwidth". They recommend running "production setups on 10Gbps ethernet or faster", say "compute-optimized instance types are the most suitable", and say "if running in a Dockerized environment, host networking should be used for optimal performance."
  Source: https://docs.livekit.io/transport/self-hosting/deployment.md (section "Resources")
- **The docs give no minimum VM size and no per-participant CPU or bandwidth figure.** The only first-party numbers are max-capacity benchmarks for a single room on a 16-core `c2-standard-16`:
  - Audio only: 10 publishers and 3000 subscribers used 80% CPU, with 7.3 kBps in and 23 MBps out.
  - Video at 720p with simulcast: 150 publishers and 150 subscribers used 85% CPU, with 50 MBps in, 93 MBps out and 762,749 packets/s out.
  - Livestream: 1 publisher and 3000 subscribers used 92% CPU, with 531 MBps out and 560,962 packets/s out.

  Source: https://docs.livekit.io/transport/self-hosting/benchmark.md
- The same page says the work an SFU does depends on "number of tracks published, number of subscribers, amount of data sent to each subscriber". It also says "each room must fit within a single node". Source: same benchmark page.
- The Helm chart's commented-out example for Kubernetes nodes requests 4 to 6 CPU and 2 GiB of memory, and mentions `c5.2xlarge`. It says only one LiveKit pod can run per node, so "we recommend giving it plenty of resources". This is advice for a multi-node cluster, not a stated minimum.
  Source: https://github.com/livekit/livekit-helm/blob/master/livekit-server/values.yaml (`resources:` block)
- Self-hosted LiveKit is a "single-home SFU" with "single server per room" and supports "up to ~3,000" users per room. Source: https://docs.livekit.io/transport/self-hosting.md

### CPU per participant (my estimate, not a LiveKit number)

The benchmarks imply a forwarding rate of about 35k to 55k packets/s per core:
- 762,749 pps over 85% of 16 cores is about 56k pps/core.
- 560,962 pps over 92% of 16 cores is about 38k pps/core.

A 6-person room has 6 × 5 = 30 forwarded video streams and 30 forwarded audio streams.
- Video: assume about 150 to 200 packets/s per 720p stream at 1.7 Mbps with ~1,100-byte packets.
- Audio: about 50 packets/s per Opus stream at 20 ms frames.
- Together that is roughly 7k packets/s outbound, or about 0.15 to 0.2 of a core using the conservative 38k figure.

So the SFU forwarding load for one 6-person room is a small fraction of one vCPU. CPU is not the constraint on a 2 vCPU box. This is a straight-line extrapolation from LiveKit's numbers, and the spike must check it (section 9).

## 2. Bandwidth per participant (from SDK defaults)

LiveKit gives no per-participant bandwidth figure. The numbers below are the **bitrate caps** in the JS client SDK defaults. Real encoders usually run below these caps.

| Item | Default | Source |
| --- | --- | --- |
| Camera capture | 1280x720 (`VideoPresets.h720`) | [defaults.ts](https://github.com/livekit/client-sdk-js/blob/main/src/room/defaults.ts) `videoDefaults` |
| Camera codec | VP8, with `backupCodec: true` | same file, `defaultVideoCodec`, `publishDefaults` |
| Simulcast | on (`simulcast: true`) | same file; also https://docs.livekit.io/transport/media/advanced.md ("Simulcast is enabled by default in all LiveKit SDKs") |
| Simulcast layers (16:9) | h180 + h360, plus the original | [publishUtils.ts](https://github.com/livekit/client-sdk-js/blob/main/src/room/participant/publishUtils.ts) `defaultSimulcastPresets169`; [options.ts](https://github.com/livekit/client-sdk-js/blob/main/src/room/track/options.ts) "When left blank, it defaults to h180, h360" |
| Preset bitrates | h720 = 1.7 Mbps @30fps, h360 = 450 kbps @20fps, h180 = 160 kbps @20fps | options.ts `VideoPresets` |
| Mic | `AudioPresets.music` = 48 kbps, DTX on, RED on | defaults.ts `publishDefaults`; options.ts `AudioPresets` |
| Speech-only presets | `speech` = 24 kbps, `telephone` = 12 kbps | options.ts `AudioPresets` |
| Screen share | `ScreenSharePresets.h1080fps15` = 1920x1080 @15fps, 2.5 Mbps | defaults.ts `screenShareEncoding`; options.ts `ScreenSharePresets` |
| `adaptiveStream`, `dynacast` | **both default to `false`** in the JS SDK | defaults.ts `roomOptionDefaults` |

Per participant, at the default caps:
- **Upload** is about 2.3 Mbps of video (1.7 + 0.45 + 0.16 across three simulcast layers) plus 48 kbps of audio.
- **Download** is the sum of the layers the SFU forwards for the 5 other people:
  - 5 × 1.7 = 8.5 Mbps if every tile is shown at 720p.
  - 5 × 0.45 = 2.25 Mbps if tiles are about 360p, which is what adaptive stream picks for a grid.
  - Plus 5 × 48 kbps of audio.

Server totals for 6 participants, worst case with everyone at 720p:
- Ingress is about 6 × 2.35 ≈ 14 Mbps.
- Egress is about 6 × 8.7 ≈ 52 Mbps.

With adaptive stream and dynacast on and a grid layout, egress falls to roughly 15 Mbps.

Monthly traffic, worst case: 52 Mbps out is about 23 GB per lesson-hour. 40 lesson-hours a month is about 1 TB, which fits the traffic allowance of typical VPS plans.

### Simulcast settings to use

- **Keep simulcast on (the default) with VP8.** The docs say: "LiveKit will automatically select appropriate layers when it detects bandwidth constraints, upgrading to higher resolutions as conditions improve." Source: https://docs.livekit.io/transport/media/advanced.md ("Video simulcast")
- **Turn on `adaptiveStream: true` and `dynacast: true` in the Room options.** The JS SDK defaults both to false.
  - Adaptive stream "automatically coordinates with the server to send back the simulcast layer that best matches the UI element". It also pauses hidden tiles on the server. Source: https://docs.livekit.io/transport/media/subscribe.md ("Adaptive stream")
  - Dynacast "automatically pauses video layer publications when they aren't being consumed by subscribers". Source: https://docs.livekit.io/transport/media/advanced.md ("Dynacast")
  - In the JS SDK, adaptive stream only works if you use `Track.attach()`. Source: subscribe page above.
- VP9 and AV1 SVC (`L3T3_KEY` by default) improve bitrate efficiency, but they cost more encoder CPU on student tablets. Also, "Dynacast can only pause entire streams, not individual layers" with SVC. VP8 simulcast is the safer baseline. Source: https://docs.livekit.io/transport/media/advanced.md
- A 1:1 lesson or a tutor-focused layout can cap the camera at h540 or h360 through `publishDefaults.videoEncoding` and `videoSimulcastLayers`. The docs give a JS example. Source: https://docs.livekit.io/transport/media/advanced.md ("Video track configuration")

## 3. Screen share cost

- Screen share is "published as a video track, just like your camera". Source: https://docs.livekit.io/transport/media/screenshare.md
- **Default encoding** is 1080p @15fps with a 2.5 Mbps cap. Source: defaults.ts `screenShareEncoding`.
  - The SDK adds one simulcast layer at half resolution: 960x540 at max(150 kbps, 2.5 Mbps / 4) = 625 kbps. Source: publishUtils.ts `computeDefaultScreenShareSimulcastPresets`.
  - The sharer uploads up to about 3.1 Mbps.
  - The SFU forwards up to 5 × 2.5 = 12.5 Mbps.
- Lighter presets exist: `h720fps5` is 0.8 Mbps, and `h360fps3` is 0.2 Mbps. Source: options.ts `ScreenSharePresets`.
- **Screen share wins over camera when bandwidth runs short.** The server's stream allocator gives screen-share tracks the highest priority (`cPriorityDefaultScreenshare = cPriorityMax`) and camera tracks the lowest (`cPriorityDefaultVideo = cPriorityMin`). "If there is not enough bandwidth even for the lowest layer, tracks at lower priorities will be paused."
  Sources: https://github.com/livekit/livekit/blob/master/pkg/sfu/streamallocator/streamallocator.go, https://github.com/livekit/livekit/blob/master/pkg/sfu/streamallocator/track.go (`SetPriority`)
- Worst case on the server, with 6 cameras at 720p plus one 1080p share: about 17 Mbps in and about 65 Mbps out.
- For Aequate, the blackboard is synced over Yjs, not over video, so screen share is a secondary feature. Defaulting it to `h720fps5` or `h720fps15` (1.5 Mbps) is reasonable for slides and documents.

## 4. Audio-only fallback path

LiveKit has three layers of fallback.

1. **Automatic, on the server.** Congestion control is "enabled by default". Under heavy congestion, "SFU may choose to pause some tracks in order to allow others to stream smoothly" (`rtc.congestion_control.allow_pause`, default true).
   - The stream allocator only manages video. `AddTrack` returns early for any downtrack that is not `RTPCodecTypeVideo`.
   - So under congestion, video drops layers and then pauses, and **audio keeps flowing**.
   - The client receives `RoomEvent.TrackStreamStateChanged` with the paused state. The track "will be resumed automatically" when bandwidth recovers.

   Sources: https://github.com/livekit/livekit/blob/master/config-sample.yaml (`congestion_control`), streamallocator.go `AddTrack`, https://github.com/livekit/client-sdk-js/blob/main/src/room/events.ts (`TrackStreamStateChanged`)
2. **Explicit, in the app.** A subscriber can stop receiving a track with `publication.setEnabled(false)`. "disabling this track stops the LiveKit server from sending bytes until the track's data is needed again". A publisher can turn its camera off, and the mic can drop to `AudioPresets.speech` (24 kbps) or `telephone` (12 kbps).
   - Aequate can build an "audio only" button on these, triggered by the user or by `ConnectionQualityChanged`.

   Sources: https://docs.livekit.io/transport/media/subscribe.md ("Enabling/disabling tracks"), options.ts `AudioPresets`, events.ts `ConnectionQualityChanged`
3. **Connectivity.** `rtc.allow_tcp_fallback` (default true) "allows automatic connection fallback to TCP and TURN/TLS (if configured) when UDP has been unstable". Source: config-sample.yaml.

## 5. coturn vs embedded TURN

- **The embedded TURN server is enough. coturn is not required.** The docs say "LiveKit includes an embedded TURN server. It's a secure TURN implementation that has integrated authentication with the rest of LiveKit". Only clients that already have a signal connection can use it. It supports TURN/TLS (`turn.tls_port`) and TURN/UDP (`turn.udp_port`). Source: https://docs.livekit.io/transport/self-hosting/deployment.md ("Improving connectivity with TURN")
- The config reference says external TURN servers (`rtc.turn_servers`, for example coturn with a shared secret in `/var/lib/coturn/secret`) are optional: "This isn't necessary if using embedded TURN server". Source: https://github.com/livekit/livekit/blob/master/config-sample.yaml
- LiveKit's own VM generator sets up "a secure LiveKit installation with built-in TURN/TLS" and no coturn. Source: https://github.com/livekit/deploy/blob/main/generate/production.go
- Adding coturn would mean another daemon. Its defaults are 3478 UDP/TCP and 5349 TLS/DTLS, with a relay range of 49152 to 65535 UDP. It would compete for port 443 with the web app and LiveKit. Source: https://github.com/coturn/coturn/blob/master/README.md, https://github.com/coturn/coturn/blob/master/README.turnserver
- **Implication for `docs/handoff.md`:** the Media row "LiveKit + coturn" should become "LiveKit (embedded TURN)".
- TURN/TLS needs **its own domain and a CA-signed cert**: "self-signed certs do not work". `turn.domain` must match the cert. Source: deployment.md.

## 6. Ports to open

Reference table: https://docs.livekit.io/transport/self-hosting/ports-firewall.md

| Port | Purpose | Notes |
| --- | --- | --- |
| 7880/tcp | API + WebSocket signal | Not exposed. It sits behind a TLS-terminating proxy on 443. |
| 50000-60000/udp | ICE/UDP media | Each participant uses two ports. 6 people need about 12. |
| 7882/udp (alternative) | ICE/UDP mux | Replaces the range when `rtc.udp_port` is set. The sample config advises a port count of at least the vCPU count. |
| 7881/tcp | ICE/TCP fallback | "cannot be behind load balancer or TLS" (config-sample.yaml) |
| 3478/udp | TURN/UDP (embedded, optional) | Also serves STUN when enabled. |
| 5349/tcp, or 443 | TURN/TLS (embedded, optional) | "If not using LB, this port needs to be set to 443" |

The VM guide uses Docker Compose with Caddy. On one host it opens these ports:
- 443 for HTTPS and TURN/TLS
- 80 for TLS issuance
- 7881/tcp
- 3478/udp
- 50000-60000/udp

Source: https://docs.livekit.io/transport/self-hosting/vm.md ("Firewall")

The same page's `firewall-cmd` example opens 443/udp instead of 3478/udp, which is an inconsistency in the docs. Open both, or pick one and set `turn.udp_port` to match.

Port 443/tcp is shared through Caddy's layer-4 SNI routing:
- The TURN domain goes to `localhost:5349`.
- The main domain goes to `localhost:7880`.

Source: https://github.com/livekit/deploy/blob/main/generate/templates/caddy.go. Aequate's own web app can sit behind the same SNI router.

## 7. Deployment options LiveKit documents

LiveKit describes itself as "Easy to deploy: single binary, Docker or Kubernetes". Source: https://github.com/livekit/livekit/blob/master/README.md

- **Single binary.** Install with `curl -sSL https://get.livekit.io | bash` on Linux, Homebrew on macOS, or GitHub releases on Windows. Pass a config with `--config` or the `LIVEKIT_CONFIG` env var. Source: https://docs.livekit.io/transport/self-hosting/local.md, deployment.md
- **Docker.** The image is `livekit/livekit-server`.
  - The `livekit/generate` tool writes `docker-compose.yaml` (LiveKit, Caddy and Redis), `livekit.yaml`, `caddy.yaml`, and a cloud-init file or `init_script.sh`. It installs a `livekit-docker` systemd unit.
  - All services use `network_mode: "host"`. The template warns this "requires host networking, which is only available on Linux".
  - The docs say they tested on Ubuntu, Amazon Linux, Linode and Google Cloud.

  Sources: https://docs.livekit.io/transport/self-hosting/vm.md, https://github.com/livekit/deploy/blob/main/generate/templates/docker.go
- **Kubernetes.** A Helm chart exists. It needs host networking, which allows only one LiveKit pod per node. It also needs Redis and certificates for both domains. Source: https://docs.livekit.io/transport/self-hosting/kubernetes.md. This is overkill for Aequate.
- **Redis** is "recommended for production deploys". When it is set, "LiveKit will automatically operate in a fully distributed fashion". A single node can run without it. Sources: deployment.md, config-sample.yaml.
- **`--dev` caveats** (source: https://github.com/livekit/livekit/blob/master/cmd/server/main.go, https://github.com/livekit/mediatransportutil/blob/master/pkg/rtcconfig/config.go, https://github.com/livekit/livekit/blob/master/pkg/config/config.go):
  - The flag help text says it "sets log-level to debug, console formatter, and /debug/pprof. insecure for production".
  - If no keys are configured, it uses the placeholder pair `devkey` / `secret`.
  - With those placeholder keys and no `--bind`, it binds only to `127.0.0.1` and `::1`. The local guide says to pass `--bind 0.0.0.0` to reach it from other devices.
  - It uses one UDP mux port, **7882**, instead of 50000-60000. It narrows the TURN relay range to 30000-30002.
  - It has no TLS or TURN/TLS, so browsers on other machines need HTTPS on the page, and restrictive networks cannot connect. It is fine for local work, but not for the spike on a real VPS.

## 8. Answer

LiveKit publishes no minimum VPS size and no per-participant cost. Its own benchmarks put a 150-by-150 video room on 16 cores. Extrapolating, a single 6-person room forwards about 7k packets/s, which needs well under one vCPU. **Bandwidth is the real constraint, not CPU.** At the JS SDK's default caps (720p VP8 simulcast at 1.7 + 0.45 + 0.16 Mbps, 48 kbps Opus, 1080p15 screen share at 2.5 Mbps), each participant uploads about 2.4 Mbps and downloads 2 to 9 Mbps. The server peaks around 17 Mbps in and 65 Mbps out with all cameras at 720p and one screen share. That is about 15 Mbps out once adaptive stream and dynacast are enabled; both default to off in the JS SDK and must be turned on.

coturn is not needed. LiveKit's embedded TURN (TURN/TLS behind 443 using SNI, plus TURN/UDP) covers restrictive networks. It needs a second domain with a CA-signed cert.

Open these ports: 80/tcp, 443/tcp, 7881/tcp, 3478/udp (or 443/udp), and 50000-60000/udp (or the single mux port 7882/udp).

Audio-only fallback is built in. Under congestion the SFU pauses only video, never audio, and screen share has priority over cameras. The app can also disable video tracks explicitly.

For deployment, use LiveKit's generated Docker Compose with Caddy and host networking, or the single binary. `--dev` is insecure (placeholder keys, binds to localhost, pprof, no TLS or TURN) and is for local use only.

## 9. Recommendation for the VPS rental and media spike

**VPS to rent:** an x86 Linux VPS (Ubuntu LTS) with:
- **2 vCPU (dedicated if the price difference is small), 4 GB RAM**
- a public IPv4 address with no provider NAT
- a port of at least 1 Gbps
- at least 2 TB of monthly traffic
- a location in or near Romania or the EU

One example class is a Hetzner Cloud CCX13 (2 dedicated vCPU, 8 GB) or CPX21 (3 shared vCPU, 4 GB). I have not checked current plan names or prices. This matches handoff Spike 3 ("2 vCPU VPS"). The analysis above suggests LiveKit will use a small part of it, which leaves room to co-locate the rest of the stack later.

Also needed:
- Two DNS names pointing at the box, for example `rtc.<domain>` and `turn.<domain>`.
- The `livekit/generate` Docker Compose deployment.
- Simulcast left on, with `adaptiveStream: true` and `dynacast: true` set in the client.

**What the spike should measure**
1. **Real 6-person room.** Use 6 real browsers or devices: 1 tutor and 5 students, cameras at 720p, plus 5 minutes of 1080p15 screen share. Record:
   - server CPU (user, system and **steal**)
   - RSS memory
   - packets/s and Mbps in and out (`prometheus_port: 6789` plus `sar` or `vnstat`)
   - glass-to-glass latency
2. **Synthetic headroom.** Run `lk load-test --video-publishers 6 --subscribers 6 --layout 3x3 --duration 10m` (flags from https://github.com/livekit/livekit-cli/blob/main/cmd/lk/perf.go). Then raise to 2 and 3 concurrent rooms to find where the 2 vCPU box saturates. Compare against the ~38k-56k pps/core extrapolation.
3. **Adaptive stream and dynacast.** Measure egress Mbps with them off and on, for both a grid layout and a tutor-focus layout. This checks the 52 vs ~15 Mbps estimate.
4. **Audio-only degradation.** Throttle one student's downlink with `tc netem`, for example to 300 kbps with 5% loss. Confirm that video pauses (`TrackStreamStateChanged`), that audio stays intelligible, that screen share outlives camera tracks, and that video recovers afterwards.
5. **Connectivity.** Block UDP on a client (or test from a corporate or VPN network) and confirm ICE/TCP 7881 works. Then allow only 443/tcp and confirm TURN/TLS through Caddy SNI works.
6. **Student tablet encode cost.** Measure CPU and battery on an iPad or Surface while publishing VP8 720p simulcast. If it is too heavy, test h540 or h360 as the student default.
