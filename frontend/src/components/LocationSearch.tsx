import {
  useEffect,
  useId,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from "react";

import { searchLocations } from "../lib/api";
import { formatCoordinate } from "../lib/format";
import type { LocationCandidate } from "../types/weather";
import { ArrowRightIcon, MapPinIcon, SearchIcon } from "./Icons";

interface LocationSearchProps {
  variant?: "hero" | "compact";
  value?: string;
  forecastLoading?: boolean;
  onSelect: (location: LocationCandidate) => void;
}

export function LocationSearch({
  variant = "hero",
  value = "",
  forecastLoading = false,
  onSelect,
}: LocationSearchProps) {
  const resultsId = useId();
  const searchController = useRef<AbortController | null>(null);
  const [query, setQuery] = useState(value);
  const [results, setResults] = useState<LocationCandidate[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setQuery(value);
  }, [value]);

  useEffect(() => {
    return () => searchController.current?.abort();
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalizedQuery = query.trim();

    if (normalizedQuery.length < 2) {
      setError("Escribe al menos dos caracteres.");
      setResults([]);
      setIsOpen(true);
      return;
    }

    searchController.current?.abort();
    const controller = new AbortController();
    searchController.current = controller;
    setIsSearching(true);
    setError(null);
    setHasSearched(false);
    setIsOpen(true);

    try {
      const response = await searchLocations(normalizedQuery, controller.signal);
      setResults(response.results);
      setHasSearched(true);
    } catch (requestError) {
      if (requestError instanceof DOMException && requestError.name === "AbortError") {
        return;
      }

      setResults([]);
      setHasSearched(true);
      setError(
        requestError instanceof Error
          ? requestError.message
          : "No se han podido buscar ubicaciones.",
      );
    } finally {
      if (!controller.signal.aborted) {
        setIsSearching(false);
      }
    }
  }

  function handleQueryChange(nextQuery: string) {
    setQuery(nextQuery);
    setError(null);
    setHasSearched(false);
    setResults([]);
    setIsOpen(false);
  }

  function handleSelect(location: LocationCandidate) {
    setQuery(location.display_name);
    setIsOpen(false);
    onSelect(location);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === "Escape") {
      setIsOpen(false);
    }
  }

  const disabled = isSearching || forecastLoading;

  return (
    <div
      className={`location-search location-search--${variant}`}
      onKeyDown={handleKeyDown}
    >
      <form className="search-form" onSubmit={handleSubmit} role="search">
        <div className="search-input-wrap">
          <MapPinIcon className="search-leading-icon" />
          <input
            aria-autocomplete="list"
            aria-controls={resultsId}
            aria-expanded={isOpen}
            autoComplete="off"
            className="search-input"
            disabled={forecastLoading}
            onChange={(event) => handleQueryChange(event.target.value)}
            onFocus={() => {
              if (results.length > 0 || error || hasSearched) {
                setIsOpen(true);
              }
            }}
            placeholder="Busca una ciudad o localidad"
            role="combobox"
            spellCheck="false"
            type="search"
            value={query}
          />
        </div>
        <button className="search-submit" disabled={disabled} type="submit">
          {isSearching ? (
            <span className="button-spinner" aria-hidden="true" />
          ) : (
            <SearchIcon />
          )}
          <span>{isSearching ? "Buscando" : "Buscar"}</span>
        </button>
      </form>

      {isOpen && (
        <div className="location-results" id={resultsId} role="listbox">
          {isSearching && (
            <div className="location-results-state" aria-live="polite">
              <span className="small-spinner" aria-hidden="true" />
              Buscando coincidencias…
            </div>
          )}

          {!isSearching && error && (
            <div className="location-results-state location-results-state--error">
              {error}
            </div>
          )}

          {!isSearching && !error && hasSearched && results.length === 0 && (
            <div className="location-results-state">
              No encontramos ubicaciones con ese nombre.
            </div>
          )}

          {!isSearching &&
            results.map((location) => (
              <button
                className="location-option"
                key={location.id}
                onClick={() => handleSelect(location)}
                role="option"
                type="button"
              >
                <span className="location-option-icon">
                  <MapPinIcon />
                </span>
                <span className="location-option-copy">
                  <span className="location-option-name">
                    {location.display_name}
                  </span>
                  <span className="location-option-meta">
                    {formatCoordinate(location.latitude)}, {formatCoordinate(location.longitude)}
                    <span aria-hidden="true"> · </span>
                    {location.timezone}
                  </span>
                </span>
                {location.country_code && (
                  <span className="country-code">{location.country_code}</span>
                )}
                <ArrowRightIcon className="location-option-arrow" />
              </button>
            ))}
        </div>
      )}
    </div>
  );
}
