"""
Pygame UI: nested multiverse with large-scale cosmic map, camera pan/zoom, time rewind.
"""
from __future__ import annotations

import copy
import math
from typing import Dict, List, Optional, Tuple

import pygame

from sim.history import History
from sim.model import (
    BlackHole,
    BodyKind,
    CelestialBody,
    LifeStage,
    Multiverse,
    Universe,
    child_inner_information_caps_sum,
    total_information_in_multiverse,
    universe_body_information_used,
)
from sim.layout import (
    black_hole_layout_xy,
    exotic_layout_xy,
    hash01,
    nebula_layout_xy,
    planet_orbit_radius,
    sector_scale,
    star_layout_xy,
)
from sim.physics import SimulationConfig, step_multiverse, universe_world_radius
from viz import proc_sprites


TWO_PI = 2 * math.pi


def _stable_angle(seed: int) -> float:
    return (seed * 0.618033988749895) % TWO_PI


def _star_xy(star: CelestialBody, u: Universe) -> Tuple[float, float]:
    return (star.pos_x, star.pos_y) if star.spatial_ready else star_layout_xy(star, u)


def _bh_xy(bh: BlackHole, u: Universe) -> Tuple[float, float]:
    return (bh.pos_x, bh.pos_y) if bh.spatial_ready else black_hole_layout_xy(bh, u)


def _neb_xy(neb: CelestialBody, u: Universe) -> Tuple[float, float]:
    return (neb.pos_x, neb.pos_y) if neb.spatial_ready else nebula_layout_xy(neb, u)


def _ex_xy(ex: CelestialBody, u: Universe) -> Tuple[float, float]:
    return (ex.pos_x, ex.pos_y) if ex.spatial_ready else exotic_layout_xy(ex, u)


def _blended_body_xy(b: CelestialBody, blend: float) -> Tuple[float, float]:
    if not b.spatial_ready:
        return b.pos_x, b.pos_y
    t = max(0.0, min(1.0, blend))
    return (
        b.render_prev_x + (b.pos_x - b.render_prev_x) * t,
        b.render_prev_y + (b.pos_y - b.render_prev_y) * t,
    )


def _blended_bh_xy(bh: BlackHole, blend: float) -> Tuple[float, float]:
    t = max(0.0, min(1.0, blend))
    return (
        bh.render_prev_x + (bh.pos_x - bh.render_prev_x) * t,
        bh.render_prev_y + (bh.pos_y - bh.render_prev_y) * t,
    )


def universe_depth_map(m: Multiverse) -> Dict[int, int]:
    d: Dict[int, int] = {}

    def walk(u: Universe, depth: int) -> None:
        d[u.id] = depth
        for bh in u.black_holes:
            if bh.inner_universe is not None:
                walk(bh.inner_universe, depth + 1)

    walk(m.root, 0)
    return d


def parent_universe(u: Universe) -> Optional[Universe]:
    if u.parent_bh is None:
        return None
    return u.parent_bh.host


def bfs_universes(m: Multiverse) -> List[Universe]:
    return m.all_universes_bfs()


def life_color(stage: LifeStage) -> Tuple[int, int, int]:
    if stage == LifeStage.NONE:
        return (140, 150, 170)
    if stage == LifeStage.PREBIOTIC:
        return (220, 200, 80)
    if stage == LifeStage.LIFE:
        return (80, 200, 120)
    return (120, 220, 255)


def _lerp_rgb(
    a: Tuple[int, int, int], b: Tuple[int, int, int], t: float
) -> Tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def star_spectral_rgb(star: CelestialBody) -> Tuple[int, int, int]:
    """Pseudospectral colour from heat + mass (not only yellow dwarf)."""
    h = star.heat_index
    m = star.mass_index
    t = max(0.0, min(1.8, h * 0.95 + m * 0.12))
    blue = (120, 175, 255)
    white = (240, 245, 255)
    yellow = (255, 235, 160)
    orange = (255, 170, 90)
    red = (255, 100, 70)
    if t < 0.28:
        return _lerp_rgb(blue, white, t / 0.28)
    if t < 0.5:
        return _lerp_rgb(white, yellow, (t - 0.28) / 0.22)
    if t < 0.85:
        return _lerp_rgb(yellow, orange, (t - 0.5) / 0.35)
    return _lerp_rgb(orange, red, min(1.0, (t - 0.85) / 0.35))


# First row of universe list (must match _draw_sidebar and click hit-test)
SIDEBAR_LIST_Y0 = 52
ROW_H = 28


