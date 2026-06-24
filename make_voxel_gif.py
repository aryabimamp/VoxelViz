import os
import glob
import imageio.v2 as imageio

# ===========================================
# 1. User Parameters (edit these paths as needed)
# ===========================================
# Folder where your slice PNGs are saved (e.g., from your slicing routine)
slice_folder = "C:/Users/ARYA BIMA/Downloads/voxel_drop_frames"

# Output paths for the assembled animations
output_gif = "C:/Users/ARYA BIMA/Downloads/voxel_animation.gif"
output_mp4 = "C:/Users/ARYA BIMA/Downloads/voxel_animation.mp4"

# Frame rate settings
gif_frame_duration = 0.1  # seconds per frame in GIF (e.g., 0.1 = 10 FPS)
mp4_fps = 10              # frames per second for MP4

# ===========================================
# 2. Gather & Sort Slice Filenames
# ===========================================
# Assumes your PNGs are named like: slice_0000.png, slice_0001.png, …
pattern = os.path.join(slice_folder, "slice_*.png")
slice_files = sorted(glob.glob(pattern))
if not slice_files:
    raise RuntimeError(f"No slice PNGs found in folder:\n  {slice_folder}")

print(f"Found {len(slice_files)} slice images. Beginning assembly...")

# ===========================================
# 3. Assemble into an Animated GIF
# ===========================================
print("Assembling frames into a GIF...")
gif_frames = []
for filename in slice_files:
    image = imageio.imread(filename)
    gif_frames.append(image)

# Save as looping GIF
imageio.mimsave(output_gif, gif_frames, duration=gif_frame_duration)
print(f"  GIF saved to: {output_gif}")

# ===========================================
# 4. Assemble into an MP4 (using FFmpeg plugin)
# ===========================================
print("Assembling frames into an MP4...")
writer = imageio.get_writer(
    output_mp4,
    format='FFMPEG',   # force the FFmpeg backend
    mode='I',          # writing individual frames
    fps=mp4_fps,
    codec='libx264',   # H.264 for MP4
    quality=8          # optional: 0 = low, 10 = lossless
)

for filename in slice_files:
    image = imageio.imread(filename)
    writer.append_data(image)

writer.close()
print(f"  MP4 saved to: {output_mp4}")

print("All animations generated successfully.")
