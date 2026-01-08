# SignSpeak - Speech/Text to Sign Language System

A web application that converts speech or text input into American Sign Language (ASL) video outputs.

---

## 📋 Project Q&A

### **Q1: What technologies have we used to develop this project?**

**Answer:**

This project is built using **pure vanilla web technologies** with NO external frameworks or libraries. Here's the complete technology stack:

#### **Frontend Technologies:**
- **HTML5** - Structure and semantic markup
- **CSS3** - Modern styling (CSS Grid, Flexbox, Variables, Animations, Glassmorphism)
- **JavaScript ES6+** - Application logic with modules, async/await, arrow functions
- **ES6 Modules** - Code organization and modularity

#### **Web APIs (Browser Built-in):**
- **Web Speech API** - Voice recognition for speech-to-text conversion
- **HTML5 Video API** - Video playback and control
- **Fetch API** - Loading JSON data dynamically
- **Canvas API** - Dynamic image generation for placeholders
- **DOM API** - Dynamic content manipulation

#### **Backend/Server:**
- **Python 3.x** - Development server (`http.server` module)
- **Custom HTTP Server** (`server.py`) - Serves static files with proper MIME types and CORS

#### **Data & Media:**
- **JSON** - Sign language mapping configuration
- **MP4 Videos** - ASL/ISL sign language demonstrations (13 phrases)
- **JPG/PNG Images** - Alphabet signs (26 letters from Kaggle ASL Dataset)

#### **Development Tools:**
- **Python Scripts** - For organizing videos, extracting datasets, processing media
- **OpenCV (cv2)** - For video-to-image conversion utilities

#### **Key Characteristics:**
✅ **Zero npm dependencies** - No package.json, no build tools  
✅ **No frameworks** - No React, Vue, Angular  
✅ **No transpilation** - Direct browser execution  
✅ **Offline capable** - Works after initial load  
✅ **Self-contained** - All code and assets are local  

---

### **Q2: Do we use NLP (Natural Language Processing) in this project?**

**Answer:**

**NO, we do NOT use traditional NLP libraries or frameworks.** Instead, we use **custom rule-based text processing algorithms** built from scratch in JavaScript.

#### **What We DON'T Use:**
❌ No NLP libraries (spaCy, NLTK, Stanford NLP)  
❌ No Machine Learning models  
❌ No AI/LLMs (ChatGPT, BERT, GPT)  
❌ No external NLP APIs  
❌ No TensorFlow/PyTorch  
❌ No Natural Language Understanding services  

#### **What We DO Use (Custom NLP-like Algorithms):**

We implemented **custom text processing algorithms** in `js/textProcessor.js`:

1. **Text Normalization Algorithm**
   - Converts to lowercase
   - Removes special characters
   - Normalizes whitespace
   - Supports Unicode (English + Hindi Devanagari characters)

2. **Contraction Expansion**
   - Rule-based dictionary replacement
   - 34 contraction mappings (e.g., "don't" → "do not", "I'm" → "I am")

3. **Tokenization Algorithm**
   - Custom greedy longest-match-first algorithm
   - Sequential token extraction (left to right)
   - Identifies phrases, words, and letters
   - Time Complexity: O(n × m)

4. **Phrase Detection Algorithm**
   - Pattern matching for 20+ common phrases
   - Longest phrase first (greedy approach)
   - Example: "thank you" matched as one phrase, not "thank" + "you"

5. **Language Detection & Translation**
   - Hindi-to-English phrase mapping
   - 22+ Hindi phrase mappings
   - Dictionary-based replacement
   - Example: "aapka naam kya hai" → "what is your name"

6. **String Matching Algorithms**
   - Regular expression pattern matching
   - Unicode range detection for Hindi (\\u0900-\\u097F)
   - Substring search for phrase identification

#### **Why Custom Algorithms Instead of NLP Libraries?**

✅ **Lightweight** - No heavy libraries to load  
✅ **Fast** - Simple hash lookups, no model inference  
✅ **Predictable** - Deterministic, same input = same output  
✅ **Offline** - Works without internet  
✅ **Privacy** - No data sent to external servers  
✅ **Sufficient** - Our use case doesn't need complex NLP  

#### **Summary:**
While we implement **NLP-like text processing** (tokenization, normalization, phrase detection), we do it using **custom JavaScript algorithms** rather than external NLP libraries. This approach is:
- **Rule-based** (not ML-based)
- **Dictionary-driven** (hash table lookups)
- **Deterministic** (not probabilistic)

---

### **Q3: Which translator do we use?**

**Answer:**

We use a **custom-built sign language translator** (`js/signTranslator.js`) - NOT any external translation service.

#### **Translation Approach:**

This is a **dictionary-based mapping system**, not a language translator like Google Translate. Here's how it works:

#### **Translation Engine: `signTranslator.js`**

**Type:** Custom JavaScript class  
**Method:** Hash table lookup (JSON mapping)  
**Languages Supported:** ASL (American Sign Language) + ISL (Indian Sign Language)

#### **Translation Process:**

```
Input Text → TextProcessor → Tokens → SignTranslator → Media Files
```

**Step-by-Step Translation:**

1. **Load Sign Mappings**
   - Reads `data/sign-mapping.json`
   - Contains mappings for both ASL and ISL
   - 58 signs per language

2. **Select Language**
   - User chooses ASL or ISL
   - Translator switches mapping dictionary

3. **Token-to-Sign Mapping**
   - For each token (phrase/word/letter)
   - Lookup in JSON mapping
   - Return media file reference (video or image)

