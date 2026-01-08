"""
Kaggle ASL Dataset Setup Script
Automatically extracts and organizes Kaggle ASL Alphabet dataset
"""

import zipfile
import shutil
import json
from pathlib import Path
from collections import defaultdict

# Configuration
PROJECT_ROOT = Path(__file__).parent
DATASET_ZIP_NAME = "asl_alphabet.zip"  # or "archive.zip" - Kaggle's default name
DATASET_ZIP_PATH = PROJECT_ROOT / DATASET_ZIP_NAME
TEMP_EXTRACT = PROJECT_ROOT / "temp_kaggle_extract"
ASL_ALPHABET_DIR = PROJECT_ROOT / "media" / "signs" / "asl" / "alphabet"
ASL_NUMBERS_DIR = PROJECT_ROOT / "media" / "signs" / "asl" / "numbers"
ASL_COMMON_DIR = PROJECT_ROOT / "media" / "signs" / "asl" / "common"
SIGN_MAPPING_FILE = PROJECT_ROOT / "data" / "sign-mapping.json"

def find_dataset_zip():
    """Find the Kaggle dataset ZIP file"""
    # Check common Kaggle download names
    possible_names = [
        "asl_alphabet.zip",
        "asl-alphabet.zip", 
        "archive.zip",
        "asl_alphabet_train.zip",
        "grassknoted-asl-alphabet.zip"
    ]
    
    for name in possible_names:
        zip_path = PROJECT_ROOT / name
        if zip_path.exists():
            print(f"✅ Found dataset: {name}")
            return zip_path
    
    # Check Downloads folder
    downloads = Path.home() / "Downloads"
    for name in possible_names:
        zip_path = downloads / name
        if zip_path.exists():
            print(f"✅ Found dataset in Downloads: {name}")
            # Copy to project directory
            dest = PROJECT_ROOT / name
            shutil.copy2(zip_path, dest)
            return dest
    
    return None

def extract_dataset(zip_path):
    """Extract the Kaggle dataset"""
    print(f"\n📦 Extracting dataset from {zip_path.name}...")
    
    TEMP_EXTRACT.mkdir(parents=True, exist_ok=True)
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(TEMP_EXTRACT)
        
        print("✅ Dataset extracted successfully")
        return True
    except Exception as e:
        print(f"❌ Error extracting: {e}")
        return False

def find_letter_folders():
    """Find all letter folders in extracted data"""
    letter_folders = {}
    
    # Search for folders named A, B, C, etc.
    for path in TEMP_EXTRACT.rglob("*"):
        if path.is_dir():
            folder_name = path.name.upper()
            # Check if it's a single letter or known special folder
            if (len(folder_name) == 1 and folder_name.isalpha()) or \
               folder_name in ['SPACE', 'DELETE', 'NOTHING']:
                letter_folders[folder_name.lower()] = path
    
    return letter_folders

def select_best_images(folder_path, count=3):
    """
    Select the best representative images from a folder
    Returns list of image paths
    """
    # Get all images
    images = []
    for ext in ['*.jpg', '*.jpeg', '*.png']:
        images.extend(list(folder_path.glob(ext)))
    
    if not images:
        return []
    
    # If there are many images, select evenly distributed ones
    if len(images) > count:
        step = len(images) // count
        selected = [images[i * step] for i in range(count)]
    else:
        selected = images[:count]
    
    return selected

