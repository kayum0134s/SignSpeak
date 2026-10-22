"""
Simple Image Organizer
Moves extracted videos and organizes them properly
Updates sign-mapping.json to support both image and video modes
"""

import json
import shutil
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent if Path(__file__).resolve().parent.name == "scripts" else Path(__file__).resolve().parent
EXTRACTED_PATH = PROJECT_ROOT / "media" / "extracted"
if not EXTRACTED_PATH.exists():
    EXTRACTED_PATH = PROJECT_ROOT / "frontend" / "public" / "media" / "extracted"
ASL_PHRASES_PATH = PROJECT_ROOT / "frontend" / "public" / "media" / "signs" / "asl" / "phrases"
SIGN_MAPPING_FILE = PROJECT_ROOT / "data" / "sign-mapping.json"

def move_videos_to_phrases():
    """Move video files from extracted folder to asl/phrases folder"""
    
    ASL_PHRASES_PATH.mkdir(parents=True, exist_ok=True)
    
    if not EXTRACTED_PATH.exists():
        print(f"❌ Extracted folder not found")
        return
    
    video_files = list(EXTRACTED_PATH.glob("*.mp4")) + list(EXTRACTED_PATH.glob("*.MP4"))
    
    if not video_files:
        print("❌ No video files found")
        return
    
    print(f"\n📹 Moving {len(video_files)} video files...\n")
    
    for video_file in video_files:
        dest_file = ASL_PHRASES_PATH / video_file.name
        
        # Copy instead of move to keep original
        shutil.copy2(video_file, dest_file)
        print(f"✅ Copied: {video_file.name}")
    
    print(f"\n✅ All videos copied to: {ASL_PHRASES_PATH}")

def update_sign_mapping_for_dual_mode():
    """
    Update sign-mapping.json to include both image and video paths
    This allows switching between Gallery and Video modes
    """
    
    print("\n📝 Updating sign-mapping.json...")
    
    try:
        with open(SIGN_MAPPING_FILE, 'r', encoding='utf-8') as f:
            mapping = json.load(f)
        
        # Phrases that have videos
        phrase_videos = {
            "good morning": "Good morning.mp4",
            "good evening": "Good Evening.mp4",
            "how are you": "How are you.mp4",
            "what is your name": "what is your name.mp4",
            "what are you doing": "What are you doing.mp4",
            "have a good day": "Have a good day.mp4",
            "monday": "Monday.mp4",
            "tuesday": "Tuesday.mp4",
            "wednesday": "Wednesday.mp4",
            "thursday": "Thursday.mp4",
            "friday": "Friday.mp4",
            "saturday": "Saturday.mp4",
            "sunday": "Sunday.mp4"
        }
        
        # Update ASL mapping with video paths
        if 'asl' in mapping:
            for phrase, video_file in phrase_videos.items():
                mapping['asl'][phrase] = {
                    "type": "video",
                    "path": f"media/signs/asl/phrases/{video_file}",
                    "generated": False
                }
        
        # Save updated mapping
        with open(SIGN_MAPPING_FILE, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Updated {len(phrase_videos)} phrases in sign-mapping.json")
        
    except Exception as e:
        print(f"❌ Error updating mapping: {e}")

def main():
    print("=" * 60)
    print("   Sign Language Dataset Organizer")
    print("=" * 60)
    
    # Move videos
    move_videos_to_phrases()
    
    # Update mapping
    update_sign_mapping_for_dual_mode()
    
    print("\n" + "=" * 60)
    print("✅ Organization Complete!")
    print("\n💡 Your videos are now organized and ready to use!")
    print("   - Video mode: Shows MP4 videos")
    print("   - Gallery mode: Will show images (if available)")
    print("=" * 60)

if __name__ == "__main__":
    main()
