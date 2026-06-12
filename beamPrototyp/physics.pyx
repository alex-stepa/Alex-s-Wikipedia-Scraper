# physics.pyx
import numpy as np
cimport numpy as np
from libc.math cimport sqrt, fabs

ctypedef np.float64_t F64

def build_sphere(int num_lat, int num_lon, double R,
                 double cx, double cy, double cz):
    import numpy as np
    from math import pi, sin, cos
    pts = []
    faces = []

    pts.append([cx, cy - R, cz])
    for lat in range(1, num_lat + 1):
        phi = pi * lat / (num_lat + 1)
        for lon in range(num_lon):
            theta = 2 * pi * lon / num_lon
            pts.append([
                cx + R * sin(phi) * cos(theta),
                cy - R * cos(phi),
                cz + R * sin(phi) * sin(theta)
            ])
    pts.append([cx, cy + R, cz])

    # top cap
    for lon in range(num_lon):
        a = 1 + lon
        b = 1 + (lon + 1) % num_lon
        faces.append((0, a, b))
    # bands
    for lat in range(num_lat - 1):
        for lon in range(num_lon):
            a = 1 + lat * num_lon + lon
            b = 1 + lat * num_lon + (lon + 1) % num_lon
            c = 1 + (lat + 1) * num_lon + lon
            d = 1 + (lat + 1) * num_lon + (lon + 1) % num_lon
            faces.append((a, b, d))
            faces.append((a, d, c))
    # bottom cap
    bot = len(pts) - 1
    lrs = 1 + (num_lat - 1) * num_lon
    for lon in range(num_lon):
        a = lrs + lon
        b = lrs + (lon + 1) % num_lon
        faces.append((a, bot, b))

    return np.array(pts, dtype=np.float64), faces


def build_beams(np.ndarray[F64, ndim=2] pos, list faces):
    edges = set()
    for f in faces:
        for i in range(3):
            a, b = f[i], f[(i + 1) % 3]
            edges.add((min(a, b), max(a, b)))
        for i in range(3):
            for j in range(i + 2, 3):
                a, b = f[i], f[j]
                edges.add((min(a, b), max(a, b)))
    beams = np.array(list(edges), dtype=np.int32)
    rests = np.array([
        sqrt(sum((pos[b][k] - pos[a][k])**2 for k in range(3)))
        for a, b in beams
    ], dtype=np.float64)
    return beams, rests


