# Installing Kodi on Apple TV 4K

Kodi is not available on the official App Store for Apple TV, so installing it requires sideloading via Xcode or AltStore. Here are both methods.

## Method 1: Sideload via Xcode (Recommended for Developers)

### Requirements
- A Mac with Xcode installed
- An Apple Developer account (free works, but app expires every 7 days; paid keeps it for 1 year)
- Your Apple TV 4K and Mac on the same Wi-Fi network

### Steps

1. **Enable Developer Mode on Apple TV**
   - Go to **Settings > System > Developer**
   - Turn on **Developer Mode**
   - Restart when prompted

2. **Pair Apple TV with Xcode**
   - Open Xcode on your Mac
   - Go to **Window > Devices and Simulators**
   - Your Apple TV should appear — click it and follow the pairing prompts

3. **Download the Kodi IPA / tvOS build**
   - Visit [kodi.tv/download](https://kodi.tv/download) and grab the tvOS `.ipa` file

4. **Sideload with iOS App Installer or Xcode**
   - In Xcode's Devices window, click the **+** under **Installed Apps**
   - Select the downloaded `.ipa`
   - Kodi will install to your Apple TV

5. **Trust the app**
   - On Apple TV go to **Settings > Users and Accounts > [your Apple ID] > Developer App**
   - Trust the certificate

---

## Method 2: AltStore (No Mac Required After Setup)

### Requirements
- A PC or Mac running AltServer
- AltStore installed on an iPhone/iPad (used as a relay)
- Apple TV 4K on the same network

### Steps

1. Install AltServer on your computer from [altstore.io](https://altstore.io)
2. Install AltStore on your iPhone via AltServer
3. Use AltStore's **Sources** to add the Kodi repo and install the tvOS build wirelessly to Apple TV

> Note: AltStore refreshes the app certificate every 7 days automatically as long as AltServer is running.

---

## Notes

- **Free Apple Developer accounts** require re-signing every 7 days; a **$99/year paid account** extends this to 1 year.
- Kodi on Apple TV 4K supports hardware-accelerated video playback, add-ons, and local/network media.
- Connecting a USB-C hub to Apple TV 4K (2nd gen) allows external storage for a local media library.