4. **Fallback Strategy**
   ```
   Try phrase match → Try word match → Fingerspell letters → Generate placeholder
   ```

#### **Translation Data Structure:**

```json
{
  "asl": {
    "good morning": {
      "type": "video",
      "path": "media/signs/asl/phrases/Good morning.mp4"
    },
    "hello": {
      "type": "image",
      "path": "media/signs/asl/common/hello.png"
    },
    "a": {
      "type": "image",
      "path": "media/signs/asl/alphabet/a.jpg"
    }
  },
  "isl": { /* same structure */ }
}
```

#### **Algorithm Used:**

**Hash Table Lookup (O(1) average time complexity)**

```javascript
function translate(token) {
  // Direct O(1) lookup in JSON object
  const sign = signMappings[currentLanguage][token.value];
  
  if (sign) {
    return sign; // Found exact match
  } else {
    // Fallback: Fingerspell letter-by-letter
    return token.split('').map(letter => signMappings[language][letter]);
  }
}
```

#### **What This Translator Does:**

✅ Maps English/Hindi text → Sign language media files  
✅ Supports both ASL and ISL  
✅ Handles phrases, words, and alphabet fingerspelling  
✅ Bilingual input (English + Hindi)  
✅ Provides fallback for unknown words  

#### **What This Translator Does NOT Do:**

❌ NOT a language-to-language translator (English ↔ Hindi)  
❌ NOT using Google Translate API  
❌ NOT using any external translation service  
❌ NOT translating between spoken languages  
❌ NOT using AI/ML translation models  

#### **Key Difference:**

- **Google Translate:** Translates between spoken languages (English ↔ Spanish ↔ Hindi)
- **Our Translator:** Maps text → visual sign language representations

#### **Summary:**

We use a **custom dictionary-based sign language translator** built in-house. It:
- Uses **JSON hash table lookups** for instant translation
- Maps **text tokens to media file paths**
- Supports **bilingual input** (English + Hindi)
- Provides **fallback strategies** (fingerspelling)
- **No external APIs** - completely self-contained

This is more accurately called a "**Sign Language Mapper**" rather than a traditional translator.

---

## � Technology Stack Summary

### **Technologies Used:**

| Category | Technology | Purpose |
|----------|-----------|---------|
| **Frontend** | HTML5 | Structure & markup |
| | CSS3 | Styling & animations |
| | JavaScript ES6+ | Application logic |
| **Web APIs** | Web Speech API | Voice recognition |
| | HTML5 Video API | Video playback |
| | Fetch API | Load JSON data |
| **Backend** | Python 3.x | Development server |
| | http.server | Static file serving |
| **Data** | JSON | Sign mapping configuration |
| | MP4 Videos | Sign demonstrations |
| | JPG Images | Alphabet signs |
| **Architecture** | ES6 Modules | Code organization |
| | MVC Pattern | Structure |
| **Design** | CSS Grid/Flexbox | Layouts |
| | CSS Variables | Theming |
| | Glassmorphism | UI effects |

### **Key Features:**
- ✅ **Zero Dependencies** - No npm, webpack, or external libraries
- ✅ **Vanilla JavaScript** - Pure ES6+ code
- ✅ **Bilingual Support** - ASL (English) + ISL (Hindi)
- ✅ **Offline Capable** - Works after initial load
- ✅ **Rule-Based** - No AI/ML required

---

## �🚀 Quick Start

### Run with Python (Recommended)

```bash
python server.py
```

This will:
- Start a local server on `http://localhost:8000`
- Automatically open your browser
- Serve all files with proper MIME types

### Alternative: Direct Browser

Simply double-click `index.html` or run:

```bash
start index.html
```

## ✨ Features

- **Speech Recognition** - Voice-to-text using Web Speech API
- **Text Input** - Type your message
- **Video Output** - Real ASL sign language videos
- **13 Sign Videos** - Common phrases and days of the week
- **Auto-Playback** - Videos play in sequence automatically

## 🎬 Your Videos

- Good morning / Good evening
- How are you
- What is your name
- What are you doing  
- Have a good day
- Monday - Sunday (all 7 days)

## 📝 Usage

1. **Run the server:**
   ```bash
   python server.py
   ```

2. **Type a phrase:**
   - "Good morning, how are you?"
   - "See you on Monday"
   - "Have a good day"

3. **Watch the videos play!**

## 📁 Project Structure

```
new mini project/
├── server.py              # Python development server
├── index.html             # Main application
├── styles.css             # Styling
├── js/                    # JavaScript modules
│   ├── app.js
│   ├── speechRecognition.js
│   ├── textProcessor.js
│   ├── signTranslator.js
│   ├── mediaPlayer.js
│   └── mediaGenerator.js
├── data/
│   └── sign-mapping.json  # Video mappings
└── media/
    └── signs/asl/phrases/ # Your 13 ASL videos ✅
```

## 🛠️ Tools & Technologies Used

### **Frontend Technologies**

#### **Core Languages**
- **HTML5** - Structure and semantic markup
- **CSS3** - Styling with modern features (CSS Grid, Flexbox, Variables, Animations)
- **JavaScript (ES6+)** - Application logic with modules and async/await

#### **Web APIs**
- **Web Speech API** - Voice recognition for speech-to-text conversion
- **HTML5 Video API** - Video playback and control
- **Fetch API** - Loading JSON data dynamically
- **DOM API** - Dynamic content manipulation

