---
name: PAVEtrack Dashboard
description: The implemented Streamlit pavement analysis workspace.
colors:
  ink: "#182337"
  muted: "#59677c"
  blue: "#2563eb"
  line: "#e0e6ef"
  surface: "#ffffff"
  canvas: "#f4f6fa"
  field-border: "#8491a5"
  download-surface: "rgb(252, 252, 253)"
  download-hover: "#eff5ff"
  recommendation-surface: "#eaf1ff"
  recommendation-border: "#ccdcfb"
  recommendation-heading: "#234776"
  thickness: "#1c4fb5"
  complete-surface: "#eaf5ef"
  complete-text: "#236445"
  waiting-surface: "#e9edf3"
  bar-track: "#edf2f9"
  bar-fill: "#719bef"
typography:
  headline:
    fontFamily: '"Segoe UI", -apple-system, BlinkMacSystemFont, sans-serif'
    fontSize: "2rem"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.035em"
  title:
    fontSize: "1.125rem"
    fontWeight: 650
  body:
    fontFamily: '"Segoe UI", -apple-system, BlinkMacSystemFont, sans-serif'
    fontSize: "0.9375rem"
    lineHeight: 1.55
  label:
    fontSize: "0.8125rem"
    fontWeight: 600
  metric:
    fontSize: "1.75rem"
    fontWeight: 650
    lineHeight: 1.25
    letterSpacing: "-0.03em"
  thickness:
    fontSize: "2.75rem"
    fontWeight: 650
    lineHeight: 1.05
    letterSpacing: "-0.04em"
rounded:
  status: "6px"
  control: "8px"
  upload: "10px"
  panel: "14px"
spacing:
  compact: "0.5rem"
  block: "1rem"
  inset: "1.25rem"
  panel: "1.5rem"
  workspace: "2rem"
components:
  button-download:
    backgroundColor: "{colors.download-surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "4px 12px"
    typography: "{typography.label}"
  button-download-hover:
    backgroundColor: "{colors.download-hover}"
  text-field:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
  status-complete:
    backgroundColor: "{colors.complete-surface}"
    textColor: "{colors.complete-text}"
    rounded: "{rounded.status}"
    padding: "0.375rem 0.65rem"
  status-waiting:
    backgroundColor: "{colors.waiting-surface}"
    textColor: "{colors.muted}"
    rounded: "{rounded.status}"
    padding: "0.375rem 0.65rem"
  project-panel:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.panel}"
    padding: "{spacing.panel}"
  metric-strip:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.panel}"
    padding: "1.25rem 0"
  recommendation:
    backgroundColor: "{colors.recommendation-surface}"
    textColor: "{colors.recommendation-heading}"
    rounded: "{rounded.panel}"
    padding: "{spacing.panel}"
  traffic-chart:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.panel}"
    padding: "{spacing.panel}"
---

# Design System: PAVEtrack Dashboard

## Overview

**Reference: PAVEtrack Intelligent Pavement Monitoring Dashboard**

The title, subtitle, form labels, section titles, and success message follow the user's reference screenshot. Avoid adding taglines, workspace labels, setup explanations, or footer copy. The light canvas, white panels, slate text, and blue emphasis organize inputs and results.

Presentation helpers live in `dashboard_ui.py`; shared styles and responsive rules live in `assets/dashboard.css`. `.streamlit/config.toml` supplies the matching light theme for native widgets. `app_dashboard.py` owns the form, validation, calculation calls, and recommendation branches. The four calculation modules retain their existing responsibilities documented in README.md.

**Key Characteristics:**
- A persistent project setup panel beside results on wide screens.
- Numeric summaries followed by a blue thickness recommendation and detailed tabs.
- Flat, bordered surfaces, system typography, and inline SVG symbols.

## Colors

Blue identifies focus indicators, chart emphasis, and the recommendation area. Ink and muted slate separate primary data from labels; white surfaces sit on the pale canvas. Green appears in the successful-file-processing status.

The first six color entries map directly to `--pave-ink`, `--pave-muted`, `--pave-blue`, `--pave-line`, `--pave-surface`, and `--pave-canvas` in the stylesheet. Other entries document recurring component colors. `download-surface` is the computed Streamlit 1.65 button color and may change with framework upgrades. Sidecar tonal ramps are generated preview metadata, not additional application colors.

