"""
dashboard.py — hvPlot / Panel / Bokeh interactive dashboard for MLCW + GWL time series.

Replaces the matplotlib-based orchestrator, widgets, and panels with a single
Panel layout using native Bokeh widgets and HoloViews Curves.  Data loading
(DataLoader, DataMapper) is reused as-is.

Usage
-----
    from mlcw_inspector import DataLoader, DataMapper
    from .dashboard import MLCWInspector

    loader = DataLoader()
    mapper = DataMapper(loader.assignment, loader.project_root)
    app = MLCWInspector(loader, mapper)
    app.show()
"""

from __future__ import annotations

import pandas as pd
import holoviews as hv
import holoviews.streams as hvs
import panel as pn
import pyproj

from .data_loader import DataLoader
from .data_mapper import DataMapper
from .plot_styles import (
    LAYER_COLORS, FALLBACK_COLOR, RING_ALPHA, RING_LINEWIDTH, INSAR_COLOR,
    get_layer_color,
)

# ---------------------------------------------------------------------------
# Enable Bokeh backend (Bokeh is the default for HoloViews >= 1.19)
# ---------------------------------------------------------------------------
hv.extension("bokeh", logo=False)

# ---------------------------------------------------------------------------
# Ordering for layers (depth sequence)
# ---------------------------------------------------------------------------
_LAYER_ORDER = ["F1", "F2", "T2", "F3", "F4", "T1"]


def _sort_layers(layer_set: set[str]) -> list[str]:
    """Return layers in depth order, unknown layers appended at the end."""
    known = [l for l in _LAYER_ORDER if l in layer_set]
    extra = sorted(layer_set - set(_LAYER_ORDER))
    return known + extra


# ---------------------------------------------------------------------------
# Legend helper — Bokeh hook to push legend outside the plot frame
# ---------------------------------------------------------------------------


def _legend_outside_right(plot, element):
    """Move the Bokeh legend from the central plot frame to the right-side
    layout panel, placing it outside the plotted axes."""
    p = plot.state
    if p.legend:
        legend = p.legend[0]
        # Detach from the central frame to avoid dual rendering
        p.center = [r for r in p.center if r is not legend]
        p.add_layout(legend, "right")


# ---------------------------------------------------------------------------
# Dashboard class
# ---------------------------------------------------------------------------

