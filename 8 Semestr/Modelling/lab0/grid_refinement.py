import numpy as np


class GridRefinement:
    def __init__(self, X=None, Y=None, Z=None):
        if X is None:
            X = []
        if Y is None:
            Y = []
        if Z is None:
            Z = np.array([[0]])

        self.X = np.array(X, dtype=float)
        self.Y = np.array(Y, dtype=float)
        self.Z = np.array(Z, dtype=float)

        if len(self.X) > 0 and len(self.Y) > 0:
            if self.Z.shape != (len(self.X), len(self.Y)):
                raise ValueError(
                    f"Размерность Z должна быть ({len(self.X)}, {len(self.Y)}), "
                    f"получено {self.Z.shape}"
                )

        self.N_x = max(0, len(self.X) - 1)
        self.N_y = max(0, len(self.Y) - 1)

        self.points = None
        self.values = None
        self.triangles = None

    def _build_triangulation(self):
        if self.triangles is not None:
            return

        if len(self.X) == 0 or len(self.Y) == 0:
            return

        pts = []
        vals = []
        for i in range(len(self.X)):
            for j in range(len(self.Y)):
                pts.append([self.X[i], self.Y[j]])
                vals.append(self.Z[i, j])

        self.points = np.array(pts, dtype=float)
        self.values = np.array(vals, dtype=float)

        self.triangles = self._bowyer_watson(self.points)

    @staticmethod
    def _circumcircle(p1, p2, p3):
        ax, ay = p1
        bx, by = p2
        cx, cy = p3

        D = 2.0 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))

        if abs(D) < 1e-12:
            mid_x = (ax + bx + cx) / 3.0
            mid_y = (ay + by + cy) / 3.0
            return mid_x, mid_y, float('inf')

        a_sq = ax * ax + ay * ay
        b_sq = bx * bx + by * by
        c_sq = cx * cx + cy * cy

        ux = (a_sq * (by - cy) + b_sq * (cy - ay) + c_sq * (ay - by)) / D
        uy = (a_sq * (cx - bx) + b_sq * (ax - cx) + c_sq * (bx - ax)) / D

        r_sq = (ax - ux) ** 2 + (ay - uy) ** 2
        return ux, uy, r_sq

    @staticmethod
    def _bowyer_watson(points):
        n = len(points)
        if n < 3:
            return []

        x_min = points[:, 0].min()
        x_max = points[:, 0].max()
        y_min = points[:, 1].min()
        y_max = points[:, 1].max()

        dx = x_max - x_min
        dy = y_max - y_min
        d_max = max(dx, dy, 1e-6)

        mid_x = (x_min + x_max) / 2.0
        mid_y = (y_min + y_max) / 2.0

        p0 = [mid_x - 20.0 * d_max, mid_y - d_max]
        p1 = [mid_x + 20.0 * d_max, mid_y - d_max]
        p2 = [mid_x, mid_y + 20.0 * d_max]

        all_points = list(points) + [p0, p1, p2]
        all_points_arr = np.array(all_points, dtype=float)

        triangles = {(n, n + 1, n + 2)}

        cc_cache = {}
        t0 = (n, n + 1, n + 2)
        cc_cache[t0] = GridRefinement._circumcircle(
            all_points_arr[t0[0]], all_points_arr[t0[1]], all_points_arr[t0[2]]
        )

        for idx in range(n):
            px, py = all_points_arr[idx]

            bad_triangles = set()
            for tri in triangles:
                cx, cy, r_sq = cc_cache[tri]
                dist_sq = (px - cx) ** 2 + (py - cy) ** 2
                if dist_sq < r_sq + 1e-10:
                    bad_triangles.add(tri)

            edge_count = {}
            for tri in bad_triangles:
                edges = [
                    (tri[0], tri[1]),
                    (tri[1], tri[2]),
                    (tri[0], tri[2]),
                ]
                for e in edges:
                    e_sorted = tuple(sorted(e))
                    edge_count[e_sorted] = edge_count.get(e_sorted, 0) + 1

            boundary_edges = [e for e, cnt in edge_count.items() if cnt == 1]

            for tri in bad_triangles:
                triangles.discard(tri)
                cc_cache.pop(tri, None)

            for e in boundary_edges:
                new_tri = tuple(sorted((e[0], e[1], idx)))
                triangles.add(new_tri)
                cc_cache[new_tri] = GridRefinement._circumcircle(
                    all_points_arr[new_tri[0]],
                    all_points_arr[new_tri[1]],
                    all_points_arr[new_tri[2]],
                )

        super_indices = {n, n + 1, n + 2}
        result = []
        for tri in triangles:
            if super_indices.isdisjoint(tri):
                result.append(tri)

        return result

    @staticmethod
    def _barycentric_coords(px, py, x1, y1, x2, y2, x3, y3):
        denom = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)

        if abs(denom) < 1e-14:
            return -1.0, -1.0, -1.0

        lam1 = ((y2 - y3) * (px - x3) + (x3 - x2) * (py - y3)) / denom
        lam2 = ((y3 - y1) * (px - x3) + (x1 - x3) * (py - y3)) / denom
        lam3 = 1.0 - lam1 - lam2

        return lam1, lam2, lam3

    def delaunay_interpolation(self, x, y):
        if self.triangles is None:
            self._build_triangulation()

        if self.triangles is None or len(self.triangles) == 0:
            return self.Z[0, 0] if self.Z.size > 0 else 0.0

        eps = -1e-10

        for tri in self.triangles:
            i0, i1, i2 = tri
            x1, y1 = self.points[i0]
            x2, y2 = self.points[i1]
            x3, y3 = self.points[i2]

            lam1, lam2, lam3 = self._barycentric_coords(
                x, y, x1, y1, x2, y2, x3, y3
            )

            if lam1 >= eps and lam2 >= eps and lam3 >= eps:
                z = (lam1 * self.values[i0]
                     + lam2 * self.values[i1]
                     + lam3 * self.values[i2])
                return z

        dists = (self.points[:, 0] - x) ** 2 + (self.points[:, 1] - y) ** 2
        nearest = np.argmin(dists)
        return self.values[nearest]
