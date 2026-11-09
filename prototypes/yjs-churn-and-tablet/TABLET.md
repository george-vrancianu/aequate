# Running the tablet benchmark (human steps)

Goal: measure how long a 1k / 3k / 5k / 10k-stroke Yjs board takes to sync, open and render on the iPad (and any other low-end tablet or Chromebook), over your real Wi-Fi, against a Hocuspocus server running on this PC (WSL2). About 15 minutes. Nothing is installed on the tablet.

## 1. Install (once, in WSL)

```
git fetch origin prototype/yjs-churn-and-tablet
git worktree add ~/aequate-tablet origin/prototype/yjs-churn-and-tablet   # separate folder, the main checkout stays untouched
cd ~/aequate-tablet/prototypes/yjs-churn-and-tablet
npm install
```

## 2. Start the server (WSL terminal, leave it running)

```
npm run tablet
```

Default port 8787. Another port: `PORT=9000 npm run tablet` or `npm run tablet -- --port 9000`. The server prints the Windows LAN URL, the WSL IP and the exact commands for steps 3 and 4 with your numbers filled in. Use those printed commands rather than the examples below if they differ. If the Windows LAN IP could not be detected, run `ipconfig` in Windows and take the IPv4 address of the Wi-Fi adapter (the one the tablet is also on).

## 3. Windows networking: pick the path for your WSL2 mode

Check the mode in WSL: `wslinfo --networking-mode` prints `mirrored` or `nat` (Windows side: `networkingMode` in `%UserProfile%\.wslconfig`). The server detects it and prints the commands for your mode with your port and IPs filled in; use the printed ones. Force a mode for the printout with `WSL_MODE=nat npm run tablet` (only changes what is printed). All commands are in an **Administrator PowerShell**.

### 3a. Mirrored mode (this PC's mode)

WSL shares the Windows network interfaces, so the tablet connects straight to the Windows LAN IP (the same address as `eth0` in WSL). **Do not add a portproxy** (it would point at its own address and port). Inbound traffic is blocked by two firewalls, so add one rule to each:

```
New-NetFirewallHyperVRule -Name aequate-proto-8787 -DisplayName "aequate-proto-8787" -Direction Inbound -VMCreatorId '{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}' -Protocol TCP -LocalPorts 8787
New-NetFirewallRule -DisplayName "aequate-proto-8787" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8787
```

The first opens the Hyper-V firewall for WSL (default inbound action is Block; the VMCreatorId is WSL's fixed id, `Get-NetFirewallHyperVVMCreator` lists it). The second is the normal Windows Defender Firewall rule. Verify: `Get-NetFirewallHyperVRule -Name aequate-proto-8787`.

### 3b. NAT mode

WSL2 sits behind a virtual NAT, so Windows must forward the port to the WSL IP:

```
netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=8787 connectaddress=<WSL-IP> connectport=8787
New-NetFirewallRule -DisplayName "aequate-proto-8787" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8787
```

`<WSL-IP>` is the `eth0` address printed by the server (also `hostname -I` in WSL). It changes when WSL restarts; if the tablet stops connecting, delete and re-add the portproxy. The firewall rule can also be written `netsh advfirewall firewall add rule name="aequate-proto-8787" dir=in action=allow protocol=TCP localport=8787`.

### Both modes

If it still cannot connect, the Wi-Fi network profile may be "Public": Settings > Network > Wi-Fi > your network > Private. The Windows LAN IP the server prints is looked up with PowerShell; if it shows `<WINDOWS-LAN-IP>`, run `ipconfig` and take the IPv4 address of the Wi-Fi adapter the tablet is also on. Not tested against a real tablet from this session (the machine could only be checked from itself over its LAN IP).

## 5. Open it on the iPad

1. iPad on the **same Wi-Fi** as the PC (not a guest network with client isolation, no VPN). Turn off Low Power Mode, set Auto-Lock to Never for the test.
2. Safari: `http://<Windows-LAN-IP>:8787/` (plain http is fine). You should see the page "PROTOTYPE: Yjs board benchmark".
3. Sanity check from the PC first if you want: open the same URL in a Windows browser.

## 6. Run

1. Tap a size (start with **1k**) and a layout, then **1. Seed on server**, then **2. Run measurements**. Each run takes tens of seconds; keep Safari in the foreground and the screen on.
2. Or tap **Run ALL** for all 4 sizes x 2 layouts (about 5 to 10 minutes on a slow device; the 10k runs are the interesting ones). If it stalls, the log box shows the last step.
3. A result table appears. iOS Safari has no `performance.memory`, so the heap column shows "n/a". That is expected. Chromium-based browsers (Chromebook, Android Chrome) do expose it, but over plain http without `--enable-precise-memory-info` the value is bucketed and can be stale (a 1k board read 9.5 MB at all four points in a check), so the page marks it "(coarse)" and records `preciseMemory: false` in the JSON. Do not use tablet heap numbers for sizing; the encoded doc bytes and the timings are the usable columns.
4. The `/stream` step leaves 100 tombstones in the held server doc on every run, so `docBytes` drifts upward slightly when you repeat a size. "Seed on server" skips a board that is already seeded, so for a clean repeat open `http://<Windows-LAN-IP>:8787/reset` in a browser tab first (it drops the held docs), then seed again. Run ALL seeds each size itself but does not reset.

## 7. Copy the JSON back

1. Tap **Copy results as JSON**. On plain http iPad Safari blocks the clipboard API; the page then selects the text in the box below it and says so. Tap in the box, **Select All**, **Copy** from the bubble.
2. Paste it into the ticket / a file / the chat. It contains the device user agent, so no extra notes about the device are needed (but do add the iPad model, iOS version and Wi-Fi band if you know them).
3. Repeat on a second device (cheap Android tablet, Chromebook) if available: same URL.

## 8. Cleanup

Stop the server with Ctrl+C in the WSL terminal. Then in the admin PowerShell.

Mirrored mode:

```
Remove-NetFirewallHyperVRule -Name aequate-proto-8787
Remove-NetFirewallRule -DisplayName "aequate-proto-8787"
```

NAT mode:

```
netsh interface portproxy delete v4tov4 listenaddress=0.0.0.0 listenport=8787
Remove-NetFirewallRule -DisplayName "aequate-proto-8787"
```

(or `netsh advfirewall firewall delete rule name="aequate-proto-8787"`). Verify with `Get-NetFirewallHyperVRule -Name aequate-proto-8787` (should error: not found) and, in NAT mode, `netsh interface portproxy show v4tov4` (should be empty). Remove the worktree with `git worktree remove ~/aequate-tablet`. Server data lives only in memory, nothing else to delete.

## What it measures

Per size and layout: time to sync and open the whole board (median of 3 fresh connects), time to open one page (for one-doc-per-board that is the same doc), apply time per remote stroke while the server streams 100 strokes 30 ms apart, time to decode and draw all strokes to a canvas (one page and the whole board), encoded doc bytes, JS JS heap where available (coarse on plain http, see step 6), and the HTTP round trip to the server. Times include real Wi-Fi latency and bandwidth.
