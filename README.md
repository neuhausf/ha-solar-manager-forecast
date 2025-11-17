# Home Assistant Solar Manager Forecast Integration

This custom component integrates the **Solar Manager** cloud PV forecast with Home Assistant.  
It fetches the official Solar Manager production forecast (15-minute resolution for several days) and:

- exposes **power forecast sensors** (now, +15 min, +30 min),
- provides an **energy forecast** to Home Assistant’s **Energy Dashboard** (dotted solar forecast line).

---

## Installation

### HACS (recommended – as custom repository)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=neuhausf&repository=solarmanager-forecast&category=integration)

1. Go to **HACS** in your Home Assistant instance.
2. Open **Integrations**.
3. Click the three dots `⋮` in the top-right → **Custom repositories**.
4. Add the repository:

   - **URL**: `https://github.com/neuhausf/solarmanager-forecast`
   - **Category**: `Integration`

5. After adding the custom repository, search for **“Solar Manager Forecast”** in HACS → Install.
6. **Restart Home Assistant**.

### Manual installation

1. Download the [latest release](https://github.com/neuhausf/solarmanager-forecast/releases/latest).
2. Unpack the release and copy the directory:

   ```text
   custom_components/solar_manager_forecast