#### **CSS Features**
- **CSS Variables** - Theme colors and spacing
- **CSS Grid & Flexbox** - Responsive layouts
- **CSS Animations** - Smooth transitions and effects
- **Backdrop Filter** - Glassmorphism effects
- **CSS Gradients** - Modern visual design

### **Backend & Development Tools**

#### **Development Server**
- **Python 3.x** - Built-in HTTP server (`http.server`)
- **Custom server.py** - Serves static files with proper MIME types
- **Features:**
  - Auto-opens browser
  - Handles CORS properly
  - Serves video files correctly

#### **Development Utilities**
- **Python Scripts**:
  - `organize_videos.py` - Organizes extracted video files
  - `extract_asl.py` - Extracts and processes ASL dataset
  - `convert_videos_to_images.py` - Converts videos to thumbnails

### **Data & Media Processing**

#### **Data Formats**
- **JSON** - Configuration and sign mapping (`sign-mapping.json`)
- **MP4 Video** - Sign language demonstration videos
- **JPG/PNG Images** - Alphabet and sign images

#### **External Resources**
- **ASL Alphabet Dataset** - Kaggle dataset (87,000+ images)
- **Sign Language Videos** - Custom recorded ASL/ISL phrases

### **Architecture & Design Patterns**

#### **Modular JavaScript Architecture**
```
js/
├── app.js                    # Main controller (ES6 Class)
├── speechRecognition.js      # Speech API handler
├── textProcessor.js          # Text normalization & tokenization
├── signTranslator.js         # Maps text to signs
├── mediaPlayer.js            # Video/image playback
└── mediaGenerator.js         # Dynamic image generation
```

#### **Design Patterns Used**
- **Module Pattern** - ES6 imports/exports
- **MVC Architecture** - Separation of concerns
- **Observer Pattern** - Event-driven callbacks
- **Singleton Pattern** - Single app instance
- **Strategy Pattern** - Different display modes (Gallery/Video)

### **Algorithms Used**

#### **YES - Multiple algorithms are implemented:**

1. **Text Processing Algorithms**
   - **Text Normalization** - Converts input to lowercase, removes special characters
   - **Contraction Expansion** - Expands "don't" → "do not", "I'm" → "I am"
   - **Whitespace Normalization** - Removes extra spaces

2. **Phrase Matching Algorithm**
   - **Greedy Longest Match First** 
     - Sorts phrases by length (longest first)
     - Matches longest phrase from current position
     - Example: "thank you" matched as one phrase, not "thank" + "you"
   - **Time Complexity**: O(n × m) where n = text length, m = number of phrases

3. **String Search & Pattern Matching**
   - **Regular Expression Matching** - Pattern matching for words and letters
   - **Unicode Range Matching** - Detects Hindi/Devanagari characters (\u0900-\u097F)
   - **Substring Search** - Finding Hindi phrases in input text

4. **Tokenization Algorithm**
   - **Sequential Token Extraction**
     - Processes text left to right
     - Identifies phrases, words, and letters
     - Creates token objects with metadata
   - **Output**: Array of token objects `{type, value, words}`

5. **Translation/Mapping Algorithm**
   - **Hash Table Lookup** (JSON object)
     - O(1) average case lookup for word → sign mapping
     - Handles both English and Hindi phrases
   - **Fallback Strategy**: 
     - Try phrase match → Try word match → Fingerspell letters

6. **Hindi-to-English Conversion Algorithm**
   - **Dictionary Replacement**
     - Maps Hindi phrases to English equivalents
     - Example: "aapka naam kya hai" → "what is your name"
   - **Pre-processing Step** - Runs before English phrase matching

7. **Video Sequencing Algorithm**
   - **Queue-based Playback**
     - Loads videos in order
     - Auto-advances on video end event
     - Loops back to start when complete

8. **Array Sorting Algorithm**
   - **JavaScript Native Sort** - Used for sorting phrases by length
   - **Comparator Function**: `(a, b) => b.length - a.length`

9. **Search Algorithms**
   - **Linear Search** - Finding matching phrases in array
   - **Object Property Lookup** - Hash table access in JSON

10. **Character Classification**
    - **Regex-based Classification**
      - Identifies letters: `/[a-z]/`
      - Identifies words: `/[a-z0-9'-]+/`
      - Identifies Hindi: `/[\u0900-\u097F]/`

### **Algorithm Complexity Analysis**

| Algorithm | Time Complexity | Space Complexity |
|-----------|----------------|------------------|
| Phrase Matching | O(n × m) | O(1) |
| Hash Lookup | O(1) average | O(k) k=mappings |
| Tokenization | O(n) | O(n) |
| Text Normalization | O(n) | O(n) |
| Video Sequencing | O(p) p=phrases | O(p) |

### **AI & Machine Learning**

#### **Does this project use LLMs or AI models?**

**NO** - This project does NOT use:
- ❌ Large Language Models (LLMs)
- ❌ Machine Learning models
- ❌ Neural Networks
- ❌ Deep Learning
- ❌ AI APIs (OpenAI, Google AI, etc.)
- ❌ TensorFlow / PyTorch
- ❌ Cloud AI Services

#### **What it DOES use:**

✅ **Rule-Based Algorithms** - Deterministic text processing
✅ **Hash Table Lookups** - Simple JSON mappings
✅ **String Matching** - Regex patterns and string operations
✅ **Browser APIs** - Web Speech API (built-in browser feature)
✅ **Static Data** - Pre-defined sign mappings

