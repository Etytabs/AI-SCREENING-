"use client";

import { useEffect, useState } from "react";

export const THEME_KEY = "ai-screening-theme";
type Theme = "light" | "dark";

/** Presentation only: flips a data-theme attribute the stylesheet reacts to. */
export default function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>("light");
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const stored = document.documentElement.getAttribute("data-theme");
    setTheme(stored === "dark" ? "dark" : "light");
    setReady(true);
  }, []);

  function apply(next: Theme) {
    setTheme(next);
    document.documentElement.setAttribute("data-theme", next);
    try {
      window.localStorage.setItem(THEME_KEY, next);
    } catch {
      /* private mode: the choice simply does not persist */
    }
  }

  const dark = theme === "dark";
  return (
    <button
      type="button"
      className="theme-toggle"
      role="switch"
      aria-checked={dark}
      aria-label={`Dark mode ${dark ? "on" : "off"}`}
      title={dark ? "Switch to light mode" : "Switch to dark mode"}
      onClick={() => apply(dark ? "light" : "dark")}
      suppressHydrationWarning
    >
      <span className="theme-toggle-track" aria-hidden="true">
        <span className="theme-toggle-thumb">{ready && dark ? "◒" : "◓"}</span>
      </span>
      <span className="theme-toggle-label">{dark ? "Dark" : "Light"}</span>
    </button>
  );
}
