# TaskMaster

A modern, secure task management application built with Python and Firebase.

## Features
- Secure user authentication
- Real-time task synchronization
- Priority management
- Due date tracking
- Task notes and details
- Profile management
- Secure data storage

## Setup

1. Create a credentials folder:
```bash
mkdir credentials
```

2. Copy example files:
```bash
cp firebase_config.example.json credentials/firebase_config.json
cp serviceAccountKey.example.json credentials/serviceAccountKey.json
cp .env.example credentials/.env
```

3. Update the copied files with your Firebase credentials

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Run the application:
```bash
python run.py
```

## Security
- All sensitive data is stored securely
- Firebase Authentication for user management
- Real-time database with secure rules
- Token-based authentication
- Encrypted session storage

## Repository

- Main repository: https://github.com/danish-ahmad-ai/TaskMaster
- Issues: https://github.com/danish-ahmad-ai/TaskMaster/issues
- Documentation: https://github.com/danish-ahmad-ai/TaskMaster/wiki

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author
Danish Ahmad
- GitHub: [@danish-ahmad-ai](https://github.com/danish-ahmad-ai)
- Website: [danishahmad.xyz](https://danishahmad.xyz)