#### **Why No AI/ML?**

- **Simple & Fast** - Direct mapping is more efficient
- **Offline Capable** - No internet required after initial load
- **Predictable** - Same input always gives same output
- **Lightweight** - No large model files to download
- **Privacy** - No data sent to external servers

#### **Technology Approach:**

This is a **Dictionary-Based Translation System**:
1. User inputs text
2. Text is normalized and tokenized
3. Tokens are matched against pre-defined mappings
4. Corresponding videos/images are displayed

**No training, no inference, no AI needed!**

### **Browser Technologies**

#### **Required Browser Features**
- **ES6 Module Support** - `<script type="module">`
- **Arrow Functions** - Modern JavaScript syntax
- **Async/Await** - Asynchronous operations
- **Template Literals** - String interpolation
- **Destructuring** - Clean code patterns

#### **Optional Features**
- **Speech Recognition** - Chrome/Edge only
- **Video Autoplay** - Most modern browsers
- **CSS Backdrop Filter** - Safari/Chrome/Edge

### **Version Control & Setup**

#### **No Build Tools Required!**
- ✅ No npm/webpack/babel needed
- ✅ No transpilation required
- ✅ Pure vanilla JavaScript
- ✅ Direct browser execution

#### **Dependencies**
- **Zero external libraries**
- **No CDN dependencies**
- **No package.json**
- **Self-contained application**

### **Development Environment**

#### **Recommended Tools**
- **Code Editor**: VS Code / Sublime / Any text editor
- **Browser**: Chrome or Edge (for full features)
- **Python**: 3.x for development server
- **Terminal**: For running server commands

#### **Optional Tools**
- **Browser DevTools** - Debugging and testing
- **Git** - Version control
- **Image Editor** - For creating custom signs

### **Data Sources**

#### **Sign Language Resources**
- **Kaggle ASL Dataset** - Alphabet images
  - URL: `kaggle.com/datasets/grassknoted/asl-alphabet`
  - Size: 87,000 images
  - Format: 200x200 JPG

- **Custom Videos** - Phrase demonstrations
  - Format: MP4
  - Resolution: Variable
  - Count: 13 phrases

### **Key Features Implementation**

#### **Hindi Language Support**
- **Unicode Support** - Devanagari character range (\u0900-\u097F)
- **Phrase Mapping** - 22+ Hindi-to-English mappings
- **Fallback System** - English equivalent conversion

#### **Bilingual System**
- **ASL (American Sign Language)** - English input
- **ISL (Indian Sign Language)** - Hindi/English input
- **Dynamic Switching** - Toggle between languages

### **Performance Optimizations**

- **Lazy Loading** - Videos load on demand
- **JSON Caching** - Sign mappings loaded once
- **Efficient DOM Updates** - Minimal reflows
- **CSS Hardware Acceleration** - Smooth animations
- **Event Delegation** - Efficient event handling

### **Accessibility Features**

- **Semantic HTML** - Screen reader friendly
- **ARIA Labels** - Enhanced accessibility
- **Keyboard Navigation** - Full keyboard support
- **High Contrast** - Dark theme by default
- **Clear Typography** - Inter font, large sizes

---

## 🛠️ Requirements

### **Hardware Requirements**
- **Device**: PC, Laptop, or Tablet
- **Input**:
  - **Microphone**: Required for Speech-to-Sign feature.
  - **Keyboard**: For text input.
- **Output**:
  - **Screen**: To view the sign language videos.
  - **Speakers**: For system feedback (optional).
- **Internet**: Not required for core functionality (works offline), but needed if you want to deploy or update.

### **Software Requirements**
- **Operating System**: Windows 10/11, macOS, or Linux. (Project is OS-agnostic web tech).
- **Web Browser**:
  - **Google Chrome** (v60+) - **Recommended** for best Web Speech API support.
  - **Microsoft Edge** (v79+) - Fully supported.
  - **Safari** - Supported (Speech recognition may need specific permissions).
  - **Firefox** - Supported (Speech API requires configuration).
- **Python**: Version **3.8 or higher** recommended (only for running the local server).
- **Dependencies**: **NONE**. No `npm`, `pip install`, or `node_modules` required. The project is self-contained.

## 📖 How to Add More Videos

1. **Add video file** to `media/signs/asl/phrases/`
2. **Update `data/sign-mapping.json`:**
   ```json
   "your phrase": {
     "type": "video",
     "path": "media/signs/asl/phrases/your_video.mp4",
     "generated": false
   }
   ```
3. **Add to `js/textProcessor.js`** if multi-word phrase
4. **Refresh browser** and test!

## 🎯 Commands

**Start server:**
```bash
python server.py
```

**Stop server:**
Press `Ctrl+C` in the terminal

## 🌐 Browser Compatibility

- ✅ Chrome/Edge (recommended)
- ✅ Firefox (limited speech recognition)
- ✅ Safari (basic support)

## 📄 License

Educational use

---

## 🏗️ Project Implementation

### System Architecture

SignSpeak follows a **modular, event-driven architecture** with clear separation of concerns. The system is built on vanilla JavaScript ES6+ modules with no external framework dependencies.

#### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interface (HTML/CSS)               │
│  - Input Section (Text/Speech)                              │
│  - Output Section (Gallery/Video)                           │
│  - Controls (Language, Mode, Playback)                      │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│              Main Controller (app.js)                        │
│  - Coordinates all modules                                  │
│  - Handles UI events                                        │
│  - Manages application state                                │
└─────┬─────┬─────┬─────┬─────┬────────────────────────────┘
      │     │     │     │     │
      ▼     ▼     ▼     ▼     ▼
