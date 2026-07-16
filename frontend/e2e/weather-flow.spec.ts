import { expect, test } from "@playwright/test";

const locations = [
  {
    id: "open_meteo:3128760",
    provider: "open_meteo_geocoding",
    provider_id: 3128760,
    name: "Barcelona",
    display_name: "Barcelona, Cataluña, España",
    latitude: 41.38879,
    longitude: 2.15899,
    timezone: "Europe/Madrid",
    country: "España",
    country_code: "ES",
    admin1: "Cataluña",
    admin2: "Barcelona",
    admin3: null,
    admin4: null,
    elevation: 15,
    population: 1620000,
  },
  {
    id: "open_meteo:3648522",
    provider: "open_meteo_geocoding",
    provider_id: 3648522,
    name: "Barcelona",
    display_name: "Barcelona, Anzoátegui, Venezuela",
    latitude: 10.13333,
    longitude: -64.7,
    timezone: "America/Caracas",
    country: "Venezuela",
    country_code: "VE",
    admin1: "Anzoátegui",
    admin2: null,
    admin3: null,
    admin4: null,
    elevation: 13,
    population: 815000,
  },
];

const conditions = [
  "sunny",
  "partly_cloudy",
  "rain",
  "cloudy",
  "sunny",
  "rain",
  "partly_cloudy",
] as const;

function stat(value: number, spread = 1) {
  return {
    min: value - spread,
    avg: value,
    max: value + spread,
  };
}

const dates = Array.from({ length: 7 }, (_, index) => {
  const date = new Date(Date.UTC(2026, 6, 13 + index));
  return date.toISOString().slice(0, 10);
});

const dailyForecast = dates.map((date, index) => ({
  date,
  provider_count: 3,
  temperature_min_c: stat(19 + (index % 2)),
  temperature_max_c: stat(28 + (index % 3)),
  precipitation_total: stat(index === 2 ? 1.2 : 0.2, 0.2),
  condition: conditions[index],
}));

const hourlyForecast = dates.flatMap((date, dayIndex) =>
  [8, 12, 16, 20].map((hour, hourIndex) => ({
    datetime: `${date}T${String(hour).padStart(2, "0")}:00:00`,
    provider_count: 3,
    temperature_c: stat(20 + dayIndex + hourIndex),
    precipitation_probability: stat(dayIndex === 2 ? 55 : 12, 5),
    precipitation_total: stat(dayIndex === 2 ? 0.6 : 0.1, 0.1),
    precipitation_snow: stat(0, 0),
    humidity_percent: 58,
    cloud_cover: dayIndex === 2 ? 78 : 25,
    wind_speed_kmh: 13.5,
    apparent_temperature_c: 23.7,
    condition: conditions[dayIndex],
  })),
);

const forecast = {
  latitude: locations[0].latitude,
  longitude: locations[0].longitude,
  timezone: locations[0].timezone,
  days: 7,
  providers_requested: ["google_weather", "open_meteo", "weather_api"],
  providers_used: ["google_weather", "open_meteo", "weather_api"],
  provider_errors: {},
  warnings: [],
  hourly_window: {
    mode: "common_provider_overlap",
    start: `${dates[0]}T08:00:00`,
    end: `${dates[6]}T20:00:00`,
  },
  daily_window: {
    mode: "common_provider_overlap",
    start: dates[0],
    end: dates[6],
  },
  hourly_forecast: hourlyForecast,
  daily_forecast: dailyForecast,
};

