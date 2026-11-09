# Running the tablet benchmark (human steps)

Goal: measure how long a 1k / 3k / 5k / 10k-stroke Yjs board takes to sync, open and render on the iPad (and any other low-end tablet or Chromebook), over your real Wi-Fi, against a Hocuspocus server running on this PC (WSL2). About 15 minutes. Nothing is installed on the tablet.

## 1. Install (once, in WSL)

```
cd /home/giu/projects/aequate/prototypes/yjs-churn-and-tablet     # on the branch prototype/yjs-churn-and-tablet
npm install
```

## 2. Start the server (WSL terminal, leave it running)

```
npm run tablet
```

Default port 8787. Another port: `PORT=9000 npm run tablet` or `npm run tablet -- --port 9000`. The server prints the Windows LAN URL, the WSL IP and the exact commands for steps 3 and 4 with your numbers filled in. Use those printed commands rather than the examples below if they differ. If the Windows LAN IP could not be detected, run `ipconfig` in Windows and take the IPv4 address of the Wi-Fi adapter (the one the tablet is also on).

## 3. Windows port proxy (WSL2 is NATed, the tablet cannot reach it otherwise)

Open **PowerShell as Administrator**:

```
netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=8787 connectaddress=<WSL-IP> connectport=8787
```

`<WSL-IP>` is the `eth0` address printed by the server (also `hostname -I` in WSL). It changes when WSL restarts; if the tablet stops connecting, delete and re-add the rule.

## 4. Windows firewall rule (same admin PowerShell)

```
New-NetFirewallRule -DisplayName "aequate-proto-8787" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8787
```

Equivalent: `netsh advfirewall firewall add rule name="aequate-proto-8787" dir=in action=allow protocol=TCP localport=8787`.

If it still cannot connect, the Wi-Fi network profile may be "Public": Settings > Network > Wi-Fi > your network > Private.

## 5. Open it on the iPad

1. iPad on the **same Wi-Fi** as the PC (not a guest network with client isolation, no VPN). Turn off Low Power Mode, set Auto-Lock to Never for the test.
2. Safari: `http://<Windows-LAN-IP>:8787/` (plain http is fine). You should see the page "PROTOTYPE: Yjs board benchmark".
3. Sanity check from the PC first if you want: open the same URL in a Windows browser.

## 6. Run

1. Tap a size (start with **1k**) and a layout, then **1. Seed on server**, then **2. Run measurements**. Each run takes tens of seconds; keep Safari in the foreground and the screen on.
2. Or tap **Run ALL** for all 4 sizes x 2 layouts (about 5 to 10 minutes on a slow device; the 10k runs are the interesting ones). If it stalls, the log box shows the last step.
3. A result table appears. Note that iOS Safari has no `performance.memory`, so the heap column shows "n/a". That is expected (Chromium-based browsers show it; on a Chromebook/Android Chrome you get heap numbers).

## 7. Copy the JSON back

1. Tap **Copy results as JSON**. On plain http iPad Safari blocks the clipboard API; the page then selects the text in the box below it and says so. Tap in the box, **Select All**, **Copy** from the bubble.
2. Paste it into the ticket / a file / the chat. It contains the device user agent, so no extra notes about the device are needed (but do add the iPad model, iOS version and Wi-Fi band if you know them).
3. Repeat on a second device (cheap Android tablet, Chromebook) if available: same URL.

## 8. Cleanup

Stop the server with Ctrl+C in the WSL terminal. Then in the admin PowerShell:

```
netsh interface portproxy delete v4tov4 listenaddress=0.0.0.0 listenport=8787
Remove-NetFirewallRule -DisplayName "aequate-proto-8787"
```

(or `netsh advfirewall firewall delete rule name="aequate-proto-8787"`). Verify with `netsh interface portproxy show v4tov4` (should be empty). Server data lives only in memory, nothing else to delete.

## What it measures

Per size and layout: time to sync and open the whole board (median of 3 fresh connects), time to open one page (for one-doc-per-board that is the same doc), apply time per remote stroke while the server streams 100 strokes 30 ms apart, time to decode and draw all strokes to a canvas (one page and the whole board), encoded doc bytes, JS heap where available, and the HTTP round trip to the server. Times include real Wi-Fi latency and bandwidth.
