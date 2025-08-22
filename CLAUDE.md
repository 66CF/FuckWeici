# CLAUDE.md

This file provides guidance to Gemini when working with code in this repository.

## Overview

This is a Python-based English vocabulary learning automation tool that interfaces with Android apps via uiautomator2. The system automatically answers different types of English vocabulary questions by combining local database lookups with optional LLM assistance.

## Project Structure

### Core Modules
- **VictorApp.py**: Main application logic and UI automation
  - Handles 5 question types: spelling (拼写), English-to-Chinese translation (英译汉), mixed questions (大杂烩), listening (听音识词), and word building (构词法拼词)
  - Uses uiautomator2 for Android device interaction
  - Integrates with both local database (SearchResult) and optional LLM helper
  - Implements retry mechanisms and performance timing

- **SearchResult.py**: Local database management and search functionality
  - Loads and manages three JSON data files in the Data/ directory
  - Provides optimized search methods for different question types
  - Generates WordCorresponding.json if missing (performance-intensive operation)
  - Handles word lookup by phonetic notation, meaning, and word parts

- **LLMHelper.py**: Optional LLM integration for answering questions
  - Configurable API support (OpenAI, Groq, DeepSeek, custom proxies)
  - Handles three question types: multiple choice, spelling, and word building
  - Includes proper error handling and timeout mechanisms
  - Falls back to local database if LLM is unavailable

- **config.py**: Configuration management
  - Contains LLM API settings and credentials
  - Controls enable/disable of LLM features
  - Stores API keys, base URLs, and model selection

### Data Files (Data/)
- **fb_word_detail.json**: Comprehensive word database with phonetic symbols, parts of speech, and Chinese meanings
- **newAnswer.json**: Pre-computed answers for different question types (context, translation, word building)
- **WordCorresponding.json**: Generated index file mapping words to their properties for faster lookup

### Build and Execution Scripts
- **启动.bat**: Windows batch script to start the application (kills ADB server and runs VictorApp.py)
- **安装依赖.bat**: Windows batch script to install uiautomator2 dependency

## Development Commands

### Running the Application
```bash
# Main execution (Windows)
启动.bat

# Direct Python execution
python VictorApp.py
```

### Installing Dependencies
```bash
# Install uiautomator2 (Windows)
安装依赖.bat

# Manual installation
python -m pip install --upgrade pip
python -m pip install -U uiautomator2
```

### Prerequisites
- Python 3.x installed
- Android device connected with USB debugging enabled
- uiautomator2 Python package
- ADB (Android Debug Bridge) configured

## Architecture Patterns

### Question Type Handling
The application uses a strategy pattern with a dictionary mapping question types to handler methods:
```python
self.TITLES = {
    1: self.__spellTitle,        # Spelling questions
    2: self.__englishToChinese,  # English to Chinese
    345: self.__question,        # Mixed questions
    6: self.__listen,           # Listening comprehension
    7: self.__buildWord,        # Word building
}
```

### Data Flow
1. **Question Detection**: `tellTitle()` identifies question type by examining UI elements
2. **Local Lookup**: `SearchResult` searches local JSON databases first
3. **LLM Fallback**: If local lookup fails, `LLMHelper` provides intelligent answers
4. **UI Interaction**: Answer is selected via uiautomator2 element interaction

### Performance Optimization
- **Caching**: `WordCorresponding.json` is generated once for faster subsequent lookups
- **Retry Logic**: Multiple attempts for question type recognition with delays
- **Permutation Handling**: Efficient handling of word building combinations
- **Timing Metrics**: Comprehensive performance logging throughout the application

### Configuration Management
- **Modular Config**: Separate config.py file for LLM settings
- **Graceful Degradation**: Application works with or without LLM integration
- **Environment Agnostic**: Supports multiple LLM providers through configuration

## Key Integration Points

### Android UI Automation
- Package: `com.android.weici.senior.student`
- UI elements identified by resource IDs (e.g., `keyboard`, `english`, `question`)
- Position-aware interaction (handles multiple question displays)

### Error Handling
- Comprehensive exception handling throughout the application
- Graceful fallbacks when LLM services are unavailable
- Retry mechanisms for UI element detection
- User-friendly error messages in Chinese

### Logging System
- Custom console styling with ANSI colors
- Verbosity-controlled logging
- Performance timing for all major operations
- Structured log messages with prefixes ([i], [✓], [!], [x], [v])