def step(
    np.ndarray[F64, ndim=2] pos,
    np.ndarray[F64, ndim=2] vel,
    np.ndarray[np.int32_t, ndim=2] beams,
    np.ndarray[F64, ndim=1] rests,
    list faces,
    double rest_vol,
    int substeps,
    double dt,
    double stiff,
    double damp,
    double pressure,
    double gravity,
    double floor_y,
    int drag_idx,
    np.ndarray[F64, ndim=1] drag_target,
):
    cdef int i, j, s, fi
    cdef int na, nb
    cdef int N = pos.shape[0]
    cdef int M = beams.shape[0]
    cdef double sub_dt = dt / substeps

    cdef double dx, dy, dz, L, L0, stretch, dvx, dvy, dvz, dv, force
    cdef double nx, ny, nz
    cdef double vol, P
    cdef double e1x, e1y, e1z, e2x, e2y, e2z
    cdef double cnx, cny, cnz, cn_len, area_f
    cdef double mx, my_c, mz, dot
    cdef double pfx, pfy, pfz
    cdef double bouncex, bouncey, bouncez

    cdef np.ndarray[F64, ndim=2] f = np.empty((N, 3), dtype=np.float64)

    for s in range(substeps):
        f[:] = 0.0
        f[:, 1] += gravity  # gravity

        # beam forces
        for i in range(M):
            na = beams[i, 0]
            nb = beams[i, 1]
            dx = pos[nb, 0] - pos[na, 0]
            dy = pos[nb, 1] - pos[na, 1]
            dz = pos[nb, 2] - pos[na, 2]
            L = sqrt(dx*dx + dy*dy + dz*dz)
            if L < 1e-9:
                continue
            nx = dx / L
            ny = dy / L
            nz = dz / L
            L0 = rests[i]
            stretch = L - L0
            dvx = vel[nb, 0] - vel[na, 0]
            dvy = vel[nb, 1] - vel[na, 1]
            dvz = vel[nb, 2] - vel[na, 2]
            dv = dvx*nx + dvy*ny + dvz*nz
            force = stiff * stretch + damp * dv
            if force > 6000.0: force = 6000.0
            if force < -6000.0: force = -6000.0
            f[na, 0] += force * nx
            f[na, 1] += force * ny
            f[na, 2] += force * nz
            f[nb, 0] -= force * nx
            f[nb, 1] -= force * ny
            f[nb, 2] -= force * nz

        # 3D pressure (signed volume)
        vol = 0.0
        for fi in range(len(faces)):
            fa = faces[fi]
            i0, i1, i2 = fa[0], fa[1], fa[2]
            vol += (pos[i0, 0] * (pos[i1, 1] * pos[i2, 2] - pos[i2, 1] * pos[i1, 2])
                  - pos[i0, 1] * (pos[i1, 0] * pos[i2, 2] - pos[i2, 0] * pos[i1, 2])
                  + pos[i0, 2] * (pos[i1, 0] * pos[i2, 1] - pos[i2, 0] * pos[i1, 1]))
        vol = fabs(vol) / 6.0
        if vol < rest_vol * 0.15:
            vol = rest_vol * 0.15
        P = pressure * rest_vol / vol
        if P > pressure * 5.0:
            P = pressure * 5.0

        for fi in range(len(faces)):
            fa = faces[fi]
            i0, i1, i2 = fa[0], fa[1], fa[2]
            e1x = pos[i1, 0] - pos[i0, 0]
            e1y = pos[i1, 1] - pos[i0, 1]
            e1z = pos[i1, 2] - pos[i0, 2]
            e2x = pos[i2, 0] - pos[i0, 0]
            e2y = pos[i2, 1] - pos[i0, 1]
            e2z = pos[i2, 2] - pos[i0, 2]
            cnx = e1y*e2z - e1z*e2y
            cny = e1z*e2x - e1x*e2z
            cnz = e1x*e2y - e1y*e2x
            cn_len = sqrt(cnx*cnx + cny*cny + cnz*cnz)
            if cn_len < 1e-9:
                continue
            cnx /= cn_len
            cny /= cn_len
            cnz /= cn_len
            mx = (pos[i0, 0] + pos[i1, 0] + pos[i2, 0]) / 3.0
            my_c = (pos[i0, 1] + pos[i1, 1] + pos[i2, 1]) / 3.0
            mz = (pos[i0, 2] + pos[i1, 2] + pos[i2, 2]) / 3.0
            dot = cnx*mx + cny*my_c + cnz*mz
            if dot < 0:
                cnx = -cnx
                cny = -cny
                cnz = -cnz
            pfx = cnx * P * cn_len / 3.0
            pfy = cny * P * cn_len / 3.0
            pfz = cnz * P * cn_len / 3.0
            f[i0, 0] += pfx; f[i0, 1] += pfy; f[i0, 2] += pfz
            f[i1, 0] += pfx; f[i1, 1] += pfy; f[i1, 2] += pfz
            f[i2, 0] += pfx; f[i2, 1] += pfy; f[i2, 2] += pfz

        # integrate
        for i in range(N):
            if i == drag_idx:
                continue
            vel[i, 0] += f[i, 0] * sub_dt
            vel[i, 1] += f[i, 1] * sub_dt
            vel[i, 2] += f[i, 2] * sub_dt
            pos[i, 0] += vel[i, 0] * sub_dt
            pos[i, 1] += vel[i, 1] * sub_dt
            pos[i, 2] += vel[i, 2] * sub_dt

        # drag
        if drag_idx >= 0:
            pos[drag_idx, 0] += (drag_target[0] - pos[drag_idx, 0]) * 0.3
            pos[drag_idx, 1] += (drag_target[1] - pos[drag_idx, 1]) * 0.3
            pos[drag_idx, 2] += (drag_target[2] - pos[drag_idx, 2]) * 0.3
            vel[drag_idx, 0] = 0.0
            vel[drag_idx, 1] = 0.0
            vel[drag_idx, 2] = 0.0

        # collisions
        for i in range(N):
            if pos[i, 1] > floor_y:
                pos[i, 1] = floor_y
                if vel[i, 1] > 0:
                    vel[i, 1] *= -0.4
                vel[i, 0] *= 0.78
                vel[i, 2] *= 0.78
            if pos[i, 0] < -400:
                pos[i, 0] = -400
                if vel[i, 0] < 0:
                    vel[i, 0] *= -0.5
            if pos[i, 0] > 400:
                pos[i, 0] = 400
                if vel[i, 0] > 0:
                    vel[i, 0] *= -0.5

    return pos, vel
