import os
from moviepy import VideoFileClip, CompositeVideoClip

# --- CONFIGURATION ---
INPUT_FOLDER = "Emotions/robotic_voices"
OUTPUT_FOLDER = "Emotions/robotic_voices/output_videos"
TARGET_WIDTH = 1920
TARGET_HEIGHT = 1080


# ---------------------

def crop_and_pad(input_path, output_path):
    clip = None
    final_clip = None
    try:
        # 1. Load the video clip
        clip = VideoFileClip(input_path)

        # 2. Crop to Square (1:1)
        # Find shortest side
        min_dim = min(clip.w, clip.h)

        # Crop to center square
        square_clip = clip.cropped(
            width=min_dim,
            height=min_dim,
            x_center=clip.w / 2,
            y_center=clip.h / 2
        )

        # 3. Resize the square to fit the height of the target (1080px)
        # In MoviePy v2, we use .resized() instead of .resize()
        square_resized = square_clip.resized(height=TARGET_HEIGHT, width=TARGET_HEIGHT)

        # 4. Center the square inside a 1920x1080 frame
        # We use CompositeVideoClip to place the square on a canvas
        # .with_position("center") handles the centering logic
        final_clip = CompositeVideoClip(
            [square_resized.with_position("center")],
            size=(TARGET_WIDTH, TARGET_HEIGHT)
        )

        # 5. Write the result
        final_clip.write_videofile(
            output_path,
            fps=clip.fps if clip.fps else 30,  # Keep original FPS or default to 30
            codec="libx264",
            audio_codec="aac"
        )

    except Exception as e:
        print(f"Error processing {input_path}: {e}")

    finally:
        # clean up resources
        if clip: clip.close()
        if final_clip: final_clip.close()


def main():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    for filename in os.listdir(INPUT_FOLDER):
        if filename.lower().endswith(".mp4"):
            input_path = os.path.join(INPUT_FOLDER, filename)
            output_path = os.path.join(OUTPUT_FOLDER, f"1920_square_{filename}")

            print(f"Processing: {filename}...")
            crop_and_pad(input_path, output_path)

    print("Batch processing complete!")


if __name__ == "__main__":
    main()