┌─────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Speech  │ │   Text   │ │   Sign   │ │  Media   │ │  Media   │
│Recognition│ │Processor │ │Translator│ │  Player  │ │Generator │
│   .js   │ │   .js    │ │   .js    │ │   .js    │ │   .js    │
└─────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘
      │            │            │            │            │
      └────────────┴────────────┴────────────┴────────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Data Layer (JSON)  │
                    │  sign-mapping.json  │
                    └─────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Media Files       │
                    │ - Videos (MP4)      │
                    │ - Images (JPG/PNG)  │
                    └─────────────────────┘
```

### Complete Data Flow

Here's how the application processes user input from start to finish:

#### Step-by-Step Workflow

```
1. USER INPUT
   ├─ Option A: Speech Input
   │  ├─ User clicks microphone button
   │  ├─ Web Speech API starts listening
   │  ├─ Speech converted to text in real-time
   │  └─ Text placed in input field
   └─ Option B: Manual Text Input
      └─ User types directly into textarea

2. TEXT PROCESSING (textProcessor.js)
   ├─ Clean text (lowercase, remove special chars)
   ├─ Expand contractions ("don't" → "do not")
   ├─ Detect language (English/Hindi)
   ├─ Convert Hindi phrases to English equivalents
   │  Example: "aapka naam kya hai" → "what is your name"
   └─ Tokenize into phrases and words
      ├─ Greedy longest-match algorithm
      ├─ Check for multi-word phrases first
      └─ Fall back to individual words
      
      Example Input: "Good morning, how are you?"
      Tokens Output: 
      [
        {type: "phrase", value: "good morning", words: ["good", "morning"]},
        {type: "phrase", value: "how are you", words: ["how", "are", "you"]}
      ]

3. SIGN TRANSLATION (signTranslator.js)
   ├─ Load sign-mapping.json data
   ├─ Select correct language (ASL or ISL)
   ├─ For each token:
   │  ├─ Try phrase match first
   │  ├─ If no phrase, try word match
   │  └─ If no word, fingerspell letter-by-letter
   └─ Build media reference array
   
      Example Translation:
      "good morning" → {
        type: "video",
        path: "media/signs/asl/phrases/Good morning.mp4"
      }
      
      "hello" → {
        type: "image",
        path: "media/signs/asl/common/hello.png"
      }
      
      "xyz" → [
        {type: "image", path: "media/signs/asl/alphabet/x.jpg"},
        {type: "image", path: "media/signs/asl/alphabet/y.jpg"},
        {type: "image", path: "media/signs/asl/alphabet/z.jpg"}
      ]

4. MEDIA DISPLAY (mediaPlayer.js)
   ├─ Check display mode (Gallery or Video)
   ├─ Gallery Mode (for images/fingerspelling):
   │  ├─ Create grid layout
   │  ├─ Display all images simultaneously
   │  └─ Show sign labels
   └─ Video Mode (for videos/phrases):
      ├─ Create sequential playlist
      ├─ Load first video
      ├─ Auto-play on video end event
      ├─ Show playback controls (speed, prev/next)
      └─ Loop when complete

5. DYNAMIC GENERATION (mediaGenerator.js)
   └─ If media file doesn't exist:
      ├─ Generate placeholder image
      ├─ Use Canvas API to create sign graphic
      ├─ Add text label
      └─ Return data URL for display
```

### Module Breakdown

#### 1. **app.js** - Main Application Controller

**Responsibilities:**
- Initialize all modules
- Setup event listeners
- Coordinate module interactions
- Manage UI state and updates
- Handle user interactions

**Key Functions:**
```javascript
- init()                    // Initialize application
- setupUI()                 // Setup UI elements
- setupEventListeners()     // Bind all event handlers
- handleTranslate()         // Process translation request
- handleLanguageChange()    // Switch between ASL/ISL
- handleModeChange()        // Switch Gallery/Video mode
- showStatus()              // Display progress messages
```

**Event Flow:**
```
User Action → Event Listener → Module Call → Data Processing → UI Update
```

#### 2. **speechRecognition.js** - Voice Input Handler

**Responsibilities:**
- Interface with Web Speech API
- Handle speech recognition lifecycle
- Convert speech to text
- Manage recognition errors

**Key Features:**
```javascript
- Continuous recognition mode
- Real-time transcription
- Error handling (no microphone, not supported, etc.)
- Status callbacks (listening, stopped, error)
- Noise cancellation support
```

**Browser Compatibility:**
- ✅ Chrome/Edge (full support)
- ⚠️ Firefox (limited support)
- ❌ Safari (not fully supported)

**API Used:**
```javascript
const recognition = new webkitSpeechRecognition() || new SpeechRecognition();
recognition.continuous = false;
recognition.interimResults = false;
recognition.lang = 'en-US'; // or 'hi-IN' for Hindi
```

#### 3. **textProcessor.js** - Text Analysis Engine

**Responsibilities:**
- Normalize and clean input text
- Expand contractions
- Detect phrases vs. individual words
- Handle bilingual input (English + Hindi)
- Tokenize text into processable units

**Processing Pipeline:**
```
Raw Text → Clean → Expand Contractions → Detect Language 
         → Convert Hindi → Tokenize → Output Token Array
