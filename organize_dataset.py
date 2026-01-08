"""
ASL Dataset Organizer
This script helps you organize and import ASL dataset images into the project structure.
"""

import os
import shutil
from pathlib import Path
import json

# Configuration
PROJECT_ROOT = Path(__file__).parent
DATASET_SOURCE = PROJECT_ROOT / "temp_dataset"  # Place your extracted dataset here
MEDIA_ROOT = PROJECT_ROOT / "media" / "signs" / "asl"
SIGN_MAPPING_FILE = PROJECT_ROOT / "data" / "sign-mapping.json"

# Create necessary directories
ALPHABET_DIR = MEDIA_ROOT / "alphabet"
COMMON_DIR = MEDIA_ROOT / "common"
PHRASES_DIR = MEDIA_ROOT / "phrases"

def create_directories():
    """Create the necessary directory structure"""
    ALPHABET_DIR.mkdir(parents=True, exist_ok=True)
    COMMON_DIR.mkdir(parents=True, exist_ok=True)
    PHRASES_DIR.mkdir(parents=True, exist_ok=True)
    DATASET_SOURCE.mkdir(parents=True, exist_ok=True)
    print(f"✅ Created directory structure")

def organize_alphabet_images():
    """
    Organize alphabet images (A-Z)
    Assumes your dataset has folders like: A/, B/, C/, etc.
    """
    print("\n📝 Organizing alphabet images...")
    
    if not DATASET_SOURCE.exists():
        print(f"⚠️  Please place your ASL dataset in: {DATASET_SOURCE}")
        return
    
    letters = 'abcdefghijklmnopqrstuvwxyz'
    organized_count = 0
    
    # Search for alphabet folders in the dataset
    for letter in letters:
        # Try different naming conventions
        possible_folders = [
            DATASET_SOURCE / letter.upper(),
            DATASET_SOURCE / letter.lower(),
            DATASET_SOURCE / f"{letter.upper()}",
            DATASET_SOURCE / "train" / letter.upper(),
            DATASET_SOURCE / "Train" / letter.upper(),
        ]
        
        for folder in possible_folders:
            if folder.exists() and folder.is_dir():
                # Find the first image in this folder
                images = list(folder.glob("*.jpg")) + list(folder.glob("*.png")) + list(folder.glob("*.jpeg"))
                
                if images:
                    # Copy the first image (or you can choose the best one)
                    source_image = images[0]
                    dest_image = ALPHABET_DIR / f"{letter.lower()}.{source_image.suffix.lstrip('.')}"
                    
                    shutil.copy2(source_image, dest_image)
                    print(f"   ✓ Copied {letter.upper()}: {source_image.name} -> {dest_image.name}")
                    organized_count += 1
                    break
    
    print(f"\n✅ Organized {organized_count} alphabet images")

def organize_common_words():
    """
    Organize common word images
    You can customize this based on your dataset structure
    """
    print("\n📝 Organizing common word images...")
    
    # Common words mapping (customize based on your dataset)
    common_words = {
        'hello': ['hello', 'hi', 'greetings'],
        'goodbye': ['goodbye', 'bye', 'farewell'],
        'please': ['please'],
        'thank_you': ['thank', 'thanks', 'thank_you', 'thankyou'],
        'yes': ['yes'],
        'no': ['no'],
        'sorry': ['sorry'],
        'help': ['help'],
        'love': ['love'],
    }
    
    organized_count = 0
    
    for word, variations in common_words.items():
        for variation in variations:
            # Try to find the word folder
            possible_paths = [
                DATASET_SOURCE / variation,
                DATASET_SOURCE / variation.upper(),
                DATASET_SOURCE / variation.capitalize(),
            ]
            
            for path in possible_paths:
                if path.exists() and path.is_dir():
                    images = list(path.glob("*.jpg")) + list(path.glob("*.png"))
                    
                    if images:
                        dest_image = COMMON_DIR / f"{word}.{images[0].suffix.lstrip('.')}"
                        shutil.copy2(images[0], dest_image)
                        print(f"   ✓ Copied {word}: {images[0].name}")
                        organized_count += 1
                        break
    
    print(f"\n✅ Organized {organized_count} common word images")

