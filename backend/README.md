# Sizzle Backend

The backend server for the Sizzle recipe assistant application. This service provides recipe generation, storage, and retrieval functionality.

## Features

- Recipe generation using GPT models
- Database integration for storing recipes, ingredients, and steps
- Image storage with Oracle Cloud Infrastructure (OCI) or local fallback
- RESTful API for frontend integration

## Setup

### Prerequisites

- Python 3.9 or higher
- PostgreSQL database (optional, can use Supabase)
- Oracle Cloud Infrastructure account (optional, for cloud storage)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/sizzle.git
cd sizzle/backend
```

2. Run the installation script:

```bash
python install.py
```

This will:
- Create a virtual environment
- Install required dependencies
- Set up necessary directories
- Create a template .env file

3. Configure your environment variables by editing the `.env` file.

### Manual Installation

If you prefer to set up manually:

1. Create a virtual environment:

```bash
python -m venv venv
```

2. Activate the virtual environment:

```bash
# On Windows
venv\\Scripts\\activate
# On macOS/Linux
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file with the required configuration.

## Running the Application

1. Start the backend server:

```bash
./run_sizzle.sh
```

Or manually:

```bash
source venv/bin/activate
python app.py
```

2. The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access the API documentation at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Environment Variables

The following environment variables can be configured in the `.env` file:

### Database Configuration
- `DB_HOST`: Database host (default: localhost)
- `DB_PORT`: Database port (default: 5432)
- `DB_USER`: Database username (default: postgres)
- `DB_PASSWORD`: Database password (default: postgres)
- `DB_NAME`: Database name (default: sizzle)
- `DATABASE_URL`: Full connection string (alternative to individual settings)

### API Configuration
- `API_PORT`: Port for the API server (default: 8000)
- `API_HOST`: Host for the API server (default: 0.0.0.0)
- `API_DEBUG`: Enable debug mode (default: False)
- `API_CORS_ORIGINS`: Allowed origins for CORS (default: *)

### OpenAI Configuration
- `OPENAI_API_KEY`: Your OpenAI API key
- `OPENAI_MODEL`: Model to use for recipe generation (default: gpt-4)
- `OPENAI_TIMEOUT`: Timeout for OpenAI API calls (default: 60)

### Oracle Cloud Configuration
- `OCI_BUCKET_NAME`: OCI bucket name for image storage
- `OCI_CONFIG_FILE`: Path to OCI config file (default: ~/.oci/config)
- `OCI_CONFIG_PROFILE`: OCI config profile (default: DEFAULT)
- `OCI_NAMESPACE`: OCI namespace

## Project Structure

```
backend/
├── app.py                # Main FastAPI application
├── config.py             # Configuration settings
├── database.py           # Database connection and operations
├── db_manager.py         # Database manager (legacy)
├── install.py            # Installation script
├── oci_storage.py        # Oracle Cloud storage integration
├── recipe_assistant.py   # Recipe generation with OpenAI
├── requirements.txt      # Python dependencies
├── run_sizzle.sh         # Startup script
├── setup_env.py          # Environment setup utilities
├── utils.py              # Utility functions
└── static/               # Static files directory
    ├── animations/       # Animation files
    └── images/           # Image files
```

## Development

### Code Style

This project follows PEP 8 guidelines for Python code style. 

### Testing

Run tests with:

```bash
pytest
```

## License

[MIT License](LICENSE)