class MLCWInspector:
    """Panel-based interactive dashboard for MLCW + GWL + InSAR inspection."""

    def __init__(self, loader: DataLoader, mapper: DataMapper):
        self.loader = loader
        self.mapper = mapper
        self._station_data: dict = {}           # cache for current station

        # ---- Widgets -------------------------------------------------

        stations = loader.stations
        first = stations[0] if stations else ""

        self.station_select = pn.widgets.Select(
            name="Station",
            options=stations,
            value=first,
            width=220,
            sizing_mode="fixed",
        )

        self.mode_radio = pn.widgets.RadioButtonGroup(
            name="View mode",
            options=["Layers", "Rings"],
            value="Layers",
            button_type="primary",
            sizing_mode="fixed",
        )

        self.mlcw_checkboxes = pn.widgets.CheckBoxGroup(
            name="MLCW layers",
            options=[],
            value=[],
            inline=False,
            sizing_mode="fixed",
            height=160,
        )

        self.gwl_checkboxes = pn.widgets.CheckBoxGroup(
            name="GWL wells",
            options=[],
            value=[],
            inline=False,
            sizing_mode="fixed",
            height=120,
        )

        # ---- Watchers ------------------------------------------------

        self.station_select.param.watch(self._on_station_changed, "value")
        self.mode_radio.param.watch(self._on_mode_changed, "value")

        # ---- Reactive plot functions ---------------------------------

        self._mlcw_pane = pn.bind(
            self._build_mlcw, station=self.station_select,
            mode=self.mode_radio, visible=self.mlcw_checkboxes,
        )
        self._gwl_pane = pn.bind(
            self._build_gwl, station=self.station_select,
            visible=self.gwl_checkboxes,
        )
        self._insar_pane = pn.bind(
            self._build_insar, station=self.station_select,
        )
        self._status_pane = pn.bind(
            self._build_status, station=self.station_select,
            mode=self.mode_radio,
        )

        # ---- Seed initial data ---------------------------------------

        self._ensure_data_loaded(first)
        self._update_mlcw_checkboxes(first, "Layers")
        self._update_gwl_checkboxes(first)

        # ---- Layout --------------------------------------------------

        sidebar = pn.Column(
            pn.pane.Markdown("### MLCW layers", margin=(0, 5, 0, 5)),
            self.mlcw_checkboxes,
            pn.pane.Str("—" * 24, margin=(5, 5, 5, 5)),
            pn.pane.Markdown("### GWL wells", margin=(5, 5, 0, 5)),
            self.gwl_checkboxes,
            sizing_mode="stretch_width",
        )

        toolbar = pn.Row(
            self.station_select,
            self.mode_radio,
            self._status_pane,
            sizing_mode="stretch_width",
        )

        self._map_pane = self._build_map_tab()

        tabs = pn.Tabs(
            ("MLCW Compaction", self._mlcw_pane),
            ("Groundwater Level", self._gwl_pane),
            ("InSAR Displacement", self._insar_pane),
            ("Station Map", self._map_pane),
            sizing_mode="stretch_width",
            tabs_location="above",
        )

        main_panels = pn.Column(
            toolbar,
            tabs,
            sizing_mode="stretch_width",
        )

        self._layout = pn.Row(
            pn.Column(sidebar, width=260, sizing_mode="fixed"),
            main_panels,
            sizing_mode="stretch_width",
        )

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    @property
    def layout(self):
        """Return the root Panel layout object (for embedding or serving)."""
        return self._layout

    def show(self, **kwargs):
        """Open the dashboard in a browser tab (starts Bokeh server)."""
        pn.serve(self._layout, show=True, title="MLCW / GWL Inspector",
                 **kwargs)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_data_loaded(self, station: str) -> dict:
        """Return cached station data, loading if needed."""
        if station not in self._station_data:
            data = self.loader.get_station_data(station)
            gwl = self.loader.load_gwl_for_station(station, self.mapper)
            data["gwl_feathers"] = gwl
            self.mapper._cached_classify = data.get("classify")
            self._station_data[station] = data
        return self._station_data[station]

    # ------------------------------------------------------------------
    # Watchers
    # ------------------------------------------------------------------

    def _on_station_changed(self, event):
        station = event.new
        self._station_data.clear()
        self._ensure_data_loaded(station)
        self._update_mlcw_checkboxes(station, self.mode_radio.value)
        self._update_gwl_checkboxes(station)

    def _on_mode_changed(self, event):
        station = self.station_select.value
        self._update_mlcw_checkboxes(station, event.new)

    # ------------------------------------------------------------------
    # Checkbox synchronisation
    # ------------------------------------------------------------------

    def _update_mlcw_checkboxes(self, station: str, mode: str):
        data = self._ensure_data_loaded(station)

        if mode == "Layers":
            layers_raw = self.mapper.get_layers_for_station(station)
            filtered = [l for l in _LAYER_ORDER if l in layers_raw]
        else:
            classify = data.get("classify")
            if classify is not None:
                dtl = DataMapper.map_rings_to_layers(classify)
                layers_set = set(dtl.values())
                filtered = _sort_layers(layers_set)
            else:
                filtered = []

        self.mlcw_checkboxes.options = filtered
        # Preserve checked layers that still exist; check all on station change
        keep = [v for v in self.mlcw_checkboxes.value if v in filtered]
        self.mlcw_checkboxes.value = keep or list(filtered)

    def _update_gwl_checkboxes(self, station: str):
        data = self._ensure_data_loaded(station)
        gwl = data.get("gwl_feathers", {})
        valid = sorted([
            l for l, s in gwl.items() if s is not None and len(s) > 0
        ])
        self.gwl_checkboxes.options = valid
        keep = [v for v in self.gwl_checkboxes.value if v in valid]
        self.gwl_checkboxes.value = keep or list(valid)

    # ------------------------------------------------------------------
    # Status line
    # ------------------------------------------------------------------

    def _build_status(self, station: str, mode: str) -> str:
        data = self._ensure_data_loaded(station)
        gwl = data.get("gwl_feathers", {})
        n_layers = len(gwl)
        n_ok = sum(1 for s in gwl.values()
                   if s is not None and len(s) > 0)
        has_rec = "✓L" if data.get("has_reconst") else "✗L"
        has_ring = "✓R" if data.get("has_rings") else "✗R"

        return (
            f"Layers `{n_layers}`  GWL `{n_ok}/{n_layers}`  "
            f"{has_rec} {has_ring}  Mode: `{mode}`"
        )

    # ------------------------------------------------------------------
    # Plot builders
    # ------------------------------------------------------------------

    @staticmethod
    def _empty(message: str, width: int = 700, height: int = 200):
        """Return a Markdown placeholder for missing data."""
        return pn.pane.HTML(
            f'<p style="color:#999999;font-style:italic;'
            f'text-align:center;padding-top:{height//3}px;">'
            f"{message}</p>",
            width=width, height=height,
            sizing_mode="fixed",
        )

    # ---- MLCW -------------------------------------------------------

    def _build_mlcw(self, station: str, mode: str, visible: list[str]):
        data = self._ensure_data_loaded(station)
        curves = []

        if mode == "Layers":
            reconst = data.get("reconst")
            if reconst is None:
                return self._empty("No layer data for this station",
                                   height=470)

            t = reconst["datetime"]
            for layer in visible:
                if layer not in reconst.columns:
                    continue
                y = reconst[layer]
                valid = y.notna()
                if valid.sum() < 2:
                    continue
                color = get_layer_color(layer)
                curve = hv.Curve(
                    (t[valid], y[valid]), "Date", "Compaction (mm)",
                    label=layer,
                ).opts(
                    color=color, line_width=1.5,
                )
                curves.append(curve)

        else:  # Rings mode
            ring = data.get("ring")
            if ring is None:
                return self._empty("No ring data for this station",
                                   height=470)

            classify = data.get("classify")
            depth_to_layer = DataMapper.map_rings_to_layers(classify)

            t = ring["datetime"]
            for col in ring.columns:
                if col == "datetime" or str(col).startswith("Unnamed"):
                    continue
                lyr = depth_to_layer.get(col, "Unclassified")
                if lyr not in visible:
                    continue
                y = ring[col]
                valid = y.notna()
                if valid.sum() < 2:
                    continue
                color = get_layer_color(lyr)
                curve = hv.Curve(
                    (t[valid], y[valid]), "Date", "Compaction (mm)",
                ).opts(
                    color=color, line_width=RING_LINEWIDTH, alpha=RING_ALPHA,
                )
                curves.append(curve)

        if not curves:
            return self._empty("No data for the selected layers",
                               height=470)

        overlay = hv.Overlay(curves).opts(
            legend_position="right",
            hooks=[_legend_outside_right],
            width=850, height=470,
            title=f"MLCW Compaction — {station}",
            show_grid=True,
            toolbar="above",
        )
        return overlay

    # ---- GWL --------------------------------------------------------

    def _build_gwl(self, station: str, visible: list[str]):
        data = self._ensure_data_loaded(station)
        gwl_dict = data.get("gwl_feathers", {})

        if not gwl_dict or not visible:
            return self._empty("No GWL data for this station", height=220)

        curves = []
        for layer in visible:
            series = gwl_dict.get(layer)
            if series is None or len(series) == 0:
                continue
            color = get_layer_color(layer)
            label = self.mapper.get_well_label(station, layer)
            curve = hv.Curve(
                (series.index, series.values), "Date", "Head (m MSL)",
                label=label,
            ).opts(
                color=color, line_width=1.5,
            )
            curves.append(curve)

        if not curves:
            return self._empty("No GWL data for visible layers", height=220)

        overlay = hv.Overlay(curves).opts(
            legend_position="right",
            hooks=[_legend_outside_right],
            width=850, height=220,
            title=f"Groundwater Level — {station}",
            show_grid=True,
        )
        return overlay

    # ---- InSAR ------------------------------------------------------

    def _build_insar(self, station: str):
        insar_df = self.loader.insar_df
        if station not in insar_df.columns:
            return self._empty("No InSAR data for this station",
                               height=150)

        y = insar_df[station] * 1000.0   # metres → mm
        t = insar_df.index

        curve = hv.Curve(
            (t, y), "Date", "Disp. (mm)",
        ).opts(
            color=INSAR_COLOR, line_width=1.0,
            width=700, height=150,
            title="InSAR Surface Displacement",
            show_grid=True,
        )
        return curve

    # ---- Station Map ----------------------------------------------------

    def _build_map_tab(self):
        """Station location map with tap-to-select and GWL well overlay.

        Loads coordinates from ``MLCW_data_timeline.csv``, enriches with
        deepest-layer and layer-count metadata from the v3 assignment.
        Also loads GWL well coordinates from ``gwl_allwells_flat.csv``
        and converts them from TWD97 (EPSG:3828) to WGS84 (EPSG:4326).

        The map is reactive: it re-renders when ``station_select`` changes.
        Non-selected stations appear as black triangles.  The selected
        station appears as a large yellow star.  Its assigned GWL wells
        are plotted as cyan circles with hover labels.

        Clicking a non-selected station marker updates the dropdown.
        """
        # -- 1. Load station coordinates (one time) -----------------------
        coord_path = self.loader.data_root / "mlcw" / "MLCW_data_timeline.csv"
        coord_df = pd.read_csv(coord_path)
        coord_df = coord_df[
            coord_df["Ename"].isin(self.loader.stations)
        ].copy()

        # -- Enrich with layer info ---------------------------------------
        assn = self.loader.assignment
        layer_order = {"F1": 0, "F2": 1, "T2": 2, "F3": 3, "F4": 4, "T1": 5}
        assn_w = assn.copy()
        assn_w["_order"] = assn_w["layer"].map(layer_order).fillna(99)

        # deepest layer present at each station
        deepest = (
            assn_w.sort_values("_order", ascending=False)
            .groupby("station")
            .first()["layer"]
            .reset_index()
        )
        deepest.columns = ["station", "deepest_layer"]

        # number of layers present
        nlyrs = (
            assn.groupby("station")["layer"]
            .nunique()
            .reset_index()
        )
        nlyrs.columns = ["station", "n_layers"]

        coord_df = coord_df.merge(
            deepest, left_on="Ename", right_on="station", how="left"
        )
        coord_df = coord_df.merge(
            nlyrs, left_on="Ename", right_on="station", how="left"
        )

        # -- 2. Load GWL well coordinates (one time) -----------------------
        # Source: gwl_allwells_flat.csv — TWD97 (EPSG:3828) projected coords.
        gwl_path = (
            self.loader.data_root / "gwl" / "well_info" / "gwl_allwells_flat.csv"
        )
        gwl_raw = pd.read_csv(gwl_path, dtype={"wellcode": str})

        # Convert TWD97 (tm2 zone 121) → WGS84 (lat/lon)
        twd97 = pyproj.CRS.from_epsg(3828)
        wgs84 = pyproj.CRS.from_epsg(4326)
        transformer = pyproj.Transformer.from_crs(twd97, wgs84, always_xy=True)
        x_vals = gwl_raw["x_twd97"].values
        y_vals = gwl_raw["y_twd97"].values
        lon_arr, lat_arr = transformer.transform(x_vals, y_vals)
        gwl_raw["lon"] = lon_arr
        gwl_raw["lat"] = lat_arr

        # Build lookup: wellcode → (lon, lat, station_name) for O(1) access
        gwl_lookup = {
            row["wellcode"]: (
                row["lon"], row["lat"],
                str(row.get("station", "")),
            )
            for _, row in gwl_raw.iterrows()
        }

        # -- 3. Reactive map function -------------------------------------

        def _render_map(station):
            """Build the HoloViews overlay for the current station."""

            # --- Basemap: OpenStreetMap (reliable without special headers) ---
            satellite = hv.Tiles(
                "https://tile.openstreetmap.org/{Z}/{Y}/{X}.png"
            ).opts(width=850, height=500, toolbar="above")

            ref_labels = hv.Tiles(
                "https://a.basemaps.cartocdn.com/light_only_labels/"
                "{Z}/{Y}/{X}.png"
            ).opts(width=850, height=500, alpha=0.85)

            # --- GWL wells for the selected station -----------------------
            gwl_records = []
            for layer, wellcode, _ in self.mapper.get_wells_for_station(station):
                if wellcode in gwl_lookup:
                    wlon, wlat, wstation = gwl_lookup[wellcode]
                    gwl_records.append({
                        "lon": wlon, "lat": wlat,
                        "wellcode": wellcode,
                        "station_name": wstation,
                        "layer": layer,
                    })

            if gwl_records:
                gwl_df = pd.DataFrame(gwl_records)
                gwl_pts = hv.Points(
                    gwl_df, ["lon", "lat"],
                    vdims=["wellcode", "station_name", "layer"],
                ).opts(
                    marker="circle",
                    color="#00CED1",
                    size=8,
                    line_color="black",
                    line_width=0.8,
                    tools=["hover"],
                )
                # Well labels beside each GWL marker
                gwl_labels = hv.Labels(
                    gwl_df, ["lon", "lat"], "wellcode"
                ).opts(
                    text_color="#004d4d",
                    text_font_size="8pt",
                    xoffset=8,
                    yoffset=0,
                )
            else:
                gwl_pts = hv.Points([]).opts(alpha=0)
                gwl_labels = hv.Labels([]).opts(text_alpha=0)

            # --- Non-selected stations — black triangles -----------------
            other_df = coord_df[coord_df["Ename"] != station]
            if not other_df.empty:
                non_sel_pts = hv.Points(
                    other_df, ["long", "lat"],
                    vdims=["Ename", "deepest_layer", "n_layers"],
                ).opts(
                    marker="triangle",
                    color="black",
                    size=8,
                    tools=["hover"],
                )
            else:
                non_sel_pts = hv.Points([]).opts(alpha=0)

            # --- Selected station — yellow star --------------------------
            sel_df = coord_df[coord_df["Ename"] == station]
            if not sel_df.empty:
                sel_pt = hv.Points(
                    sel_df, ["long", "lat"],
                    vdims=["Ename", "deepest_layer", "n_layers"],
                ).opts(
                    marker="star",
                    color="#FFD700",
                    size=15,
                    line_color="black",
                    line_width=1.0,
                    tools=["hover"],
                )
            else:
                sel_pt = hv.Points([]).opts(alpha=0)

            # --- Composite overlay: basemap → MLCW → GWL on top ---------
            overlay = (
                satellite * ref_labels
                * non_sel_pts * sel_pt
                * gwl_pts * gwl_labels
            ).opts(
                responsive=True,
                title=f"MLCW Station Locations — selected: {station}",
            )

            # --- Tap stream -----------------------------------------------
            tap = hvs.Tap(source=non_sel_pts)

            def _on_tap(x, y):
                if x is None or y is None:
                    return ""
                dist_sq = (
                    (coord_df["long"] - x) ** 2.0
                    + (coord_df["lat"] - y) ** 2.0
                )
                idx = dist_sq.idxmin()
                if dist_sq.iloc[idx] < 0.01:
                    self.station_select.value = coord_df.iloc[idx]["Ename"]
                return ""

            watcher = pn.bind(
                _on_tap, x=tap.param.x, y=tap.param.y,
            )
            watcher_html = pn.pane.HTML(watcher, height=0, margin=0,
                                        sizing_mode="fixed")

            return pn.Column(overlay, watcher_html, sizing_mode="stretch_width")

        # -- 4. Wire up the reactive pane --------------------------------
        map_pane = pn.bind(_render_map, station=self.station_select)

        return pn.Column(map_pane, sizing_mode="stretch_width")
