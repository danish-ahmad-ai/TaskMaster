# Contributing to TaskMaster (With Keylogger)

⚠️ **Educational Version**: This repository contains keystroke monitoring functionality for educational purposes. For contributing to the clean version, visit [TaskMaster Clean Version](https://github.com/danish-ahmad-ai/TaskMaster).

## Development Setup

1. Fork the [repository](https://github.com/danish-ahmad-ai/AdvanceToDoList)
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Setup development environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   pip install -r requirements.txt
   ```
4. Copy `firebase_config_example.py` to `firebase_config.py` and add your Firebase credentials
5. Make your changes
6. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
7. Push to the branch (`git push origin feature/AmazingFeature`)
8. Open a Pull Request

## Project Structure

```
AdvanceToDoList/
├── ui/                    # UI components
│   ├── main_ui.py        # Main task interface
│   ├── login_ui.py       # Login interface
│   ├── account_ui.py     # Account management
│   ├── modern_widgets.py # Custom widgets
│   └── custom_widgets.py # Additional widgets
├── run.py                # Application entry point
├── utils.py              # Utility functions
├── firebase_config.py    # Firebase configuration (not in repo)
└── requirements.txt      # Project dependencies
```