## Typography

The UI uses Segoe UI with operating-system sans-serif fallbacks; no web font is downloaded. The headline role is the page title. The body role describes introductory and empty-state copy, not every Streamlit paragraph. Results headings use the title role; setup and chart headings use slightly smaller sizes.

Metric and thickness values use tabular numerals. Labels and helper copy are smaller than the values they explain. The headline reduces to 1.75rem at the narrowest breakpoint, and metrics reduce to 1.375rem below 1100px.

## Layout

The main container is capped at 1600px, with desktop padding of 2.5rem 3rem 2rem. `app_dashboard.py` creates two Streamlit columns with weights 1:2.65; the stylesheet fixes the setup column at 340px from 1100px upward and uses a 2rem workspace gap. Regular Streamlit blocks have a 1rem gap.

- At 1099px and below, page padding becomes 2rem 1.5rem, panel insets tighten, and chart percentage labels disappear while counts remain.
- At 800px and below, inputs and results stack at full width.
- At 480px and below, page padding becomes 1.5rem 1rem; metrics become individual rows; the recommendation and chart heading stack, and tab labels can wrap.

These are the implemented dashboard breakpoints, not a general rule for unrelated screens. Keep long project locations and vehicle-class names able to wrap.

## Elevation & Depth

Custom panels have no box shadows. White and pale-blue fills, one-pixel borders, and internal dividers establish hierarchy. Native Streamlit overlays retain framework behavior.

## Shapes

Panels share the `--pave-radius` corner token. Controls and expanders use the control radius; status badges are smaller rounded rectangles. The upload area uses a dashed border and the upload radius. Inline SVG icons use rounded strokes and inherit their surrounding color. No raster images ship with the presentation.

## Components

- **Input Control Panel:** Native Streamlit uploader, selectboxes, text inputs, and an expandable sample download. Input outlines use the field-border color; text fields have a 42px minimum height and selectboxes 44px. Input focus changes the border to blue. Buttons, links, inputs, and tabs receive a 2px blue focus-visible outline with a 3px offset.
- **Download buttons:** Native secondary buttons with the documented control shape and label typography. Hover uses a pale-blue fill and blue border. Background and border transitions last 160ms with ease-out; reduced-motion preference removes transitions.
- **Status:** `render_results_heading()` shows “Traffic File Processed Successfully” with `role="status"` and an inline check icon after calculation. Project location is escaped before rendering.
- **Empty state:** `render_empty_state()` shows a short upload prompt, or the original warning to complete engineering inputs after upload. Location is optional.
- **Metric strip:** `render_results()` displays AADT, daily ESAL, and cumulative ESAL with labels and units. Desktop dividers are vertical; mobile dividers are horizontal.
- **Recommendation:** The blue panel prioritizes recommended thickness in millimeters, then pavement type and the existing recommendation text. The adjacent note explains rounding upward to 10mm and model minimums. Display styling must not alter the calculation branches.
- **Result tabs:** Streamlit tabs expose Traffic overview, Uploaded Traffic Data, and Calculation details. The data table hides its index, uses 36px rows, and offers processed CSV download. The details list shows inputs, calculated and recommended thickness, and model minimum without additional explanatory copy.
- **Traffic composition:** `render_traffic_chart()` draws one horizontal row per vehicle class, in input order. Width is relative to the maximum class count; the printed share is relative to total count. The first row has the stronger blue. Counts remain visible at all breakpoints. Bars are decorative; class names and values are text.

## Do's and Don'ts

### Do:
- Do keep CSS tokens and the Streamlit theme aligned when changing shared colors.
- Do keep units, numeric alignment, and calculation context beside the values they explain.
- Do verify desktop and stacked layouts, empty and error states, and keyboard focus after presentation edits.
- Do escape uploaded or user-entered text before interpolating it into custom HTML.

### Don't:
- Don't change calculation arguments, rounding, model minimums, or recommendation branches through presentation helpers.
- Don't rely on color or chart width alone to communicate results.
- Don't assume Streamlit internal selectors survive a framework upgrade; check native controls and tabs in the browser.
