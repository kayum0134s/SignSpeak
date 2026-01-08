"""
Video to Image Converter
Extracts a thumbnail image from each video file for use in Gallery mode
"""

import cv2
import os
from pathlib import Path

# Paths
EXTRACTED_PATH = Path("media/extracted")
ASL_PHRASES_PATH = Path("media/signs/asl/phrases")
ISL_PHRASES_PATH = Path("media/signs/isl/phrases")

# Create directories
ASL_PHRASES_PATH.mkdir(parents=True, exist_ok=True)
ISL_PHRASES_PATH.mkdir(parents=True, exist_ok=True)

def extract_thumbnail(video_path, output_path, frame_number=10):
    """
    Extract a frame from a video as a thumbnail image
    
    Args:
        video_path: Path to the video file
        output_path: Path where to save the thumbnail image
        frame_number: Which frame to extract (default: 10)
    """
    try:
        # Open the video
        cap = cv2.VideoCapture(str(video_path))
        
        # Set the frame position
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        
        # Read the frame
        ret, frame = cap.read()
        
        if ret:
            # Save the frame as an image
            cv2.imwrite(str(output_path), frame)
            print(f"✅ Created thumbnail: {output_path.name}")
            return True
        else:
            print(f"❌ Failed to read frame from: {video_path.name}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {video_path.name}: {e}")
        return False
    finally:
        cap.release()

def convert_all_videos():
    """Convert all videos in the extracted folder to thumbnail images"""
    
    if not EXTRACTED_PATH.exists():
        print(f"❌ Extracted folder not found: {EXTRACTED_PATH}")
        return
    
    video_files = list(EXTRACTED_PATH.glob("*.mp4")) + list(EXTRACTED_PATH.glob("*.MP4"))
    
    if not video_files:
        print("❌ No video files found in extracted folder")
        return
    
    print(f"\n🎬 Found {len(video_files)} video files")
    print("📸 Extracting thumbnails...\n")
    
    success_count = 0
    
    for video_file in video_files:
        # Create image filename (replace .mp4 with .jpg)
        image_name = video_file.stem + ".jpg"
        
        # Save to ASL phrases folder
        asl_output = ASL_PHRASES_PATH / image_name
        
        if extract_thumbnail(video_file, asl_output):
            success_count += 1
        
        # Optionally create ISL version (copy the same thumbnail)
        # isl_output = ISL_PHRASES_PATH / image_name
        # if asl_output.exists():
        #     shutil.copy2(asl_output, isl_output)
    
    print(f"\n✅ Successfully created {success_count}/{len(video_files)} thumbnails")
    print(f"📁 Saved to: {ASL_PHRASES_PATH}")

def main():
    print("=" * 60)
    print("   Video to Image Thumbnail Converter")
    print("=" * 60)
    
    # Check if OpenCV is installed
    try:
        import cv2
        print("✅ OpenCV is installed")
    except ImportError:
        print("❌ OpenCV not installed!")
        print("\nPlease install it with:")
        print("   pip install opencv-python")
        return
    
    convert_all_videos()
    
    print("\n" + "=" * 60)
    print("💡 TIP: You can now use these images in Gallery mode!")
    print("=" * 60)

if __name__ == "__main__":
    main()
