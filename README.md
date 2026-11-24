# Quiet Frame

Quiet Frame is a full-screen daily artwork app for Samsung Tizen TVs. The local time and date sit over the artwork, with Prime Video, YouTube, and Jellyfin in a small dock. The artwork, icons, and code are bundled. Quiet Frame has no accounts, analytics, ads, or network access.

## Remote

- **Left / Right** moves between shortcuts. **Up / Down** returns focus to the current shortcut.
- **OK** opens the selected app when the TV permits it. If the request fails, press **Home** and open the app from Samsung Home.
- **Back** dismisses a status message or exits Quiet Frame.

## Configure and build

1. Edit [app/shortcuts.js](app/shortcuts.js) and add one object per shortcut with a `label`, optional `initials` and bundled `icon`, and the exact Tizen `appId`. Verify the ID from the target's `tizen:application id` manifest field or documented application metadata. Jellyfin's [published manifest](https://github.com/jellyfin/jellyfin-tizen/blob/master/config.xml) gives its application ID as `AprZAARz4r.Jellyfin` and its package ID as `AprZAARz4r`. The Tizen application launch API remains subject to the TV's app and firmware policy.
2. Install [Tizen Studio and the Samsung TV Extension](https://developer.samsung.com/smarttv/develop/getting-started/setting-up-sdk/installing-tv-sdk.html) and configure a signing profile supported by your TV. Run `bash tools/build.sh PROFILE_NAME` with `tizen` on your PATH, or set `TIZEN_CLI` to the SDK executable. The signed WGT is written to `dist/`.
3. Use [Samsung's developer-device installation procedure](https://developer.samsung.com/smarttv/develop/getting-started/using-sdk/tv-device.html) and choose this WGT. The app's ID is `Qf7aKp2LmN.QuietFrame`. Launch it from the SDK, or open it from Apps and use Add to Home if the TV offers that option for the developer-installed build.

For browser preview, open `app/index.html` directly. To reproduce the simulated remote checks, install Playwright for Python, run `python -m playwright install chromium`, and run `python tests/ui.py`. The simulation checks bundled offline rendering, navigational focus, the exact launch request, error and timeout behavior, and Back. Hardware installation, cross-app launch, and startup behavior need a TV test.

The coastal painting generated for Quiet Frame is used if the daily artwork cannot load. The launcher icon is an original coastal scene in [SVG](app/assets/quiet-frame.svg), exported as a PNG for Tizen.

## Daily gallery

Quiet Frame ships with 38 paintings from [The Cleveland Museum of Art Open Access program](https://www.clevelandart.org/open-access). Each selected record expressly designates the image CC0 and supplies its matching museum JPEG. [The bundled gallery manifest](app/gallery.js) records the artist, title, museum, accession, object page, source image, and per-object rights evidence. The images are resized to fit a 1920 × 1080 box without changing aspect ratio and displayed whole against a dark matte.

The device-local civil date selects a fixed entry each day. Midnight and return from sleep pick up the current date. The index repeats after the last painting. Run `python tests/gallery.py` to check offline rollover, restart, resume, daylight-saving changes, and the decode fallback.

## Shortcut artwork

A checkout uses initials unless local icons are supplied. The personalized build uses publisher-provided app artwork from [Prime Video](https://apps.apple.com/us/app/amazon-prime-video/id545519333), [YouTube](https://apps.apple.com/us/app/youtube-watch-listen-stream/id544007664), and [Jellyfin Mobile](https://apps.apple.com/us/app/jellyfin-mobile/id1480192618). Place appropriately licensed replacements in the ignored `app/assets/local-shortcuts/` folder using the filenames in `app/shortcuts.js`. The app uses local files only. The third-party marks are outside the source repository.

## Power and startup on The Frame

The target is Samsung's 2022 43-inch The Frame, model QN43LS03BAFXZA, Tizen 6.5 generation. Samsung documents **Settings → All Settings → General & Privacy → Start Screen Options → Autorun Last App** for compatible 2022 TVs. It depends on model and app support. The setting follows the most recent eligible app, so using Jellyfin afterward could change which app the TV selects. The published documentation does not establish eligibility for this developer-installed WGT or behavior after AC power loss. The unit's firmware revision and behavior remain unverified. [Exact-model e-manual listing](https://www.samsung.com/latin_en/support/model/QN43LS03BAFXZA/) · [Samsung 2022 startup settings](https://www.samsung.com/au/support/tv-audio-video/use-autorun-start-screen-options-on-your-samsung-tv/)

- **Resume** is the return to a suspended app while the TV still has its state. Quiet Frame restores shortcut focus when it becomes visible. Samsung's multitasking guide describes app switching separately from startup. [Samsung Developer](https://developer.samsung.com/smarttv/develop/guides/fundamentals/multitasking.html)
- **Art Mode** is a system display mode. A short Power press switches between TV mode and Art Mode; holding Power turns the set fully off. Art Mode can show personal images imported by USB, independent of Quiet Frame. [2022 Samsung support](https://www.samsung.com/levant/support/tv-audio-video/2022-how-to-troubleshoot-when-the-frame-automatically-turns-off/) · [Personal photos in Art Mode](https://www.samsung.com/us/support/answer/ANS10005239/)
- **Cold boot and kiosk** have no documented supported startup path for a developer-installed WGT on this consumer model. Samsung ended its old background prelaunch feature for consumer Smart TVs starting in 2019. Samsung's application-installation FAQ describes automatic launch for hotel TVs with server-installed apps from Tizen 6.5, a separate product and deployment path. For everyday use, open Quiet Frame manually after installation. [Samsung prelaunch guidance](https://developer.samsung.com/smarttv/develop/guides/fundamentals/prelaunching-applications.html) · [Samsung installation FAQ](https://developer.samsung.com/smarttv/develop/faq/application-installation.html)

An on-TV test should record the software version and check first launch, Jellyfin handoff, return from Home, Art Mode wake, full power-off, and (if startup settings changes are approved) Autorun Last App with Quiet Frame and then with Jellyfin as the most recently used app.
