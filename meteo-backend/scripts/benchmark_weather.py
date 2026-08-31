import statistics
import time

import httpx


URL = "http://127.0.0.1:8000/api/weather/aggregate/forecast"
EXECUTIONS = 10
WAIT_SECONDS = 5

PAYLOAD = {
    "location": {
        "name": "Barcelona",
        "display_name": "Barcelona, Cataluna, Espana",
        "latitude": 41.3874,
        "longitude": 2.1686,
        "timezone": "Europe/Madrid",
    },
    "days": 7,
}


def request_forecast(client: httpx.Client) -> tuple[float, dict]:
    start = time.perf_counter()
    response = client.post(URL, json=PAYLOAD)
    elapsed = time.perf_counter() - start
    response.raise_for_status()
    return elapsed, response.json()


def main() -> None:
    times = []

    with httpx.Client(timeout=30) as client:
        print("Peticion de calentamiento...")
        request_forecast(client)

        for execution in range(1, EXECUTIONS + 1):
            elapsed, data = request_forecast(client)
            times.append(elapsed)

            providers = len(data["providers_used"])
            errors = ", ".join(data["provider_errors"]) or "ninguna"
            print(
                f"{execution:02d}: {elapsed:.3f} s | "
                f"{providers} proveedores | incidencias: {errors}"
            )

            if execution < EXECUTIONS:
                time.sleep(WAIT_SECONDS)

    print("\nResumen")
    print(f"Numero de ejecuciones: {len(times)}")
    print(f"Tiempo minimo: {min(times):.3f} s")
    print(f"Mediana: {statistics.median(times):.3f} s")
    print(f"Promedio: {statistics.mean(times):.3f} s")
    print(f"Tiempo maximo: {max(times):.3f} s")


if __name__ == "__main__":
    main()