test("permite elegir una ciudad homónima y cambiar el día mostrado", async ({ page }) => {
  let forecastRequest: Record<string, unknown> | null = null;

  await page.route("**/api/locations/search?**", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ query: "Barcelona", count: 10, results: locations }),
    });
  });

  await page.route("**/api/weather/aggregate/forecast", async (route) => {
    forecastRequest = route.request().postDataJSON() as Record<string, unknown>;
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify(forecast),
    });
  });

  await page.goto("/");
  await expect(page.getByRole("heading", { name: /más de un punto de vista/i })).toBeVisible();
  await expect(page.locator(".landing-footer")).toHaveCount(0);
  await expect(page.locator(".landing-copy")).toHaveCSS("animation-name", "fade-in");
  await expect(page.locator(".location-search--hero")).toHaveCSS("animation-name", "fade-in");

  await page.getByRole("combobox").fill("Barcelona");
  await page.getByRole("button", { name: "Buscar" }).click();
  await expect(page.getByRole("option")).toHaveCount(2);

  await page.getByRole("option").filter({ hasText: "Cataluña" }).click();

  await expect(page.getByRole("heading", { name: "Próximos 7 días" })).toBeVisible();
  await expect(page.locator(".day-card")).toHaveCount(7);
  await expect(page.locator(".topbar-source-count")).toContainText("3 proveedores");
  await expect(page.locator(".location-banner")).not.toContainText("Consenso");
  await expect(page.locator(".location-banner")).not.toContainText("Europe/Madrid");
  await expect(page.locator(".location-banner-meta")).toContainText("41,39, 2,16");
  await expect(page.locator(".provider-availability")).toHaveCount(0);
  await expect(page.locator(".disclaimer")).toHaveCount(0);
  await expect(page.locator(".day-card-topline").first()).toContainText(/Lun\s*-\s*13 Jul/i);
  const [dayNameStyle, dayDateStyle] = await page
    .locator(".day-card-topline")
    .first()
    .locator(".day-name, .day-date")
    .evaluateAll((elements) => elements.map((element) => {
      const style = getComputedStyle(element);
      return { color: style.color, fontSize: style.fontSize, fontWeight: style.fontWeight };
    }));
  expect(dayDateStyle).toEqual(dayNameStyle);
  await expect(page.locator(".day-sources")).toHaveCount(0);
  await expect(page.locator(".daily-legend, .hourly-toolbar-note")).toHaveCount(0);
  expect(forecastRequest).toMatchObject({ days: 7 });
  expect(forecastRequest).toHaveProperty("location.timezone", "Europe/Madrid");

  await page.locator(".day-card").nth(1).click();
  await expect(page.locator(".hourly-toolbar h2")).toContainText("Martes, 14 de julio");
  await expect(page.locator(".hour-time").first()).toHaveText("08:00");
  await expect(page.locator(".hour-inline-metric--feels").first()).toHaveText("24°C");
  await expect(page.locator(".hour-inline-metric--wind").first()).toHaveText("14 km/h");
  await expect(page.getByRole("columnheader", { name: "Nubosidad" })).toHaveCount(0);
  await expect(page.locator(".hour-inline-metric--cloud")).toHaveCount(0);
  await expect(page.locator(".probability-average").first()).toHaveText("12%");
  await expect(page.locator(".probability-range").first()).toHaveText("7–17%");
  const dailyPrecipitation = page.locator(".day-temperature--precipitation").nth(1);
  await expect(dailyPrecipitation.locator(".day-temperature-values > span").first()).toHaveText("0");
  await expect(dailyPrecipitation.locator(".day-temperature-values > strong")).toHaveText("0,2");
  await expect(dailyPrecipitation.locator(".day-temperature-values > span").last()).toHaveText("0,4");
  await expect(page.locator(".hour-metric--precipitation").first()).toContainText("0,1");
  await expect(page.getByRole("columnheader", { name: "Nieve (cm) mín. media máx." })).toBeVisible();
  await expect(page.locator(".hour-metric--snow").first()).toContainText("0");
  await expect(page.locator(".hour-expand")).toHaveCount(0);

  const secondaryTextSizes = await page
    .locator(".day-temperature-label, .metric-column-header small, .probability-gauge small")
    .evaluateAll((elements) => elements.map((element) => parseFloat(getComputedStyle(element).fontSize)));
  expect(Math.min(...secondaryTextSizes)).toBeGreaterThanOrEqual(10);

  await page.screenshot({
    path: "test-results/results-desktop.png",
    fullPage: true,
  });
});