class Camera:
    """World coords: +x right, +y up (screen y flipped when projecting)."""

    def __init__(self) -> None:
        self.cx = 0.0
        self.cy = 0.0
        self.zoom = 0.35  # pixels per world unit

    def world_to_screen(self, wx: float, wy: float, view: pygame.Rect) -> Tuple[float, float]:
        sx = view.centerx + (wx - self.cx) * self.zoom
        sy = view.centery - (wy - self.cy) * self.zoom
        return sx, sy

    def screen_to_world(self, sx: float, sy: float, view: pygame.Rect) -> Tuple[float, float]:
        wx = self.cx + (sx - view.centerx) / self.zoom
        wy = self.cy - (sy - view.centery) / self.zoom
        return wx, wy

    def fit_bounds(
        self,
        view: pygame.Rect,
        points: List[Tuple[float, float]],
        margin: float = 0.12,
        zoom_min: float = 0.02,
        zoom_max: float = 12.0,
    ) -> None:
        if not points:
            self.cx, self.cy, self.zoom = 0.0, 0.0, 0.35
            return
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        self.cx = (min_x + max_x) / 2
        self.cy = (min_y + max_y) / 2
        w = max(max_x - min_x, 120.0)
        h = max(max_y - min_y, 120.0)
        zx = (view.width * (1 - 2 * margin)) / w
        zy = (view.height * (1 - 2 * margin)) / h
        self.zoom = max(zoom_min, min(zoom_max, min(zx, zy)))