def update_sign_mapping():
    """
    Update sign-mapping.json with actual image paths
    Changes 'generated: true' to 'generated: false' for real images
    """
    print("\n📝 Updating sign-mapping.json...")
    
    try:
        with open(SIGN_MAPPING_FILE, 'r') as f:
            mapping = json.load(f)
        
        if 'asl' not in mapping:
            mapping['asl'] = {}
        
        updated_count = 0
        
        # Update alphabet mappings
        for letter in 'abcdefghijklmnopqrstuvwxyz':
            for ext in ['.png', '.jpg', '.jpeg']:
                image_path = ALPHABET_DIR / f"{letter}{ext}"
                if image_path.exists():
                    mapping['asl'][letter] = {
                        "type": "image",
                        "path": f"media/signs/asl/alphabet/{letter}{ext}",
                        "generated": False
                    }
                    updated_count += 1
                    break
        
        # Update common words
        for word_file in COMMON_DIR.glob("*"):
            if word_file.suffix in ['.png', '.jpg', '.jpeg']:
                word = word_file.stem
                mapping['asl'][word] = {
                    "type": "image",
                    "path": f"media/signs/asl/common/{word_file.name}",
                    "generated": False
                }
                updated_count += 1
        
        # Save updated mapping
        with open(SIGN_MAPPING_FILE, 'w') as f:
            json.dump(mapping, f, indent=2)
        
        print(f"✅ Updated {updated_count} entries in sign-mapping.json")
        
    except Exception as e:
        print(f"❌ Error updating sign-mapping.json: {e}")

def scan_dataset_structure():
    """
    Scan and display the structure of your dataset
    Helps you understand how to organize it
    """
    print("\n🔍 Scanning dataset structure...")
    
    if not DATASET_SOURCE.exists():
        print(f"⚠️  Dataset folder not found: {DATASET_SOURCE}")
        print(f"   Please create this folder and place your ASL dataset inside it.")
        return
    
    print(f"\nDataset location: {DATASET_SOURCE}")
    print("\nFound directories:")
    
    dirs = [d for d in DATASET_SOURCE.iterdir() if d.is_dir()]
    
    if not dirs:
        print("   (No directories found)")
    else:
        for d in sorted(dirs)[:20]:  # Show first 20 directories
            file_count = len(list(d.glob("*")))
            print(f"   📁 {d.name} ({file_count} files)")
        
        if len(dirs) > 20:
            print(f"   ... and {len(dirs) - 20} more directories")

def main():
    """Main function"""
    print("=" * 60)
    print("   ASL Dataset Organizer")
    print("=" * 60)
    
    # Create directory structure
    create_directories()
    
    # Scan dataset
    scan_dataset_structure()
    
    # Ask user if they want to proceed
    print("\n" + "=" * 60)
    print("INSTRUCTIONS:")
    print("1. Extract your ASL dataset")
    print(f"2. Place it in: {DATASET_SOURCE}")
    print("3. Run this script again")
    print("=" * 60)
    
    if DATASET_SOURCE.exists() and any(DATASET_SOURCE.iterdir()):
        proceed = input("\n📌 Dataset found! Proceed with organization? (y/n): ")
        
        if proceed.lower() == 'y':
            organize_alphabet_images()
            organize_common_words()
            update_sign_mapping()
            print("\n" + "=" * 60)
            print("✅ Dataset organization complete!")
            print("=" * 60)
        else:
            print("\n❌ Organization cancelled.")
    else:
        print(f"\n⚠️  Please place your dataset in: {DATASET_SOURCE}")

if __name__ == "__main__":
    main()
