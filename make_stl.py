import numpy as np
import struct

L, W, H, R, WALL = 140.0, 60.0, 40.0, 6.0, 2.4
nx, np_pts = 30, 32
vertices, triangles = [], []

def add_vertex(pt):
    vertices.append(pt)
    return len(vertices) - 1

def add_tri(i1, i2, i3):
    triangles.append((i1, i2, i3))

def add_quad(i1, i2, i3, i4):
    add_tri(i1, i2, i3)
    add_tri(i1, i3, i4)

cy, cz = (W/2.0 - R), (H/2.0 - R)
angles = np.linspace(0, 2*np.pi, np_pts, endpoint=False)
prof = []
for a in angles:
    sy = 1.0 if np.cos(a) >= 0 else -1.0
    sz = 1.0 if np.sin(a) >= 0 else -1.0
    prof.append([sy*cy + R*np.cos(a), sz*cz + R*np.sin(a)])
prof = np.array(prof)

xs = np.linspace(0, L, nx)
grid = []
for ix, x in enumerate(xs):
    s = 1.0
    if x < R: s = np.sqrt(max(0.01, 1.0 - ((R - x)/R)**2))
    elif x > (L - R): s = np.sqrt(max(0.01, 1.0 - ((x - (L - R))/R)**2))
    ring = [add_vertex([float(x), float(prof[ip, 0]), float(H/2.0 + prof[ip, 1]*s)]) for ip in range(np_pts)]
    grid.append(ring)

for ix in range(nx - 1):
    for ip in range(np_pts):
        ip_n = (ip + 1) % np_pts
        add_quad(grid[ix][ip], grid[ix+1][ip], grid[ix+1][ip_n], grid[ix][ip_n])

v_rear = add_vertex([0.0, 0.0, H/2.0])
v_front = add_vertex([L, 0.0, H/2.0])
for ip in range(np_pts):
    ip_n = (ip + 1) % np_pts
    add_tri(v_rear, grid[0][ip_n], grid[0][ip])
    add_tri(v_front, grid[-1][ip], grid[-1][ip_n])

# פיית יציאה
spout_z, r_out, r_in, spout_len, n_c = 15.4, 7.5, 5.75, 16.0, 24
tc = np.linspace(0, 2*np.pi, n_c, endpoint=False)
cos_c, sin_c = np.cos(tc), np.sin(tc)

sp_rings = []
for s in range(5):
    x_c = L + (s / 4.0) * spout_len
    r_c = r_out + (0.75 if (0 < s < 4 and s % 2 == 1) else 0.0)
    sp_rings.append([add_vertex([float(x_c), float(r_c * cos_c[i]), float(spout_z + r_c * sin_c[i])]) for i in range(n_c)])

for s in range(4):
    for i in range(n_c):
        i_n = (i + 1) % n_c
        add_quad(sp_rings[s][i], sp_rings[s+1][i], sp_rings[s+1][i_n], sp_rings[s][i_n])

lip_ring = [add_vertex([L + spout_len, float(r_in * cos_c[i]), float(spout_z + r_in * sin_c[i])]) for i in range(n_c)]
bore_ring = [add_vertex([L - WALL, float(r_in * cos_c[i]), float(spout_z + r_in * sin_c[i])]) for i in range(n_c)]
for i in range(n_c):
    i_n = (i + 1) % n_c
    add_quad(sp_rings[-1][i], lip_ring[i], lip_ring[i_n], sp_rings[-1][i_n])
    add_quad(lip_ring[i], bore_ring[i], bore_ring[i_n], lip_ring[i_n])
v_bore_end = add_vertex([L - WALL, 0.0, spout_z])
for i in range(n_c):
    i_n = (i + 1) % n_c
    add_tri(v_bore_end, bore_ring[i_n], bore_ring[i])

# שקע עליון
top_x, top_z, rec_r, rec_d = 105.0, 40.0, 15.0, 3.5
rim_ring = [add_vertex([float(top_x + rec_r*cos_c[i]), float(rec_r*sin_c[i]), float(top_z)]) for i in range(n_c)]
floor_ring = [add_vertex([float(top_x + rec_r*cos_c[i]), float(rec_r*sin_c[i]), float(top_z - rec_d)]) for i in range(n_c)]
for i in range(n_c):
    i_n = (i + 1) % n_c
    add_quad(rim_ring[i], floor_ring[i], floor_ring[i_n], rim_ring[i_n])
v_floor = add_vertex([top_x, 0.0, top_z - rec_d])
for i in range(n_c):
    i_n = (i + 1) % n_c
    add_tri(v_floor, floor_ring[i], floor_ring[i_n])

# פין אחורי
rr, rlen = 6.0, 4.0
r_base = [add_vertex([0.0, float(rr*cos_c[i]), float(spout_z + rr*sin_c[i])]) for i in range(n_c)]
r_tip = [add_vertex([-rlen, float(rr*cos_c[i]), float(spout_z + rr*sin_c[i])]) for i in range(n_c)]
for i in range(n_c):
    i_n = (i + 1) % n_c
    add_quad(r_base[i], r_tip[i], r_tip[i_n], r_base[i_n])
v_rtip = add_vertex([-rlen, 0.0, spout_z])
for i in range(n_c):
    i_n = (i + 1) % n_c
    add_tri(v_rtip, r_tip[i_n], r_tip[i])

verts = np.array(vertices, dtype=np.float32)
tris = np.array(triangles, dtype=np.int32)
coords = verts[tris]
v0, v1, v2 = coords[:, 0], coords[:, 1], coords[:, 2]
normals = np.cross(v1 - v0, v2 - v0)
norm = np.linalg.norm(normals, axis=1, keepdims=True)
norm[norm == 0] = 1.0
normals = normals / norm

with open("dispenser_tank_a1_mini.stl", "wb") as f:
    f.write(b"Bambu Lab A1 Mini Dispenser STL".ljust(80, b" "))
    f.write(struct.pack("<I", len(triangles)))
    for i in range(len(triangles)):
        f.write(struct.pack("<3f3f3f3fH",
                            normals[i, 0], normals[i, 1], normals[i, 2],
                            coords[i, 0, 0], coords[i, 0, 1], coords[i, 0, 2],
                            coords[i, 1, 0], coords[i, 1, 1], coords[i, 1, 2],
                            coords[i, 2, 0], coords[i, 2, 1], coords[i, 2, 2],
                            0))
print("קובץ dispenser_tank_a1_mini.stl נוצר בהצלחה!")
