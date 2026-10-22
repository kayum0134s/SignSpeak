"""
ASL.zip Dataset Extractor and Organizer
Extracts your ASL.zip and organizes images for Gallery mode
"""

import zipfile
import shutil
import json
from pathlib import Path
import os

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent if Path(__file__).resolve().parent.name == "scripts" else Path(__file__).resolve().parent
TEMP_EXTRACT = PROJECT_ROOT / "temp_asl_extract"
ASL_ALPHABET_DIR = PROJECT_ROOT / "frontend" / "public" / "media" / "signs" / "asl" / "alphabet"
ASL_COMMON_DIR = PROJECT_ROOT / "frontend" / "public" / "media" / "signs" / "asl" / "common"
SIGN_MAPPING_FILE = PROJECT_ROOT / "data" / "sign-mapping.json"

def find_asl_zip():
    """Find ASL.zip in project or parent directories"""
    locations = [
        PROJECT_ROOT / "ASL.zip",
        PROJECT_ROOT.parent / "ASL.zip",
        Path("c:/Users/hp/OneDrive/Desktop/sign project/ASL.zip"),
        Path("c:/Users/hp/Desktop/sign project/ASL.zip"),
        Path("c:/Users/hp/Downloads/ASL.zip"),
    ]
    
    for loc in locations:
        if loc.exists():
            print(f"✅ Found ASL.zip at: {loc}")
            return loc
    
    return None

def extract_asl_zip(zip_path):
    """Extract ASL.zip"""
    print(f"\n📦 Extracting {zip_path.name}...")
    
    try:
        TEMP_EXTRACT.mkdir(parents=True, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(TEMP_EXTRACT)
        
        print("✅ Extraction complete")
        
        # List what was extracted
        print("\n📂 Extracted contents:")
        items = list(TEMP_EXTRACT.iterdir())
        for item in items[:10]:  # Show first 10 items
            print(f"   - {item.name}")
        if len(items) > 10:
            print(f"   ... and {len(items) - 10} more items")
        
        return True
    except Exception as e:
        print(f"❌ Error extracting: {e}")
        return False

def find_and_organize_images():
    """Find image folders and organize them"""
    print("\n🔍 Searching for sign images...")
    
    ASL_ALPHABET_DIR.mkdir(parents=True, exist_ok=True)
    ASL_COMMON_DIR.mkdir(parents=True, exist_ok=True)
    
    organized = 0
    letters = 'abcdefghijklmnopqrstuvwxyz'
    
    # Search for folders/images in extracted data
    for root, dirs, files in os.walk(TEMP_EXTRACT):
        root_path = Path(root)
        
        # Check if this folder represents a letter
        folder_name = root_path.name.lower()
        
        # Handle letter folders (A/ B/ C/ etc.)
        if len(folder_name) == 1 and folder_name in letters:
            # Find first image in this folder
            images = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
            
            if images:
                source = root_path / images[0]
                ext = Path(images[0]).suffix
                dest = ASL_ALPHABET_DIR / f"{folder_name}{ext}"
                
                shutil.copy2(source, dest)
                print(f"   ✓ {folder_name.upper()}: {images[0]} → {dest.name}")
                organized += 1
        
        # Also check for direct image files named like 'a.jpg', 'b.png', etc.
        for file in files:
            name_lower = file.lower()
            if name_lower.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                # Check if filename is a single letter
                name_without_ext = Path(file).stem.lower()
                if len(name_without_ext) == 1 and name_without_ext in letters:
                    source = root_path / file
                    ext = Path(file).suffix
                    dest = ASL_ALPHABET_DIR / f"{name_without_ext}{ext}"
                    
                    if not dest.exists():  # Don't overwrite
                        shutil.copy2(source, dest)
                        print(f"   ✓ {name_without_ext.upper()}: {file} → {dest.name}")
                        organized += 1
    
    return organized

def update_mapping():
    """Update sign-mapping.json"""
    print("\n📝 Updating sign-mapping.json...")
    
    try:
        with open(SIGN_MAPPING_FILE, 'r', encoding='utf-8') as f:
            mapping = json.load(f)
        
        if 'asl' not in mapping:
            mapping['asl'] = {}
        
        updated = 0
        
        # Update with actual image paths
        for letter in 'abcdefghijklmnopqrstuvwxyz':
            for ext in ['.jpg', '.jpeg', '.png', '.gif']:
                img_path = ASL_ALPHABET_DIR / f"{letter}{ext}"
                if img_path.exists():
                    mapping['asl'][letter] = {
                        "type": "image",
                        "path": f"media/signs/asl/alphabet/{letter}{ext}",
                        "generated": False
                    }
                    updated += 1
                    break
        
        with open(SIGN_MAPPING_FILE, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Updated {updated} entries")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def cleanup():
    """Remove temporary extraction folder"""
    print("\n🧹 Cleaning up...")
    try:
        if TEMP_EXTRACT.exists():
            shutil.rmtree(TEMP_EXTRACT)
        print("✅ Done")
    except:
        pass

def main():
    print("=" * 70)
    print("   ASL.zip Image Extractor & Organizer")
    print("=" * 70)
    
    # Find ZIP
    zip_path = find_asl_zip()
    
    if not zip_path:
        print("\n❌ ASL.zip not found!")
        print("\n📍 Please place ASL.zip in one of these locations:")
        print(f"   1. {PROJECT_ROOT}")
        print(f"   2. {PROJECT_ROOT.parent}")
        print("   3. c:/Users/hp/OneDrive/Desktop/sign project/")
        print("   4. c:/Users/hp/Downloads/")
        print("\nThen run this script again.")
        return
    
    # Extract
    if not extract_asl_zip(zip_path):
        return
    
    # Organize
    count = find_and_organize_images()
    
    if count > 0:
        # Update mapping
        update_mapping()
        
        # Cleanup
        cleanup()
        
        print("\n" + "=" * 70)
        print(f"✅ SUCCESS! Organized {count} images")
        print(f"\n📊 Images saved to:")
        print(f"   {ASL_ALPHABET_DIR}")
        print("\n🎉 Your Gallery mode is now ready!")
        print("   1. Refresh your browser")
        print("   2. Type any text and translate")
        print("   3. Click 'Gallery' mode to see images!")
        print("=" * 70)
    else:
        print("\n⚠️  No images found in ASL.zip")
        print("Please check the ZIP file structure")
        cleanup()

if __name__ == "__main__":
    main()
