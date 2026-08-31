import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type { WeatherCondition } from "../types/weather";
import { WeatherIcon } from "./WeatherIcon";

const states: Array<{ condition: WeatherCondition; marker: string }> = [
  { condition: "sunny", marker: 'fill="#ffbd20"' },
  { condition: "partly_cloudy", marker: 'transform="translate(-5 -6) scale(.78)"' },
  { condition: "cloudy", marker: 'fill="#aebed2"' },
  { condition: "rain", marker: 'stroke="#1688f8"' },
  { condition: "snow", marker: 'fill="#56aef8"' },
  { condition: "unknown", marker: ">?</text>" },
];

describe("WeatherIcon", () => {
  it("RF16", () => {
    const renderedIcons = states.map(({ condition, marker }) => {
      const markup = renderToStaticMarkup(
        <WeatherIcon className="rf16" condition={condition} size={48} />,
      );

      expect(markup).toContain(marker);
      expect(markup).toContain('class="weather-icon rf16"');
      expect(markup).toContain('width="48"');
      expect(markup).toContain('height="48"');
      expect(markup).toContain('aria-hidden="true"');
      return markup;
    });

    expect(new Set(renderedIcons)).toHaveLength(states.length);
  });
});