```

**Data Structures:**

**Contractions Dictionary** (34 mappings):
```javascript
{
  "i'm": "i am",
  "you're": "you are",
  "won't": "will not",
  "can't": "can not"
  // ... etc
}
```

**Common Phrases List** (20 phrases):
```javascript
[
  "how are you",
  "thank you",
  "good morning",
  "what is your name",
  // ... etc
]
```

**Hindi Phrase Mappings** (22 mappings):
```javascript
{
  "aapka naam kya hai": "what is your name",
  "namaste": "hello",
  "shukriya": "thank you",
  "aap kaise hain": "how are you"
  // ... etc
}
```

**Algorithms Used:**

**1. Greedy Longest Match First**
```
Purpose: Match longest phrases before shorter ones
Process:
  1. Sort phrases by length (descending)
  2. Scan text from left to right
  3. Try to match longest phrase at current position
  4. If matched, consume phrase and advance
  5. If not matched, try next shorter phrase
  6. If no phrase matches, take single word
Time: O(n × m) where n = text length, m = phrase count
```

**2. Unicode Range Detection**
```
Purpose: Identify Hindi (Devanagari) characters
Regex: /[\u0900-\u097F]/
Range: Covers all Devanagari Unicode characters
```

#### 4. **signTranslator.js** - Translation Engine

**Responsibilities:**
- Load sign mappings from JSON
- Map tokens to media files
- Handle ASL/ISL language switching
- Implement fallback strategies
- Manage missing sign cases

**Translation Strategy:**
```
For each token:
  1. Try exact phrase/word match
  2. If found → return media reference
  3. If not found → fingerspell letter-by-letter
  4. If letter not found → use generated placeholder
```

**Sign Mapping Structure:**
```json
{
  "asl": {
    "phrase/word": {
      "type": "video" | "image",
      "path": "media/signs/asl/category/filename.ext",
      "generated": false | true
    }
  },
  "isl": { /* same structure */ }
}
```

**Categories:**
- `alphabet/` - A-Z fingerspelling letters
- `common/` - Common words (hello, goodbye, please, etc.)
- `phrases/` - Multi-word phrases and days of week

**Total Signs Available:**
- **26** alphabet letters (A-Z)
- **11** common words
- **8** generated phrases
- **13** video phrases
- **Total: 58 signs per language**

#### 5. **mediaPlayer.js** - Media Playback Controller

**Responsibilities:**
- Display images in gallery mode
- Play videos in sequence
- Control playback (play/pause/speed)
- Navigate between signs
- Handle video events

**Display Modes:**

**Gallery Mode** (for images):
```
- CSS Grid layout (auto-fit, min 150px)
- All images displayed simultaneously
- Shows sign labels below each image
- Responsive grid that adapts to screen size
- Best for: alphabet fingerspelling, short words
```

**Video Mode** (for videos):
```
- Sequential playback
- One video at a time
- Auto-advance to next video
- Playback controls:
  - Previous/Next buttons
  - Speed control (0.5x - 2x)
  - Pause/Play
  - Progress indicator
- Best for: phrases, sentences
```

**Video Event Handling:**
```javascript
video.addEventListener('ended', () => {
  currentIndex++;
  if (currentIndex < playlist.length) {
    loadVideo(playlist[currentIndex]);
  } else {
    // Loop back to start or show completion
  }
});
```

#### 6. **mediaGenerator.js** - Dynamic Image Generator

**Responsibilities:**
- Generate placeholder images for missing signs
- Create visual representations using Canvas API
- Add text labels to images
- Provide fallback when media files unavailable

**Canvas Generation Process:**
```javascript
1. Create canvas element (400x400px)
2. Get 2D rendering context
3. Draw background gradient
4. Draw hand emoji/icon (✋)
5. Draw sign text label
6. Convert canvas to data URL
7. Return as image source
```

**Use Cases:**
- Missing sign files during development
- Rapid prototyping without media assets
- Fallback for unsupported words/phrases
- Testing new sign additions

### Data Processing Algorithms

#### 1. **Phrase Matching Algorithm**

**Problem:** Given input text and a list of known phrases, extract the longest matching phrases.

**Solution:** Greedy Longest Match First

```javascript
function tokenize(text) {
  const tokens = [];
  let remaining = text;
  
  // Sort phrases by length (longest first)
  const sorted = phrases.sort((a, b) => b.length - a.length);
  
  while (remaining.length > 0) {
    let matched = false;
    
    // Try each phrase starting with longest
    for (const phrase of sorted) {
      if (remaining.startsWith(phrase)) {
        tokens.push({type: 'phrase', value: phrase});
        remaining = remaining.slice(phrase.length).trim();
        matched = true;
        break;
      }
    }
    
    // If no phrase matched, take next word
    if (!matched) {
      const word = remaining.match(/^([a-z0-9]+)/)[1];
      tokens.push({type: 'word', value: word});
      remaining = remaining.slice(word.length).trim();
    }
  }
  
  return tokens;
}
```

**Example:**
```
Input: "thank you very much"
Phrases: ["thank you", "very much", "thank"]

Process:
1. Try "thank you" at position 0 ✓ Match!
   Token: {type: "phrase", value: "thank you"}
   Remaining: "very much"

2. Try "thank you" at position 0 ✗ No match
   Try "very much" at position 0 ✓ Match!
   Token: {type: "phrase", value: "very much"}
   Remaining: ""

