# CLAUDE.md

This file provides guidance to Gemini when working with code in this repository.

## Project Overview

This is an Android automation tool called "Victor" that automatically answers English vocabulary questions in the "Weici Senior Student" app (com.android.weici.senior.student). The tool uses uiautomator2 for Android UI automation and includes LLM integration for intelligent question answering.

## Architecture

- **VictorApp.py**: Main application that handles UI interaction and question solving
- **SearchResult.py**: Database search and answer retrieval from JSON data files
- **LLMHelper.py**: LLM integration for intelligent question answering
- **config.py**: Configuration for LLM API settings
- **Data/**: JSON database files containing vocabulary and answer data

## Key Components

### Question Types Handled
1. **拼写 (Spelling)**: Type words based on phonetic symbols
2. **构词法拼词 (Word Building)**: Build words from parts
3. **英译汉 (English to Chinese)**: Translate English words to Chinese
4. **大杂烩 (Mixed Questions)**: Various question types including Chinese to English
5. **听音识词 (Listening)**: Identify words from audio

### Data Files
- `fb_word_detail.json`: Detailed vocabulary database
- `WordCorresponding.json`: Generated word-phonetic mapping
- `newAnswer.json`: Predefined answers for different question types

## Development Commands

### Installation
```bash
# Install dependencies
安装依赖.bat
```

### Running the Application
```bash
# Start the automation tool
启动.bat
# Or directly
python VictorApp.py
```

### Configuration
Edit `config.py` to configure LLM settings:
- Set `LLM_ENABLED = True/False` to enable/disable LLM assistance
- Configure API key, base URL, and model name for LLM integration

## Important Notes

- The tool requires an Android device connected via ADB
- UI automation uses uiautomator2 library
- LLM integration supports multiple providers (Groq, OpenAI, DeepSeek, custom proxies)
- Performance is monitored with detailed timing logs
- Data files are loaded from the `Data/` directory during initialization

## File Structure
```
├── VictorApp.py      # Main application
├── SearchResult.py   # Database search
├── LLMHelper.py      # LLM integration
├── config.py         # Configuration
├── 启动.bat          # Launch script
├── 安装依赖.bat      # Dependency installer
└── Data/
    ├── fb_word_detail.json
    ├── WordCorresponding.json
    ├── newAnswer.json
    └── newAnswer.bak.json
```