class PygameUniverseGame:
    def __init__(
        self,
        initial_state: Multiverse,
        history: History,
        sim_config: SimulationConfig,
        width: int = 1280,
        height: int = 720,
        *,
        start_auto_play: bool = True,
    ) -> None:
        pygame.init()
        pygame.display.set_caption("Nested Universe Simulation — pan/zoom like a sandbox")
        self._windowed_size = (width, height)
        self._fullscreen = False
        self.screen = pygame.display.set_mode(self._windowed_size, pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 18)
        self.font_small = pygame.font.Font(None, 16)
        self.title_font = pygame.font.Font(None, 22)

        self.history = history
        self.sim_config = sim_config
        self.hist_idx = len(history.snapshots) - 1
        self.state = initial_state

        self.focus_id = self.state.root.id
        self._autofit_focus_id: Optional[int] = None
        self.list_scroll = 0
        self.sidebar_w = 260
        self.bottom_h = 132
        self.auto_play = start_auto_play
        self.base_auto_ms = 280.0
        self.speed_mult = 1.0
        self._motion_blend = 1.0

        self.camera = Camera()
        self._dragging_time = False
        self._panning = False
        self._pan_anchor_world: Optional[Tuple[float, float]] = None
        self._pan_anchor_screen: Optional[Tuple[float, float]] = None
        self._selected_bh_id: Optional[int] = None
        self._selected_body_id: Optional[int] = None
        self._bh_hit: List[Tuple[float, float, float, int]] = []
        self._body_hit: List[Tuple[float, float, float, int]] = []
        self._control_hit: List[Tuple[pygame.Rect, str]] = []

    @property
    def main_rect(self) -> pygame.Rect:
        w, h = self.screen.get_size()
        return pygame.Rect(self.sidebar_w, 0, w - self.sidebar_w, h - self.bottom_h)

    @property
    def sidebar_rect(self) -> pygame.Rect:
        w, h = self.screen.get_size()
        return pygame.Rect(0, 0, self.sidebar_w, h - self.bottom_h)

    @property
    def bottom_rect(self) -> pygame.Rect:
        w, h = self.screen.get_size()
        return pygame.Rect(0, h - self.bottom_h, w, self.bottom_h)

    def focus_universe(self) -> Universe:
        u = self.state.universes.get(self.focus_id)
        if u is None:
            self.focus_id = self.state.root.id
            u = self.state.root
        return u

    def set_hist_idx(self, idx: int) -> None:
        n = len(self.history.snapshots)
        if n == 0:
            return
        self.hist_idx = max(0, min(n - 1, idx))
        self.state = self.history.restore(self.hist_idx)
        if self.focus_id not in self.state.universes:
            self.focus_id = self.state.root.id

    def scrub_time_rel(self, delta: int) -> None:
        self.set_hist_idx(self.hist_idx + delta)

    def step_forward(self) -> None:
        n = len(self.history.snapshots)
        if self.hist_idx < n - 1:
            self.set_hist_idx(self.hist_idx + 1)
            return
        self.history.truncate_after(self.hist_idx)
        self.state = self.history.restore(self.hist_idx)
        step_multiverse(self.state, self.sim_config)
        self.history.snapshots.append(copy.deepcopy(self.state))
        self.hist_idx = len(self.history.snapshots) - 1
        self.state = self.history.restore(self.hist_idx)

    def _toggle_fullscreen(self) -> None:
        if self._fullscreen:
            self.screen = pygame.display.set_mode(self._windowed_size, pygame.RESIZABLE)
            self._fullscreen = False
        else:
            self._windowed_size = self.screen.get_size()
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            self._fullscreen = True

    def _zoom_at_screen(self, sx: float, sy: float, factor: float, view: pygame.Rect) -> None:
        wx, wy = self.camera.screen_to_world(sx, sy, view)
        z = self.camera.zoom * factor
        z = max(0.015, min(14.0, z))
        self.camera.zoom = z
        # keep world point under cursor
        self.camera.cx = wx - (sx - view.centerx) / self.camera.zoom
        self.camera.cy = wy + (sy - view.centery) / self.camera.zoom

    def _collect_world_points(self, u: Universe) -> List[Tuple[float, float]]:
        pts: List[Tuple[float, float]] = []
        for s in u.bodies:
            if s.kind == BodyKind.STAR:
                pts.append(_star_xy(s, u))
        for bh in u.black_holes:
            pts.append(_bh_xy(bh, u))
        for pl in u.bodies:
            if pl.kind != BodyKind.PLANET:
                continue
            star = None
            if pl.host_star_id is not None:
                for s in u.bodies:
                    if s.id == pl.host_star_id and s.kind == BodyKind.STAR:
                        star = s
                        break
            sx, sy = (0.0, 0.0)
            if star:
                sx, sy = _star_xy(star, u)
            orbit = planet_orbit_radius(pl, u)
            pts.append((sx + math.cos(pl.orbit_angle) * orbit, sy + math.sin(pl.orbit_angle) * orbit))
        if not pts:
            pts.append((0.0, 0.0))
        return pts

    def _maybe_autofit_camera(self, u: Universe) -> None:
        if self._autofit_focus_id == self.focus_id:
            return
        self.camera.fit_bounds(self.main_rect, self._collect_world_points(u))
        self._autofit_focus_id = self.focus_id

    def _auto_interval_ms(self, at_timeline_end: bool) -> float:
        """Shorter interval when replaying recorded history; scales with speed_mult."""
        base = self.base_auto_ms if at_timeline_end else self.base_auto_ms * 0.45
        return max(16.0, base / max(0.05, self.speed_mult))

    def run(self) -> None:
        running = True
        sim_accumulator = 0.0
        while running:
            frame_dt = self.clock.tick(60)
            view = self.main_rect
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE and not self._fullscreen:
                    self._windowed_size = (max(640, event.w), max(480, event.h))
                    self.screen = pygame.display.set_mode(self._windowed_size, pygame.RESIZABLE)
                elif event.type == pygame.KEYDOWN:
                    self._on_key(event, view)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self._on_mouse_down(event, view)
                elif event.type == pygame.MOUSEBUTTONUP:
                    self._on_mouse_up(event)
                elif event.type == pygame.MOUSEMOTION:
                    self._on_mouse_motion(event, view)
                elif event.type == pygame.MOUSEWHEEL:
                    self._on_mouse_wheel(event, view)

            if self.auto_play:
                at_end = self.hist_idx >= len(self.history.snapshots) - 1
                interval = self._auto_interval_ms(at_end)
                sim_accumulator += frame_dt
                max_burst = 1 if at_end else 24
                steps_done = 0
                while sim_accumulator >= interval and steps_done < max_burst:
                    sim_accumulator -= interval
                    steps_done += 1
                    if at_end:
                        self.step_forward()
                    else:
                        self.set_hist_idx(self.hist_idx + 1)
                        if self.hist_idx >= len(self.history.snapshots) - 1:
                            sim_accumulator = min(sim_accumulator, interval * 0.5)
                if at_end and interval > 1e-6:
                    self._motion_blend = min(1.0, sim_accumulator / interval)
                else:
                    self._motion_blend = 1.0
            else:
                sim_accumulator = 0.0
                self._motion_blend = 1.0

            keys = pygame.key.get_pressed()
            pan_px = 520.0 / max(0.08, self.camera.zoom) * (frame_dt / 1000.0)
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.camera.cx -= pan_px
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.camera.cx += pan_px
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.camera.cy += pan_px
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                self.camera.cy -= pan_px

            self._draw()
            pygame.display.flip()
        pygame.quit()

    def _on_key(self, event: pygame.event.Event, view: pygame.Rect) -> None:
        k = event.key
        if k == pygame.K_F11:
            self._toggle_fullscreen()
        elif k in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            u = self.focus_universe()
            p = parent_universe(u)
            if p is not None:
                self.focus_id = p.id
        elif k == pygame.K_HOME:
            u = self.focus_universe()
            self.camera.fit_bounds(view, self._collect_world_points(u))
            self._autofit_focus_id = self.focus_id
        elif k == pygame.K_LEFTBRACKET or k == pygame.K_COMMA:
            self.scrub_time_rel(-1)
        elif k == pygame.K_RIGHTBRACKET or k == pygame.K_PERIOD:
            self.scrub_time_rel(1)
        elif k == pygame.K_SPACE:
            self.step_forward()
        elif k == pygame.K_p:
            self.auto_play = not self.auto_play
        elif k == pygame.K_F5:
            self.speed_mult = max(0.1, self.speed_mult / 1.5)
        elif k == pygame.K_F6:
            self.speed_mult = min(64.0, self.speed_mult * 1.5)
        elif k == pygame.K_TAB:
            self._cycle_focus(1 if not (pygame.key.get_mods() & pygame.KMOD_SHIFT) else -1)
        elif k == pygame.K_PAGEUP:
            self._cycle_level(-1)
        elif k == pygame.K_PAGEDOWN:
            self._cycle_level(1)
        elif k == pygame.K_i:
            self._enter_selected_bh()
        elif k in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self._zoom_at_screen(view.centerx, view.centery, 1 / 1.15, view)
        elif k in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
            self._zoom_at_screen(view.centerx, view.centery, 1.15, view)

    def _cycle_focus(self, direction: int) -> None:
        order = bfs_universes(self.state)
        ids = [u.id for u in order]
        if not ids:
            return
        try:
            i = ids.index(self.focus_id)
        except ValueError:
            i = 0
        i = (i + direction) % len(ids)
        self.focus_id = ids[i]

    def _cycle_level(self, delta: int) -> None:
        depths = universe_depth_map(self.state)
        dcur = depths.get(self.focus_id, 0)
        target = max(0, dcur + delta)
        candidates = [u for u in bfs_universes(self.state) if depths.get(u.id, 0) == target]
        if candidates:
            self.focus_id = candidates[0].id

    def _enter_selected_bh(self) -> None:
        if self._selected_bh_id is None:
            return
        bh = self.state.black_holes.get(self._selected_bh_id)
        if bh is None or bh.inner_universe is None:
            return
        self.focus_id = bh.inner_universe.id

    def _on_mouse_wheel(self, event: pygame.event.Event, view: pygame.Rect) -> None:
        mx, my = pygame.mouse.get_pos()
        if self.sidebar_rect.collidepoint(mx, my):
            self.list_scroll -= event.y * ROW_H
            return
        if not view.collidepoint(mx, my):
            return
        factor = 1.12**event.y
        self._zoom_at_screen(float(mx), float(my), factor, view)

    def _on_mouse_down(self, event: pygame.event.Event, view: pygame.Rect) -> None:
        mx, my = event.pos
        br = self.bottom_rect
        for rect, action in self._control_hit:
            if rect.collidepoint(mx, my) and event.button == 1:
                if action == "pause":
                    self.auto_play = False
                elif action == "run":
                    self.auto_play = True
                elif action == "slower":
                    self.speed_mult = max(0.1, self.speed_mult / 1.5)
                elif action == "faster":
                    self.speed_mult = min(64.0, self.speed_mult * 1.5)
                return

        pad = 16
        bar = pygame.Rect(br.x + pad, br.y + 72, br.w - 2 * pad, 22)
        if bar.collidepoint(mx, my) and event.button == 1:
            self._dragging_time = True
            self._time_scrub_from_x(mx, bar)
            return

        if view.collidepoint(mx, my) and event.button in (2, 3):
            self._panning = True
            self._pan_anchor_screen = (float(mx), float(my))
            self._pan_anchor_world = (self.camera.cx, self.camera.cy)
            return

        if view.collidepoint(mx, my) and event.button == 1:
            wx, wy = self.camera.screen_to_world(float(mx), float(my), view)
            picks: List[Tuple[float, str, int]] = []
            for bx, by, wrad, bid in self._bh_hit:
                dist = math.hypot(wx - bx, wy - by)
                if dist <= wrad and wrad > 1e-6:
                    picks.append((dist / wrad, "bh", bid))
            for bx, by, wrad, bid in self._body_hit:
                dist = math.hypot(wx - bx, wy - by)
                if dist <= wrad and wrad > 1e-6:
                    picks.append((dist / wrad, "body", bid))
            if picks:
                picks.sort(key=lambda t: t[0])
                _, kind, bid = picks[0]
                if kind == "bh":
                    bh = self.state.black_holes.get(bid)
                    self._selected_bh_id = bid
                    self._selected_body_id = None
                    if bh and bh.inner_universe and (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                        self.focus_id = bh.inner_universe.id
                else:
                    self._selected_body_id = bid
                    self._selected_bh_id = None
                return

        sr = self.sidebar_rect
        if sr.collidepoint(mx, my) and event.button == 1:
            y0 = SIDEBAR_LIST_Y0 - self.list_scroll
            for u in bfs_universes(self.state):
                row = pygame.Rect(4, y0, sr.w - 8, ROW_H)
                if row.collidepoint(mx, my):
                    self.focus_id = u.id
                    return
                y0 += ROW_H

    def _on_mouse_up(self, event: pygame.event.Event) -> None:
        if event.button == 1:
            self._dragging_time = False
        if event.button in (2, 3):
            self._panning = False
            self._pan_anchor_screen = None
            self._pan_anchor_world = None

    def _on_mouse_motion(self, event: pygame.event.Event, view: pygame.Rect) -> None:
        if self._dragging_time:
            bar = pygame.Rect(
                self.bottom_rect.x + 16,
                self.bottom_rect.y + 72,
                self.bottom_rect.w - 32,
                22,
            )
            self._time_scrub_from_x(event.pos[0], bar)
        elif self._panning and self._pan_anchor_screen and self._pan_anchor_world:
            sx0, sy0 = self._pan_anchor_screen
            wcx0, wcy0 = self._pan_anchor_world
            dx = event.pos[0] - sx0
            dy = event.pos[1] - sy0
            self.camera.cx = wcx0 - dx / self.camera.zoom
            self.camera.cy = wcy0 + dy / self.camera.zoom

    def _time_scrub_from_x(self, mx: int, bar: pygame.Rect) -> None:
        n = len(self.history.snapshots)
        if n <= 1:
            return
        t = (mx - bar.x) / max(1, bar.w)
        t = max(0.0, min(1.0, t))
        self.set_hist_idx(int(round(t * (n - 1))))

    def _draw_soft_gas_blob_screen(
        self, cx: int, cy: int, max_r_px: int, base: Tuple[int, int, int], seed: int
    ) -> None:
        if max_r_px < 10:
            return
        w = max_r_px * 2 + 10
        s = pygame.Surface((w, w), pygame.SRCALPHA)
        ctr = w // 2
        for k in range(7):
            t = k / 6.0
            rr = max(5, int(max_r_px * (0.3 + t * 0.68)))
            ox = ((seed >> (k * 4)) & 31) - 15
            oy = ((seed >> (k * 4 + 2)) & 31) - 15
            a = max(10, min(52, 18 + k * 5 + (seed & 7)))
            pygame.draw.circle(s, (*base, a), (ctr + ox, ctr + oy), rr)
        self.screen.blit(s, (cx - ctr, cy - ctr))

    def _draw_ambient_gas(self, view: pygame.Rect, u: Universe) -> None:
        """Large colored gas clouds (world-fixed); no camera-dependent pattern shift."""
        S = sector_scale(u)
        nb = len(u.bodies)
        n_layers = 8 if nb > 160 else 14
        palettes = (
            (88, 52, 128),
            (42, 92, 158),
            (132, 68, 118),
            (52, 124, 108),
            (108, 72, 148),
            (72, 48, 112),
            (58, 110, 150),
        )
        for j in range(n_layers):
            seed = self.focus_id * 10007 + j * 7919 + u.id * 17
            a = _stable_angle(seed)
            rr = S * (0.18 + 0.78 * hash01(seed + 3))
            wx = rr * math.cos(a)
            wy = rr * math.sin(a * 1.02)
            sx, sy = self.camera.world_to_screen(wx, wy, view)
            if not view.collidepoint(int(sx), int(sy)) and j > n_layers - 5:
                continue
            base = palettes[j % len(palettes)]
            rmul = 0.72 if nb > 200 else 1.0
            max_r_px = int(max(70, min(420, S * 0.2 * self.camera.zoom * rmul)))
            self._draw_soft_gas_blob_screen(int(sx), int(sy), max_r_px, base, seed)

    def _draw_starfield(self, view: pygame.Rect) -> None:
        """Distant stars in world space; seed depends only on universe (pan = translation)."""
        u0 = self.focus_universe()
        rng_mod = (self.focus_id * 997 + u0.id * 41) & 0xFFFF
        cap_r = int(sector_scale(u0) * 2.6)
        n_pts = 220 if len(u0.bodies) > 180 else 420
        for i in range(n_pts):
            a = _stable_angle(i * 7919 + rng_mod)
            rr = 40 + (i * 163) % max(120, cap_r)
            wx = rr * math.cos(a)
            wy = rr * math.sin(a * 1.041)
            sx, sy = self.camera.world_to_screen(wx, wy, view)
            if not view.collidepoint(int(sx), int(sy)):
                continue
            br = 1 if i % 5 else 2
            tint = 32 + (i % 7) * 4
            pygame.draw.circle(self.screen, (tint, tint + 6, tint + 14), (int(sx), int(sy)), br)

    def _draw_hud_panel(self, view: pygame.Rect) -> None:
        lines = [
            f"tick {self.state.global_tick}   history {self.hist_idx + 1}/{len(self.history.snapshots)}",
            f"{'RUN' if self.auto_play else 'PAUSE'}   {self.speed_mult:.2f}x   zoom {self.camera.zoom:.3f}",
        ]
        w = max(self.font.size(ln)[0] for ln in lines) + 20
        h = len(lines) * 20 + 14
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        surf.fill((18, 22, 40, 220))
        for i, ln in enumerate(lines):
            surf.blit(self.font.render(ln, True, (220, 225, 240)), (10, 8 + i * 20))
        self.screen.blit(surf, (view.right - w - 8, view.y + 8))

    def _draw(self) -> None:
        self.screen.fill((12, 14, 28))
        self._draw_sidebar()
        self._draw_cosmic()
        self._draw_bottom_bar()
        self._draw_hud_panel(self.main_rect)

    def _draw_sidebar(self) -> None:
        sr = self.sidebar_rect
        pygame.draw.rect(self.screen, (22, 26, 42), sr)
        pygame.draw.line(self.screen, (60, 70, 100), (sr.right - 1, sr.y), (sr.right - 1, sr.bottom), 1)
        t = self.title_font.render("Universes", True, (220, 225, 240))
        self.screen.blit(t, (8, 8))
        hint = self.font_small.render("Click row · Tab next", True, (140, 150, 175))
        self.screen.blit(hint, (8, 30))
        depths = universe_depth_map(self.state)
        y = SIDEBAR_LIST_Y0 - self.list_scroll
        for u in bfs_universes(self.state):
            d = depths.get(u.id, 0)
            sel = u.id == self.focus_id
            row = pygame.Rect(4, y, sr.w - 8, ROW_H)
            if row.bottom < sr.y or row.y > sr.bottom:
                y += ROW_H
                continue
            bg = (50, 70, 120) if sel else (32, 38, 58)
            pygame.draw.rect(self.screen, bg, row, border_radius=4)
            life = "*" if u.has_life else ""
            n_stars = sum(1 for b in u.bodies if b.kind == BodyKind.STAR)
            label = f"L{d}  U{u.id}  ★{n_stars} {life}"
            self.screen.blit(self.font_small.render(label, True, (230, 235, 245)), (row.x + 6, row.y + 5))
            y += ROW_H

    def _draw_cosmic(self) -> None:
        r = self.main_rect
        pygame.draw.rect(self.screen, (6, 8, 18), r)
        u = self.focus_universe()
        self._maybe_autofit_camera(u)
        depths = universe_depth_map(self.state)
        d = depths.get(u.id, 0)
        p = u.physics
        S = sector_scale(u)

        Rlim = universe_world_radius(u, self.sim_config)
        title = (
            f"Sector U{u.id}   level {d}   scale={u.scale:.2f}   R≈{S:.0f} wu   Rlim≈{Rlim:.0f} wu"
        )
        self.screen.blit(self.title_font.render(title, True, (240, 240, 250)), (r.x + 10, r.y + 6))
        prof = f"g={p.gravity_coupling:.2f}  rad={p.radiation_efficiency:.2f}  str={p.structure_bias:.2f}  ex={p.exotic_permit:.2f}  chem={p.chemistry_ease:.2f}"
        self.screen.blit(self.font_small.render(prof, True, (160, 170, 200)), (r.x + 10, r.y + 30))
        info_used = universe_body_information_used(u)
        latent = u.latent_information
        budg = f"matter here {info_used:.1f} / {u.information_budget:.1f}"
        if latent > 0.01:
            budg += f"   latent {latent:.1f}"
        self.screen.blit(self.font_small.render(budg, True, (140, 200, 175)), (r.x + 10, r.y + 48))
        root_b0 = self.state.root.information_budget
        tot = total_information_in_multiverse(self.state)
        tree_line = f"conserved total {tot:.1f} / {root_b0:.1f} (bodies+latent+in BHs)"
        self.screen.blit(self.font_small.render(tree_line, True, (160, 185, 210)), (r.x + 10, r.y + 64))
        csum = child_inner_information_caps_sum(u)
        cap_line = f"inner Σ caps {csum:.1f} ≤ host {u.information_budget:.1f}"
        self.screen.blit(self.font_small.render(cap_line, True, (130, 165, 190)), (r.x + 10, r.y + 82))

        clip = self.screen.get_clip()
        self.screen.set_clip(r)
        self._draw_starfield(r)
        self._draw_ambient_gas(r, u)

        mb = self._motion_blend
        cx0, cy0 = self.camera.world_to_screen(0.0, 0.0, r)
        rad_lim = int(Rlim * self.camera.zoom)
        if 3 < rad_lim < 9000:
            pygame.draw.circle(self.screen, (48, 58, 88), (int(cx0), int(cy0)), rad_lim, 1)

        stars = [b for b in u.bodies if b.kind == BodyKind.STAR]
        star_pos: Dict[int, Tuple[float, float]] = {s.id: _star_xy(s, u) for s in stars}
        star_draw: Dict[int, Tuple[float, float]] = {s.id: _blended_body_xy(s, mb) for s in stars}
        self._bh_hit = []
        self._body_hit = []

        for s in stars:
            wx, wy = star_draw[s.id]
            sx, sy = self.camera.world_to_screen(wx, wy, r)
            rad = max(4, int((6 + s.mass_index * 10) * min(2.0, self.camera.zoom**0.35)))
            wr = max(14.0, (rad + 6) / self.camera.zoom)
            self._body_hit.append((star_pos[s.id][0], star_pos[s.id][1], wr, s.id))
            diam = max(8, min(96, rad * 2 + 2))
            col = star_spectral_rgb(s)
            spr = proc_sprites.star_sprite(diam, s.id, col)
            self.screen.blit(spr, spr.get_rect(center=(int(sx), int(sy))))
            if s.id == self._selected_body_id:
                pygame.draw.circle(self.screen, (255, 255, 120), (int(sx), int(sy)), rad + 5, 2)
                lb = self.font_small.render(f"★{s.id}", True, (235, 240, 255))
                self.screen.blit(lb, (int(sx) - lb.get_width() // 2, int(sy) + rad + 6))

        if not stars:
            sx, sy = self.camera.world_to_screen(0.0, 0.0, r)
            pygame.draw.circle(self.screen, (55, 50, 65), (int(sx), int(sy)), 6)
            self.screen.blit(self.font_small.render("no stars", True, (150, 150, 170)), (int(sx) - 32, int(sy) + 14))

        n_planets = sum(1 for b in u.bodies if b.kind == BodyKind.PLANET)
        nb_all = len(u.bodies)
        crowded = n_planets > 50 or nb_all > 190
        zoom_ok = self.camera.zoom > 0.11

        for pl in u.bodies:
            if pl.kind != BodyKind.PLANET:
                continue
            swx, swy = (0.0, 0.0)
            if pl.host_star_id is not None and pl.host_star_id in star_draw:
                swx, swy = star_draw[pl.host_star_id]
            orbit = planet_orbit_radius(pl, u)
            if pl.spatial_ready:
                pwx, pwy = _blended_body_xy(pl, mb)
            else:
                pwx = swx + math.cos(pl.orbit_angle) * orbit
                pwy = swy + math.sin(pl.orbit_angle) * orbit
            psx, psy = self.camera.world_to_screen(swx, swy, r)
            ppx, ppy = self.camera.world_to_screen(pwx, pwy, r)
            draw_orbit = (not crowded or pl.id == self._selected_body_id) and zoom_ok
            if draw_orbit:
                pygame.draw.circle(
                    self.screen, (45, 50, 68), (int(psx), int(psy)), int(max(2, orbit * self.camera.zoom)), 1
                )
            pr = max(2, int((2.5 + pl.mass_index * 5) * min(1.8, self.camera.zoom**0.35)))
            wrp = max(12.0, (pr + 8) / self.camera.zoom)
            hpx, hpy = (pl.pos_x, pl.pos_y) if pl.spatial_ready else (pwx, pwy)
            self._body_hit.append((hpx, hpy, wrp, pl.id))
            col = life_color(pl.life_stage)
            pd = max(10, min(64, pr * 2 + 4))
            psurf = proc_sprites.planet_sprite(pd, pl.id, col)
            self.screen.blit(psurf, psurf.get_rect(center=(int(ppx), int(ppy))))
            pygame.draw.circle(self.screen, (255, 255, 255), (int(ppx), int(ppy)), pr + 1, 1)
            if pl.id == self._selected_body_id:
                pygame.draw.circle(self.screen, (255, 255, 120), (int(ppx), int(ppy)), pr + 6, 2)
                lb = self.font_small.render(f"P{pl.id}", True, (235, 240, 255))
                self.screen.blit(lb, (int(ppx) - lb.get_width() // 2, int(ppy) + pr + 6))

        for moon in u.bodies:
            if moon.kind != BodyKind.MOON:
                continue
            pl = None
            if moon.host_planet_id is not None:
                for p in u.bodies:
                    if p.id == moon.host_planet_id and p.kind == BodyKind.PLANET:
                        pl = p
                        break
            if pl is None:
                candidates = [
                    p
                    for p in u.bodies
                    if p.kind == BodyKind.PLANET
                    and (moon.host_star_id is None or p.host_star_id == moon.host_star_id)
                ]
                pl = candidates[0] if candidates else None
            if pl is None:
                continue
            if pl.spatial_ready:
                pwx, pwy = _blended_body_xy(pl, mb)
            else:
                swx, swy = (0.0, 0.0)
                if pl.host_star_id is not None and pl.host_star_id in star_draw:
                    swx, swy = star_draw[pl.host_star_id]
                porb = planet_orbit_radius(pl, u)
                pwx = swx + math.cos(pl.orbit_angle) * porb
                pwy = swy + math.sin(pl.orbit_angle) * porb
            if moon.spatial_ready:
                mwx, mwy = _blended_body_xy(moon, mb)
            else:
                mwx = pwx + math.cos(moon.moon_orbit_angle) * 22
                mwy = pwy + math.sin(moon.moon_orbit_angle) * 22
            mx, my = self.camera.world_to_screen(mwx, mwy, r)
            mr = max(2, int(3 * min(1.5, self.camera.zoom**0.35)))
            wrm = max(10.0, (mr + 6) / self.camera.zoom)
            mhx, mhy = (moon.pos_x, moon.pos_y) if moon.spatial_ready else (mwx, mwy)
            self._body_hit.append((mhx, mhy, wrm, moon.id))
            md = max(6, min(40, mr * 2 + 2))
            ms = proc_sprites.moon_sprite(md, moon.id)
            self.screen.blit(ms, ms.get_rect(center=(int(mx), int(my))))
            if moon.id == self._selected_body_id:
                pygame.draw.circle(self.screen, (255, 255, 120), (int(mx), int(my)), mr + 5, 2)
                lb = self.font_small.render(f"M{moon.id}", True, (235, 240, 255))
                self.screen.blit(lb, (int(mx) - lb.get_width() // 2, int(my) + mr + 6))

        neb_pals = (
            (120, 70, 175),
            (55, 110, 185),
            (165, 85, 145),
            (70, 140, 155),
            (130, 95, 175),
        )
        for neb in u.bodies:
            if neb.kind != BodyKind.NEBULA:
                continue
            nwx, nwy = _blended_body_xy(neb, mb) if neb.spatial_ready else _neb_xy(neb, u)
            nx, ny = self.camera.world_to_screen(nwx, nwy, r)
            base = neb_pals[neb.id % len(neb_pals)]
            ref_m = 0.52
            mi_scale = max(0.15, min(1.55, (neb.mass_index / ref_m) ** 0.55))
            rpx = int(max(22, min(360, S * 0.28 * self.camera.zoom * mi_scale)))
            self._draw_soft_gas_blob_screen(int(nx), int(ny), rpx, base, neb.id * 1103515245)
            if neb.mass_index > 0.16:
                self._draw_soft_gas_blob_screen(
                    int(nx + rpx * 0.08), int(ny - rpx * 0.06), int(rpx * 0.72), base, neb.id * 7919 + 3
                )
            wrn = max(22.0, S * 0.12)
            nnx, nny = _neb_xy(neb, u)
            self._body_hit.append((nnx, nny, wrn, neb.id))
            if neb.id == self._selected_body_id:
                pygame.draw.circle(self.screen, (255, 255, 120), (int(nx), int(ny)), int(rpx * 0.35) + 8, 2)
                lb = self.font_small.render(f"Neb{neb.id}", True, (235, 240, 255))
                self.screen.blit(lb, (int(nx) - lb.get_width() // 2, int(ny) + int(rpx * 0.28)))

        for ex in u.bodies:
            if ex.kind != BodyKind.EXOTIC:
                continue
            ewx, ewy = _blended_body_xy(ex, mb) if ex.spatial_ready else _ex_xy(ex, u)
            exx, exy = self.camera.world_to_screen(ewx, ewy, r)
            sz = max(10, int(14 * min(1.5, self.camera.zoom**0.35)))
            wre = max(12.0, (sz + 8) / self.camera.zoom)
            ehx, ehy = _ex_xy(ex, u)
            self._body_hit.append((ehx, ehy, wre, ex.id))
            es = proc_sprites.exotic_sprite(sz * 2, ex.id)
            self.screen.blit(es, es.get_rect(center=(int(exx), int(exy))))
            if ex.id == self._selected_body_id:
                pygame.draw.circle(self.screen, (255, 255, 120), (int(exx), int(exy)), sz + 6, 2)
                lb = self.font_small.render(f"X{ex.id}", True, (235, 240, 255))
                self.screen.blit(lb, (int(exx) - lb.get_width() // 2, int(exy) + sz + 6))

        for bh in u.black_holes:
            wx, wy = _blended_bh_xy(bh, mb)
            sx, sy = self.camera.world_to_screen(wx, wy, r)
            br = max(6, int((10 + min(28, bh.mass * 5)) * min(1.6, self.camera.zoom**0.35)))
            wr_hit = max(18.0, (br + 10) / self.camera.zoom)
            hbx, hby = _bh_xy(bh, u)
            self._bh_hit.append((hbx, hby, wr_hit, bh.id))
            sel = bh.id == self._selected_bh_id
            bd = max(14, min(92, br * 2 + 6))
            bsurf = proc_sprites.black_hole_sprite(bd, bh.id)
            self.screen.blit(bsurf, bsurf.get_rect(center=(int(sx), int(sy))))
            pygame.draw.circle(self.screen, (255, 150, 50), (int(sx), int(sy)), br + 4, 2)
            if bh.inner_universe:
                pygame.draw.circle(self.screen, (80, 220, 255), (int(sx), int(sy)), max(5, br // 2), 2)
            if sel:
                pygame.draw.circle(self.screen, (255, 255, 120), (int(sx), int(sy)), br + 6, 2)
            lbl = self.font_small.render(f"BH{bh.id}", True, (230, 235, 250))
            self.screen.blit(lbl, (int(sx) - lbl.get_width() // 2, int(sy) + br + 4))

        self.screen.set_clip(clip)

        help_lines = [
            "Wheel zoom · Right/MMB drag pan · hold WASD/arrows to move map",
            "Home fit · +/- zoom · F11 fullscreen · bottom bar: Pause / Run / Slower / Faster",
            "[ ] scrub time · Space one step · P run/pause · F5/F6 speed · Tab universe",
        ]
        hy = r.bottom - 54
        for line in help_lines:
            self.screen.blit(self.font_small.render(line, True, (115, 125, 155)), (r.x + 10, hy))
            hy += 16

    def _draw_bottom_bar(self) -> None:
        br = self.bottom_rect
        pygame.draw.rect(self.screen, (20, 22, 38), br)
        pygame.draw.line(self.screen, (60, 70, 100), (br.x, br.y), (br.right, br.y), 1)
        n = len(self.history.snapshots)
        pad = 16
        self._control_hit.clear()
        btn_y = br.y + 8
        x = pad
        for label, w, action in (
            ("Pause", 76, "pause"),
            ("Run", 68, "run"),
            ("Slower", 78, "slower"),
            ("Faster", 78, "faster"),
        ):
            rr = pygame.Rect(x, btn_y, w, 30)
            self._control_hit.append((rr, action))
            if action == "pause" and not self.auto_play:
                bg = (72, 92, 140)
            elif action == "run" and self.auto_play:
                bg = (72, 92, 140)
            else:
                bg = (44, 50, 78)
            pygame.draw.rect(self.screen, bg, rr, border_radius=6)
            pygame.draw.rect(self.screen, (95, 105, 140), rr, 1, border_radius=6)
            lab = self.font_small.render(label, True, (235, 238, 250))
            self.screen.blit(lab, (rr.centerx - lab.get_width() // 2, rr.centery - lab.get_height() // 2))
            x += w + 8

        fs = "F11 window" if self._fullscreen else "F11 full"
        self.screen.blit(
            self.font_small.render(f"Timeline  {self.hist_idx + 1} / {n}   {fs}", True, (190, 195, 215)),
            (br.x + pad, br.y + 44),
        )
        bar = pygame.Rect(br.x + pad, br.y + 72, br.w - 2 * pad, 22)
        pygame.draw.rect(self.screen, (40, 44, 64), bar, border_radius=6)
        if n > 0:
            t = self.hist_idx / max(1, n - 1)
            knob_x = int(bar.x + t * bar.w)
            pygame.draw.circle(self.screen, (220, 225, 240), (knob_x, bar.centery), 10)


def run_pygame_game(
    m: Multiverse,
    history: History,
    sim_config: Optional[SimulationConfig] = None,
    *,
    start_auto_play: bool = True,
) -> None:
    if sim_config is None:
        sim_config = SimulationConfig()
    game = PygameUniverseGame(m, history, sim_config, start_auto_play=start_auto_play)
    game.run()