Output: [{phrase: "thank you"}, {phrase: "very much"}]
```

**Complexity:**
- Time: O(n × m) - n = text length, m = phrases
- Space: O(n) - for token array

#### 2. **Hash Table Lookup Algorithm**

**Problem:** Quickly find media file for a given word/phrase.

**Solution:** JSON Object as Hash Map

```javascript
const signMappings = {
  "asl": {
    "hello": {type: "image", path: "..."},
    "goodbye": {type: "image", path: "..."}
  }
};

function translate(word, language) {
  // O(1) average case lookup
  const mapping = signMappings[language][word];
  
  if (mapping) {
    return mapping; // Found
  } else {
    // Fallback: fingerspell
    return fingerspell(word);
  }
}
```

**Complexity:**
- Time: O(1) average case
- Space: O(k) - k = number of sign mappings

#### 3. **Fingerspelling Algorithm**

**Problem:** Convert unknown words to letter-by-letter signs.

**Solution:** Character Array Mapping

```javascript
function fingerspell(word) {
  const letters = word.toLowerCase().split('');
  
  return letters.map(letter => {
    if (/[a-z]/.test(letter)) {
      return {
        type: "image",
        path: `media/signs/asl/alphabet/${letter}.jpg`,
        letter: letter
      };
    }
  }).filter(Boolean);
}
```

**Example:**
```
Input: "cat"
Output: [
  {type: "image", path: "media/.../c.jpg", letter: "c"},
  {type: "image", path: "media/.../a.jpg", letter: "a"},
  {type: "image", path: "media/.../t.jpg", letter: "t"}
]
```

**Complexity:**
- Time: O(n) - n = word length
- Space: O(n)

### Backend Implementation

#### Python Development Server

**Purpose:** Serve static files with proper MIME types and CORS headers.

**server.py Structure:**

```python
import http.server
import socketserver

class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS for local development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        super().end_headers()
    
    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
        return super().do_GET()

# Start server on port 8000
with socketserver.TCPServer(("", 8000), MyHttpRequestHandler) as httpd:
    httpd.serve_forever()
```

**Features:**
- ✅ Auto-redirects `/` to `/index.html`
- ✅ CORS headers for API requests
- ✅ Proper MIME types for `.mp4`, `.jpg`, `.json`
- ✅ Auto-opens browser on start
- ✅ Graceful shutdown on Ctrl+C

**Why Python Server?**
1. Cross-platform (Windows/Mac/Linux)
2. No installation needed (Python built-in)
3. Handles video files correctly
4. Simple and lightweight

### Dataset Processing Scripts

#### 1. **setup_kaggle_dataset.py**

**Purpose:** Download and extract ASL alphabet dataset from Kaggle.

**Features:**
- Downloads ASL alphabet dataset (87,000+ images)
- Extracts ZIP files
- Organizes images by letter (A-Z)
- Validates image quality
- Creates folder structure

#### 2. **convert_videos_to_images.py**

**Purpose:** Extract thumbnail frames from video files.

**Process:**
```
1. Scan media/signs/asl/phrases for .mp4 files
2. Extract middle frame using OpenCV/PIL
3. Save as JPG thumbnail
4. Optional: Create animated GIF preview
```

#### 3. **organize_dataset.py**

**Purpose:** Organize extracted media files into correct folders.

**Folder Structure Created:**
```
media/
├── signs/
│   ├── asl/
│   │   ├── alphabet/    # A-Z images
│   │   ├── common/      # Common words
│   │   └── phrases/     # Video phrases
│   └── isl/
│       ├── alphabet/
│       ├── common/
│       └── phrases/
```

#### 4. **organize_videos.py**

**Purpose:** Move and rename video files from extracted folders.

**Process:**
```
1. Scan for video files in extracted/ folder
2. Identify phrase based on filename
3. Move to correct category (phrases/common)
4. Rename with standardized naming
5. Update sign-mapping.json
```

### Complete Translation Example

Let's trace a complete example through the entire system:

**Input:** "Good morning, how are you?"

**Step 1: Text Processing**
```
Raw: "Good morning, how are you?"
Cleaned: "good morning how are you"
Contractions: (none to expand)
Tokens: [
  {type: "phrase", value: "good morning", words: ["good", "morning"]},
  {type: "phrase", value: "how are you", words: ["how", "are", "you"]}
]
```

**Step 2: Sign Translation**
```
Token 1: "good morning"
  → Look up in signMappings["asl"]["good morning"]
  → Found: {type: "video", path: "media/signs/asl/phrases/Good morning.mp4"}

Token 2: "how are you"
  → Look up in signMappings["asl"]["how are you"]
  → Found: {type: "video", path: "media/signs/asl/phrases/How are you.mp4"}

Media Array: [
  {type: "video", path: "media/signs/asl/phrases/Good morning.mp4"},
  {type: "video", path: "media/signs/asl/phrases/How are you.mp4"}
]
```

**Step 3: Media Display**
```
Mode: Video (because both are videos)

Playlist: [
  "media/signs/asl/phrases/Good morning.mp4",
  "media/signs/asl/phrases/How are you.mp4"
]

