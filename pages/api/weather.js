/**
 * Weather API Route
 *
 * Proxies requests to wttr.in (keyless, no account required).
 * Endpoint: GET /api/weather?city=<city>
 *
 * Returns structured weather data including current conditions and
 * a 3-day forecast derived from the wttr.in JSON format (j1).
 */

const WTTR_BASE = 'https://wttr.in';
const REQUEST_TIMEOUT_MS = 8000;

/**
 * Map wttr.in weather code to a human-readable description.
 * Full code list: https://www.worldweatheronline.com/weather-api/api/docs/weather-icons.aspx
 */
function describeWeatherCode(code) {
  const n = Number(code);
  if (n === 113) return 'Sunny / Clear';
  if (n === 116) return 'Partly Cloudy';
  if (n === 119) return 'Cloudy';
  if (n === 122) return 'Overcast';
  if ([143, 248, 260].includes(n)) return 'Fog / Mist';
  if ([176, 293, 296].includes(n)) return 'Light Rain';
  if ([179, 323, 326].includes(n)) return 'Light Snow';
  if ([182, 185, 281, 284].includes(n)) return 'Sleet / Freezing Drizzle';
  if ([200, 386, 389, 392, 395].includes(n)) return 'Thunderstorm';
  if ([227, 230].includes(n)) return 'Blizzard';
  if ([299, 302, 305, 308, 314, 353, 356].includes(n)) return 'Rain';
  if ([311, 312, 317, 320].includes(n)) return 'Sleet';
  if ([329, 332, 335, 338, 350, 359, 362, 365, 368, 371, 374, 377].includes(n)) return 'Snow / Sleet';
  return 'Unknown';
}

/**
 * Select a representative emoji for the weather code.
 */
function weatherEmoji(code) {
  const n = Number(code);
  if (n === 113) return '☀️';
  if (n === 116) return '⛅';
  if ([119, 122].includes(n)) return '☁️';
  if ([143, 248, 260].includes(n)) return '🌫️';
  if ([176, 293, 296, 299, 302, 305, 308, 353, 356].includes(n)) return '🌧️';
  if ([179, 323, 326, 329, 332, 335, 338].includes(n)) return '🌨️';
  if ([200, 386, 389, 392, 395].includes(n)) return '⛈️';
  return '🌡️';
}

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { city } = req.query;

  if (!city || !city.trim()) {
    return res.status(400).json({ error: 'city parameter is required' });
  }

  const encodedCity = encodeURIComponent(city.trim());
  const url = `${WTTR_BASE}/${encodedCity}?format=j1`;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  let raw;
  try {
    const response = await fetch(url, { signal: controller.signal });
    clearTimeout(timeoutId);

    if (!response.ok) {
      // wttr.in returns 404 for unknown locations
      if (response.status === 404) {
        return res.status(404).json({ error: `Location "${city}" not found.` });
      }
      return res.status(502).json({ error: `Upstream weather service returned ${response.status}.` });
    }

    raw = await response.json();
  } catch (err) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      return res.status(504).json({ error: 'Weather service timed out. Please try again.' });
    }
    return res.status(502).json({ error: 'Unable to reach weather service. Check your connection.' });
  }

  // Validate minimal expected shape from wttr.in j1 format
  if (!raw?.current_condition?.[0] || !raw?.weather?.[0]) {
    return res.status(502).json({ error: 'Unexpected response from weather service.' });
  }

  const cc = raw.current_condition[0];
  const nearestArea = raw.nearest_area?.[0];

  // Build structured current conditions
  const current = {
    tempC: Number(cc.temp_C),
    tempF: Number(cc.temp_F),
    feelsLikeC: Number(cc.FeelsLikeC),
    feelsLikeF: Number(cc.FeelsLikeF),
    humidity: Number(cc.humidity),
    windSpeedKmph: Number(cc.windspeedKmph),
    windDir: cc.winddir16Point,
    visibilityKm: Number(cc.visibility),
    weatherCode: cc.weatherCode,
    description: describeWeatherCode(cc.weatherCode),
    emoji: weatherEmoji(cc.weatherCode),
    uvIndex: Number(cc.uvIndex),
    cloudCover: Number(cc.cloudcover),
    observedAt: cc.observation_time,
  };

  // Build 3-day forecast
  const forecast = raw.weather.slice(0, 3).map((day) => {
    const hourly = day.hourly || [];
    // Pick representative icons from noon (index 4 = 12:00) or fall back to first
    const noonHour = hourly[4] || hourly[0] || {};
    return {
      date: day.date,
      maxTempC: Number(day.maxtempC),
      minTempC: Number(day.mintempC),
      maxTempF: Number(day.maxtempF),
      minTempF: Number(day.mintempF),
      avgHumidity: hourly.length > 0
        ? Math.round(hourly.reduce((s, h) => s + Number(h.humidity), 0) / hourly.length)
        : 0,
      weatherCode: noonHour.weatherCode || day.hourly?.[0]?.weatherCode,
      description: describeWeatherCode(noonHour.weatherCode || day.hourly?.[0]?.weatherCode),
      emoji: weatherEmoji(noonHour.weatherCode || day.hourly?.[0]?.weatherCode),
      sunrise: day.astronomy?.[0]?.sunrise,
      sunset: day.astronomy?.[0]?.sunset,
    };
  });

  // Resolve display name
  const locationName =
    nearestArea?.areaName?.[0]?.value ||
    nearestArea?.region?.[0]?.value ||
    city.trim();
  const country = nearestArea?.country?.[0]?.value || '';

  res.setHeader('Cache-Control', 's-maxage=300, stale-while-revalidate=60');
  return res.status(200).json({
    location: { name: locationName, country, query: city.trim() },
    current,
    forecast,
  });
}