def organize_alphabet_images():
    """Organize alphabet images from Kaggle dataset"""
    print("\n📝 Organizing alphabet images...")
    
    ASL_ALPHABET_DIR.mkdir(parents=True, exist_ok=True)
    
    letter_folders = find_letter_folders()
    
    if not letter_folders:
        print("❌ No letter folders found in extracted data")
        return 0
    
    print(f"✅ Found {len(letter_folders)} letter/sign folders")
    
    organized_count = 0
    letters = 'abcdefghijklmnopqrstuvwxyz'
    
    for letter in letters:
        if letter in letter_folders:
            folder = letter_folders[letter]
            
            # Get the best image
            images = select_best_images(folder, count=1)
            
            if images:
                source_image = images[0]
                # Preserve original extension
                ext = source_image.suffix
                dest_image = ASL_ALPHABET_DIR / f"{letter}{ext}"
                
                # Copy the image
                shutil.copy2(source_image, dest_image)
                print(f"   ✓ {letter.upper()}: {source_image.name} → {dest_image.name}")
                organized_count += 1
    
    # Handle special signs if available
    special_signs = {
        'space': 'space',
        'delete': 'delete',
        'nothing': 'nothing'
    }
    
    for key, folder_name in special_signs.items():
        if folder_name in letter_folders:
            folder = letter_folders[folder_name]
            images = select_best_images(folder, count=1)
            
            if images:
                source_image = images[0]
                ext = source_image.suffix
                dest_image = ASL_COMMON_DIR / f"{key}{ext}"
                ASL_COMMON_DIR.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_image, dest_image)
                print(f"   ✓ {key.upper()}: {source_image.name} → {dest_image.name}")
    
    print(f"\n✅ Organized {organized_count} alphabet images")
    return organized_count

def update_sign_mapping_with_images():
    """Update sign-mapping.json with actual image paths"""
    print("\n📝 Updating sign-mapping.json...")
    
    try:
        # Load existing mapping
        with open(SIGN_MAPPING_FILE, 'r', encoding='utf-8') as f:
            mapping = json.load(f)
        
        if 'asl' not in mapping:
            mapping['asl'] = {}
        
        updated_count = 0
        
        # Update alphabet letters with actual images
        for letter in 'abcdefghijklmnopqrstuvwxyz':
            # Check which extension exists
            for ext in ['.jpg', '.jpeg', '.png']:
                image_path = ASL_ALPHABET_DIR / f"{letter}{ext}"
                if image_path.exists():
                    mapping['asl'][letter] = {
                        "type": "image",
                        "path": f"media/signs/asl/alphabet/{letter}{ext}",
                        "generated": False
                    }
                    updated_count += 1
                    break
        
        # Save updated mapping
        with open(SIGN_MAPPING_FILE, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Updated {updated_count} entries in sign-mapping.json")
        
    except Exception as e:
        print(f"❌ Error updating sign-mapping.json: {e}")

def cleanup():
    """Clean up temporary extraction folder"""
    print("\n🧹 Cleaning up temporary files...")
    
    try:
        if TEMP_EXTRACT.exists():
            shutil.rmtree(TEMP_EXTRACT)
            print("✅ Cleanup complete")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")

def main():
    print("=" * 70)
    print("   Kaggle ASL Alphabet Dataset Setup")
    print("=" * 70)
    
    # Find the dataset ZIP
    zip_path = find_dataset_zip()
    
    if not zip_path:
        print("\n❌ Dataset ZIP file not found!")
        print("\n📋 INSTRUCTIONS:")
        print("1. Download ASL Alphabet dataset from Kaggle:")
        print("   https://www.kaggle.com/datasets/grassknoted/asl-alphabet")
        print("2. Place the downloaded ZIP file in this folder:")
        print(f"   {PROJECT_ROOT}")
        print("3. Run this script again")
        print("\n💡 Accepted ZIP names: asl_alphabet.zip, archive.zip, etc.")
        print("=" * 70)
        return
    
    # Extract dataset
    if not extract_dataset(zip_path):
        return
    
    # Organize images
    count = organize_alphabet_images()
    
    if count > 0:
        # Update mapping
        update_sign_mapping_with_images()
        
        # Cleanup
        cleanup()
        
        print("\n" + "=" * 70)
        print("✅ SETUP COMPLETE!")
        print(f"\n📊 Summary:")
        print(f"   - Organized {count} alphabet images")
        print(f"   - Images saved to: {ASL_ALPHABET_DIR}")
        print(f"   - Updated sign-mapping.json")
        print("\n💡 Your app is now ready to display ASL alphabet images!")
        print("   - Refresh your browser")
        print("   - Type any text and translate")
        print("   - Switch to Gallery mode to see images!")
        print("=" * 70)
    else:
        print("\n❌ No images were organized. Please check the dataset structure.")
        cleanup()

if __name__ == "__main__":
    main()