Playback:
1. Load first video: "Good morning.mp4"
2. Play video
3. On video.ended event → Load next video
4. Play "How are you.mp4"
5. On second video.ended → Show completion message
```

**UI Output:**
```
┌────────────────────────────────┐
│     Video Player               │
│  ┌──────────────────────────┐  │
│  │                          │  │
│  │  [Playing: Good Morning] │  │
│  │                          │  │
│  └──────────────────────────┘  │
│  Progress: 1 of 2              │
│  [◄ Previous] [Pause] [Next ►]│
│  Speed: 1.0x                   │
└────────────────────────────────┘
```

### Performance Characteristics

#### Time Complexity Analysis

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Load JSON | O(1) | One-time on startup |
| Text Cleaning | O(n) | n = text length |
| Contraction Expansion | O(n × c) | c = contractions count |
| Phrase Matching | O(n × m) | m = phrases count |
| Token Translation | O(t) | t = token count |
| Hash Lookup | O(1) | Average case |
| Fingerspelling | O(k) | k = word length |
| Video Loading | O(1) | Per video |
| Gallery Rendering | O(s) | s = signs to display |

#### Space Complexity

| Component | Space | Notes |
|-----------|-------|-------|
| Sign Mappings | O(k) | k = total signs (~58 per language) |
| Token Array | O(t) | t = tokens extracted |
| Media Playlist | O(p) | p = playlist length |
| DOM Elements | O(s) | s = visible signs |

#### Optimization Strategies

1. **Lazy Loading:** Videos load on-demand, not all at once
2. **JSON Caching:** Sign mappings loaded once and kept in memory
3. **Efficient DOM Updates:** Minimal reflows, batch updates
4. **CSS Hardware Acceleration:** GPU-accelerated animations
5. **Event Delegation:** Single listeners vs. multiple per element

### Error Handling & Edge Cases

#### Input Edge Cases

```javascript
// Empty input
Input: ""
Output: {tokens: [], original: ""}

// Special characters only
Input: "!@#$%"
Output: {tokens: [], original: "!@#$%"}

// Mixed English + Hindi
Input: "hello namaste"
Output: [
  {type: "word", value: "hello"},
  {type: "word", value: "namaste" → "hello"}
]

// Unknown words
Input: "supercalifragilisticexpialidocious"
Output: Fingerspell all 34 letters
```

#### Error Handling

```javascript
// Missing media file
if (!fileExists(signPath)) {
  return mediaGenerator.generate(signText);
}

// Speech recognition error
recognition.onerror = (event) => {
  if (event.error === 'no-speech') {
    showError('No speech detected. Please try again.');
  }
};

// JSON loading failure
try {
  signMappings = await fetch('data/sign-mapping.json').then(r => r.json());
} catch (error) {
  signMappings = getDefaultMappings(); // Fallback
}
```

### Browser Compatibility & Requirements

#### Minimum Requirements

- **Browser:** Chrome 60+, Edge 79+, Firefox 78+, Safari 14+
- **JavaScript:** ES6+ support (2015+)
- **Features Required:**
  - ES6 Modules (`import`/`export`)
  - Arrow functions
  - Template literals
  - `async`/`await`
  - Fetch API
  - HTML5 Video

#### Optional Features

- **Web Speech API:** Chrome/Edge only (for voice input)
- **CSS Backdrop Filter:** Chrome/Safari (for UI effects)

### Deployment Options

#### Local Development

```bash
# Run with Python
python server.py

# Access at http://localhost:8000
```

#### Static Hosting

Can be deployed to any static hosting service:
- **GitHub Pages:** Free, easy setup
- **Netlify:** Drag & drop deployment
- **Vercel:** Automatic deployments
- **Firebase Hosting:** Google infrastructure

**Deployment Steps:**
1. Upload all files to hosting service
2. Ensure `index.html` is at root
3. Configure server to serve `.mp4` with correct MIME type
4. Enable HTTPS (optional but recommended)

### Future Enhancement Possibilities

#### Technical Improvements

1. **Offline Support:** Service Worker for PWA
2. **Caching:** Cache API for media files
3. **Compression:** Reduce video file sizes
4. **WebRTC:** Real-time sign detection with camera
5. **Database:** Move from JSON to IndexedDB for larger datasets

#### Feature Additions

1. **User Recordings:** Let users record their own signs
2. **Custom Dictionaries:** Personal sign vocabulary
3. **Multi-language:** Add more sign languages (BSL, Auslan, etc.)
4. **Speed Learning:** Quiz mode to learn signs
5. **Social Sharing:** Share sign sequences

#### AI/ML Integration (Future)

While currently rule-based, could add:
- **Computer Vision:** Real-time sign recognition from webcam
- **NLP:** Better phrase understanding with transformer models
- **Gesture Synthesis:** AI-generated sign animations

---

## 📊 Project Statistics

### Code Metrics

| Metric | Count |
|--------|-------|
| **Total Lines of Code** | ~2,500 lines |
| **JavaScript Files** | 6 modules |
| **Python Scripts** | 4 utilities |
| **HTML Files** | 1 main page |
| **CSS Lines** | ~500 lines |
| **JSON Data** | 1 mapping file |

### Media Assets

| Asset Type | Count | Total Size |
|------------|-------|------------|
| **Alphabet Images** | 26 (A-Z) | ~5 MB |
| **Common Word Images** | 11 | ~2 MB |
| **Generated Phrase Images** | 8 | ~1 MB |
| **Video Phrases** | 13 | ~750 KB |
| **Total Media Files** | 58 | ~8 MB |

### Sign Language Coverage

| Category | ASL | ISL | Total |
|----------|-----|-----|-------|
| **Alphabet** | 26 | 26 | 26 |
| **Common Words** | 11 | 11 | 11 |
| **Phrases** | 21 | 21 | 21 |
| **Days of Week** | 7 | 7 | 7 |
| **Total Signs** | 58 | 58 | 58 |

---

**Made with ❤️ for the deaf and hard-of-hearing community**
