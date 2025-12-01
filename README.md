# qBittorrent Category Updater for GazelleGames

This script connects to a qBittorrent instance and automatically updates torrent categories for GazelleGames torrents using the GazelleGames API.

## Features

- Connects to qBittorrent Web API
- Identifies torrents from GazelleGames tracker
- Queries GazelleGames API for game information using torrent hash
- Creates hierarchical categories in format: Manufacturer/Platform/GameName (Year)
- Automatically creates categories if they don't exist
- HTML entity decoding for clean category names
- Comprehensive logging and error handling
- Rate limiting to respect API limits

## Prerequisites

- Python 3.7 or higher
- qBittorrent with Web UI enabled
- Access to qBittorrent instance (local or remote)
- GazelleGames account with API access
- GazelleGames API key with appropriate permissions

## Installation

1. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure your credentials in the `.env` file:
   ```
   QB_HOST=https://your-qbittorrent-url:port/
   QB_USERNAME=your_username
   QB_PASSWORD=your_password
   GGN_API_KEY=your_gazellegames_api_key
   ```

## Usage

Run the script:
```bash
python qbit_category_updater.py
```

## Output

The script will:

1. Connect to your qBittorrent instance
2. Scan all torrents for GazelleGames tracker
3. Skip torrents that already have categories assigned
4. Query GazelleGames API using torrent hash
5. Extract game information (name, platform, year, etc.)
6. Create hierarchical categories: Manufacturer/Platform/GameName (Year)
7. Automatically create categories in qBittorrent if they don't exist
8. Update torrent categories with proper organization

Example categories created:
- `Games/Microsoft/Windows/The Elder Scrolls V Skyrim (2011)`
- `Games/Sony/PlayStation 4/God of War (2018)`
- `Games/Nintendo/Nintendo Switch/Super Mario Odyssey (2017)`

## Configuration

The script reads configuration from environment variables:

- `QB_HOST`: qBittorrent Web UI URL (e.g., `http://localhost:8080/` or `https://your-server:8086/`)
- `QB_USERNAME`: qBittorrent Web UI username
- `QB_PASSWORD`: qBittorrent Web UI password
- `GGN_API_KEY`: GazelleGames API key with appropriate permissions

### Getting GazelleGames API Key

1. Log into your GazelleGames account
2. Go to your profile settings
3. Navigate to the API Keys section
4. Create a new API key with required permissions:
   - User: For basic user info
   - Any additional permissions needed for torrent data access
5. Copy the generated API key to your `.env` file

## qBittorrent Setup

Make sure qBittorrent Web UI is enabled:

1. Open qBittorrent
2. Go to Tools → Options → Web UI
3. Enable "Web User Interface (Remote control)"
4. Set username and password
5. Note the port (default is 8080)

## Troubleshooting

- **Connection refused**: Check if qBittorrent Web UI is enabled and accessible
- **Login failed**: Verify username and password in `.env` file
- **SSL errors**: If using HTTPS, ensure certificates are valid or disable SSL verification for testing
- **No torrents found**: Check if you have any torrents from GazelleGames tracker
- **API errors**: Verify your GazelleGames API key is valid and has proper permissions
- **Rate limiting**: The script includes 1-second delays between API calls to respect limits
- **Category creation fails**: Ensure qBittorrent user has permission to create categories
- **HTML entities in names**: The script automatically decodes HTML entities like `&#39;` to proper characters

## Category Structure

The script creates organized categories in the format:
```
Manufacturer/Platform/GameName (Year)
```

**Supported Manufacturers:**
- Microsoft (Windows, PC, Xbox, Xbox 360, Xbox One, Xbox Series X)
- Sony (PlayStation, PlayStation 2, PlayStation 3, PlayStation 4, PlayStation 5, PSP, PS Vita)
- Nintendo (Nintendo Switch, Nintendo 3DS, Nintendo DS, Nintendo Wii, Nintendo Wii U, Nintendo GameCube)
- Apple (Mac, macOS, iOS)
- Google (Android)

**Features:**
- Automatic HTML entity decoding (e.g., `&#39;` becomes `'`)
- Special character removal for filesystem compatibility
- Hierarchical organization for easy browsing
- Platform-specific manufacturer mapping
