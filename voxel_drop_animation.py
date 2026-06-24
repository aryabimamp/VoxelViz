import os
import numpy as np
import trimesh
import imageio.v2 as imageio
import matplotlib.cm as cm

# --- params ---
mesh_path = "C:/Users/ARYA BIMA/Downloads/bunny.obj"
voxel_size = 0.02    # large = less voxels
method = "trimesh"

output_frames_folder = "C:/Users/ARYA BIMA/Downloads/voxel_3d_frames"
os.makedirs(output_frames_folder, exist_ok=True)

output_gif = "C:/Users/ARYA BIMA/Downloads/voxel_3d_animation.gif"
output_mp4 = "C:/Users/ARYA BIMA/Downloads/voxel_3d_animation.mp4"

drop_frames_per_block = 2   
gif_frame_duration = 0.05   
mp4_fps = 10

render_resolution = (600, 600)

# --- load and voxelize ---
print("Loading mesh from:", mesh_path)
mesh = trimesh.load(mesh_path)
if isinstance(mesh, trimesh.Scene):
    mesh = trimesh.util.concatenate(list(mesh.geometry.values()))
print(f"Mesh has {len(mesh.vertices)} vertices, {len(mesh.faces)} faces.")

if not mesh.is_watertight:
    print("WARNING: Mesh not watertight—using convex hull.")
    mesh = mesh.convex_hull

# aabb computation
min_bound, max_bound = mesh.bounds
extent = max_bound - min_bound

# grid size
nx = int(np.ceil(extent[0] / voxel_size))   
ny = int(np.ceil(extent[1] / voxel_size))
nz = int(np.ceil(extent[2] / voxel_size))
print(f"Voxel grid dimensions: {nx} × {ny} × {nz}")

# voxelization using trimesh
if method == "trimesh":
    vg = mesh.voxelized(pitch=voxel_size)
    inside_mask = vg.matrix.copy()  
    nx, ny, nz = inside_mask.shape
    origin = vg.transform[:3, 3]
    xs = origin[0] + (np.arange(nx) + 0.5) * voxel_size
    ys = origin[1] + (np.arange(ny) + 0.5) * voxel_size
    zs = origin[2] + (np.arange(nz) + 0.5) * voxel_size
    print(f"Trimesh voxel grid: {nx} × {ny} × {nz}")
else:
    raise ValueError("Only 'trimesh' method is supported in this version.")

# --- color the cubes ---
base_box = trimesh.creation.box(extents=(voxel_size, voxel_size, voxel_size))
face_count = base_box.faces.shape[0]
colormap = cm.get_cmap("plasma", nz)

# build and sort the list of blocks
filled_voxels = [
    (ix, iy, iz)
    for ix in range(nx)
    for iy in range(ny)
    for iz in range(nz)
    if inside_mask[ix, iy, iz]
]
# sort by iz ascending so it drops bottom to top
filled_voxels.sort(key=lambda v: v[2])

# calcu for drop height start
max_final_z = zs.max()
drop_start_z = max_final_z + voxel_size * 2  

# --- render falling drop ---
print("render 3D frames single drop animation...")
frame_paths = []
frame_index = 0

# camera setup
def look_at(cam_pos, target):
    forward = (target - cam_pos)
    forward /= np.linalg.norm(forward)
    up = np.array([0, 0, 1], dtype=np.float64)
    right = np.cross(up, forward)
    right /= np.linalg.norm(right)
    true_up = np.cross(forward, right)
    mat = np.eye(4, dtype=np.float64)
    mat[0, :3] = right
    mat[1, :3] = true_up
    mat[2, :3] = -forward
    mat[:3, 3] = cam_pos
    return mat

center = (min_bound + max_bound) / 2
cam_distance = max(extent)
camera_position = center + np.array([cam_distance, cam_distance * 1.5, cam_distance * 5.0])
camera_transform = look_at(camera_position, center)

for idx, (ix, iy, iz) in enumerate(filled_voxels):
    final_z = zs[iz]
    # drop animation
    for subframe in range(drop_frames_per_block):
        t = subframe / (drop_frames_per_block - 1)  # 0 → 1
        interp_z = drop_start_z * (1 - t) + final_z * t

        scene = trimesh.Scene()
        scene.background = [255, 255, 255, 255]

        # 1) Add all previously landed voxels at their final positions
        for j in range(idx):
            pax, pay, paz = filled_voxels[j]
            x = xs[pax]; y = ys[pay]; z = zs[paz]
            cube = base_box.copy()
            cube.apply_translation((x, y, z))
            rgba_float = colormap(paz)
            layer_color = [
                int(rgba_float[0] * 255),
                int(rgba_float[1] * 255),
                int(rgba_float[2] * 255),
                int(rgba_float[3] * 255),
            ]
            cube.visual.face_colors = np.tile(layer_color, (face_count, 1))
            scene.add_geometry(cube)

        # 2) Add the currently dropping voxel at interpolated Z
        cx = xs[ix]; cy = ys[iy]
        cube = base_box.copy()
        cube.apply_translation((cx, cy, interp_z))
        rgba_float = colormap(iz)
        layer_color = [
            int(rgba_float[0] * 255),
            int(rgba_float[1] * 255),
            int(rgba_float[2] * 255),
            int(rgba_float[3] * 255),
        ]
        cube.visual.face_colors = np.tile(layer_color, (face_count, 1))
        scene.add_geometry(cube)

        # 3) Set camera and fov
        scene.camera_transform = camera_transform
        scene.camera.fov = (50.0, 50.0)

        # rndr
        png = scene.save_image(resolution=render_resolution, visible=True)
        frame_path = os.path.join(output_frames_folder, f"frame_{frame_index:04d}.png")
        with open(frame_path, "wb") as f:
            f.write(png)
        frame_paths.append(frame_path)

        print(f"  Saved block‐drop frame {frame_index:04d} (voxel {idx}, subframe {subframe})")
        frame_index += 1


print("All falling‐block frames rendered.")

# --- gif ---
print("Assembling frames into a GIF...")
gif_frames = []
for fp in frame_paths:
    img = imageio.imread(fp)
    gif_frames.append(img)
imageio.mimsave(output_gif, gif_frames, duration=gif_frame_duration)
print(f"  GIF saved to: {output_gif}")

# --- mp4 ---
print("Assembling frames into an MP4...")
writer = imageio.get_writer(
    output_mp4,
    format="FFMPEG",
    mode="I",
    fps=mp4_fps,
    codec="libx264",
    quality=8,
)
for fp in frame_paths:
    img = imageio.imread(fp)
    writer.append_data(img)
writer.close()
print(f"  MP4 saved to: {output_mp4}")

print("3D single‐block drop animation complete.")
