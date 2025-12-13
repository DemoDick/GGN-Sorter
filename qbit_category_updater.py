#!/usr/bin/env python3
"""
qBittorrent Category Updater for GazelleGames Torrents

This script finds torrents from GazelleGames, queries the API for game information,
and updates torrent categories to Manufacturer/Platform/Game (Year) format.
"""

import os
import requests
import json
import re
import time
import html
from urllib.parse import urlparse
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class QBittorrentClient:
    """Client for interacting with qBittorrent Web API"""
    
    def __init__(self, host, username, password):
        self.host = host.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.logged_in = False
        
    def login(self):
        """Authenticate with qBittorrent"""
        login_url = f"{self.host}/api/v2/auth/login"
        
        try:
            response = self.session.post(
                login_url,
                data={'username': self.username, 'password': self.password},
                timeout=10
            )
            
            if response.status_code == 200 and response.text == "Ok.":
                self.logged_in = True
                logger.info("Successfully logged in to qBittorrent")
                return True
            else:
                logger.error(f"Login failed: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Connection error during login: {e}")
            return False
    
    def get_torrents(self):
        """Get list of all torrents not tagged with 'GGn-Sorted'"""
        if not self.logged_in:
            logger.error("Not logged in to qBittorrent")
            return None
            
        response = self.session.get(f"{self.host}/api/v2/torrents/info", timeout=10)
        
        if response.status_code == 200:
            all_torrents = response.json()
            # Filter out torrents already tagged with "GGn-Sorted"
            filtered_torrents = []
            for torrent in all_torrents:
                tags = torrent.get('tags', '')
                if 'GGn-Sorted' not in tags:
                    filtered_torrents.append(torrent)
            
            logger.info(f"Retrieved {len(filtered_torrents)} unprocessed torrents (out of {len(all_torrents)} total)")
            return filtered_torrents
        else:
            logger.error(f"Failed to get torrents: {response.status_code}")
            return None
    
    def get_torrent_properties(self, hash):
        """Get detailed properties for a specific torrent"""
        if not self.logged_in:
            return None
            
        response = self.session.get(
            f"{self.host}/api/v2/torrents/properties",
            params={'hash': hash},
            timeout=10
        )
        
        return response.json() if response.status_code == 200 else None
    
    def get_torrent_trackers(self, hash):
        """Get tracker information for a specific torrent"""
        if not self.logged_in:
            return None
            
        response = self.session.get(
            f"{self.host}/api/v2/torrents/trackers",
            params={'hash': hash},
            timeout=10
        )
        
        return response.json() if response.status_code == 200 else None
    
    def get_categories(self):
        """Get all existing categories"""
        if not self.logged_in:
            return None
            
        response = self.session.get(
            f"{self.host}/api/v2/torrents/categories",
            timeout=10
        )
        
        return response.json() if response.status_code == 200 else None
    
    def create_category(self, category, save_path=""):
        """Create a new category"""
        if not self.logged_in:
            return False
            
        response = self.session.post(
            f"{self.host}/api/v2/torrents/createCategory",
            data={'category': category, 'savePath': save_path},
            timeout=10
        )
        
        return response.status_code == 200
    
    def set_torrent_category(self, hash, category):
        """Set category for a specific torrent, creating the category if it doesn't exist"""
        if not self.logged_in:
            return False
        
        # First, try to set the category
        response = self.session.post(
            f"{self.host}/api/v2/torrents/setCategory",
            data={'hashes': hash, 'category': category},
            timeout=10
        )
        
        # If category doesn't exist (409), create it and try again
        if response.status_code == 409:
            logger.info(f"Category '{category}' doesn't exist, creating it...")
            if self.create_category(category):
                logger.info(f"Successfully created category: {category}")
                # Try setting the category again
                response = self.session.post(
                    f"{self.host}/api/v2/torrents/setCategory",
                    data={'hashes': hash, 'category': category},
                    timeout=10
                )
                return response.status_code == 200
            else:
                logger.error(f"Failed to create category: {category}")
                return False
        
        return response.status_code == 200
    
    def add_torrent_tags(self, hash, tags):
        """Add tags to a specific torrent"""
        if not self.logged_in:
            return False
            
        response = self.session.post(
            f"{self.host}/api/v2/torrents/addTags",
            data={'hashes': hash, 'tags': tags},
            timeout=10
        )
        
        return response.status_code == 200


class GazelleGamesAPI:
    """Client for interacting with GazelleGames API"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://gazellegames.net/api.php"
        self.session = requests.Session()
        
    def get_torrent(self, torrent_hash):
        """Get torrent information by torrent hash"""
        # Add rate limiting delay
        time.sleep(2)
        try:
            # Ensure hash is uppercase as required by API
            torrent_hash = torrent_hash.upper()
            params = {'request': 'torrent', 'hash': torrent_hash}
            headers = {'X-API-Key': self.api_key, 'User-Agent': 'qBittorrent Category Updater v1.0'}
            
            logger.info(f"Querying GazelleGames API for torrent hash: {torrent_hash}")
            
            response = self.session.get(self.base_url, params=params, headers=headers, timeout=15)
            
            logger.info(f"API Response - Status: {response.status_code}, Content-Length: {len(response.text)}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('status') == 'success':
                        logger.info(f"Successfully retrieved data for torrent hash: {torrent_hash}")
                        return data.get('response', {})
                    else:
                        logger.error(f"API error for torrent hash {torrent_hash}: {data.get('error', 'Unknown error')}")
                        logger.error(f"Full API response: {response.text[:500]}")
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error for torrent hash {torrent_hash}: {e}")
                    logger.error(f"Response text: {response.text[:200]}")
            else:
                logger.error(f"HTTP error {response.status_code} for torrent hash {torrent_hash}")
                logger.error(f"Response headers: {dict(response.headers)}")
                logger.error(f"Response text: {response.text[:200]}")
                
        except Exception as e:
            logger.error(f"Exception querying API for torrent hash {torrent_hash}: {e}")
            
        return None


def is_gazelle_games_tracker(trackers):
    """Check if any of the trackers is from GazelleGames"""
    if not trackers:
        return False
    
    for tracker in trackers:
        url = tracker.get('url', '')
        if 'gazellegames.net' in url.lower():
            return True
    return False


def create_category(api_data, torrent_hash):
    """Create category string from API data: Manufacturer/Platform/GameName (Year)[/SubCategory]"""
    if not api_data:
        logger.debug("create_category: No API data provided")
        return None
    
    group = api_data.get('group', {})
    torrent_data = api_data.get('torrent', {})
    logger.debug(f"create_category: Group data keys: {list(group.keys())}")
    logger.debug(f"create_category: Torrent data keys: {list(torrent_data.keys())}")
    
    platform = group.get('platform', '').strip()
    game_name = group.get('name', 'Unknown Game')
    year = group.get('year', 'Unknown')
    
    logger.debug(f"create_category: platform='{platform}', game_name='{game_name}', year='{year}'")
    
    # Check for gameDOXType to determine subcategory
    subcategory = ""
    if torrent_data:
        game_dox_type = torrent_data.get('gameDOXType', '').strip()
        logger.debug(f"create_category: gameDOXType='{game_dox_type}'")
        if game_dox_type:
            if game_dox_type.lower() == 'update':
                subcategory = "/Update"
            elif game_dox_type.lower() == 'dlc':
                subcategory = "/DLC"
            elif game_dox_type.lower() == 'patch':
                subcategory = "/Patch"
            else:
                # For other types, use the gameDOXType directly
                clean_dox_type = re.sub(r'[<>:"/\\|?*]', '', game_dox_type)
                subcategory = f"/{clean_dox_type}"
        
        logger.debug(f"create_category: subcategory='{subcategory}'")
        clean_dox_type = re.sub(r'[<>:"/\\|?*]', '', game_dox_type)
        subcategory = f"/{clean_dox_type}"
        
        logger.debug(f"create_category: gameDOXType='{game_dox_type}', subcategory='{subcategory}'")
    
    # Map platforms to manufacturers
    manufacturer_map = {
        'windows': 'Microsoft', 'pc': 'Microsoft', 'xbox': 'Microsoft', 
        'xbox 360': 'Microsoft', 'xbox one': 'Microsoft', 'xbox series x': 'Microsoft',
        'playstation': 'Sony', 'playstation 2': 'Sony', 'playstation 3': 'Sony', 
        'playstation 4': 'Sony', 'playstation 5': 'Sony', 'playstation portable': 'Sony', 'playstation vita': 'Sony',
        'switch': 'Nintendo', 'nintendo 3ds': 'Nintendo', 'nintendo ds': 'Nintendo',
        'wii': 'Nintendo', 'wii u': 'Nintendo', 'gamecube': 'Nintendo',
        'linux': 'Linux', 'mac': 'Apple', 'macos': 'Apple', 'ios': 'Apple',
        'android': 'Google', 'steam deck': 'Valve'
    }
    
    platform_lower = platform.lower()
    manufacturer = 'Unknown'
    
    for platform_key, mfg in manufacturer_map.items():
        if platform_key in platform_lower:
            manufacturer = mfg
            break
    
    # Clean game name for filesystem compatibility
    # First decode HTML entities (like &#39; -> ')
    decoded_name = html.unescape(game_name)
    
    # Remove or replace problematic characters for filesystem paths
    # Remove HTML tags if any remain
    clean_name = re.sub(r'<[^>]+>', '', decoded_name)
    
    # Replace special filesystem characters with safe alternatives or remove them
    clean_name = re.sub(r'[<>:"/\\|?*]', '', clean_name)
    
    # Replace multiple spaces with single space and strip
    clean_name = re.sub(r'\s+', ' ', clean_name).strip()
    
    # Remove any remaining problematic characters but keep basic punctuation
    clean_name = re.sub(r'[^\w\s\-\.\(\)\[\]&\']', '', clean_name)
    
    category = f"Games/{manufacturer}/{platform}/{clean_name} ({year}){subcategory}"
    logger.debug(f"create_category: Created category: '{category}'")
    
    return category


def main():
    """Main function"""
    load_dotenv()
    
    # Get configuration
    qb_host = os.getenv('QB_HOST')
    qb_username = os.getenv('QB_USERNAME')
    qb_password = os.getenv('QB_PASSWORD')
    ggn_api_key = os.getenv('GGN_API_KEY')
    
    if not all([qb_host, qb_username, qb_password, ggn_api_key]):
        logger.error("Missing configuration. Check QB_HOST, QB_USERNAME, QB_PASSWORD, and GGN_API_KEY in .env file")
        return
    
    # Initialize clients
    qb_client = QBittorrentClient(qb_host, qb_username, qb_password)
    ggn_client = GazelleGamesAPI(ggn_api_key)
    
    # Test API key by making a simple request
    logger.info(f"Testing GazelleGames API with key: {ggn_api_key[:8]}...")
    # Skip API test since we need a valid hash - will test with actual torrents
    logger.info("API key configured - will test with actual torrent hashes")
    
    if not qb_client.login():
        logger.error("Failed to login to qBittorrent")
        return
    
    # Get existing categories
    categories = qb_client.get_categories()
    if categories:
        logger.info(f"Found {len(categories)} existing categories: {list(categories.keys())}")
    else:
        logger.info("No existing categories found")
    
    # Get torrents
    torrents = qb_client.get_torrents()
    if not torrents:
        logger.error("Failed to retrieve torrents")
        return
    
    updated_count = 0
    
    # Process each torrent
    for torrent in torrents:
        hash_id = torrent.get('hash')
        name = torrent.get('name', 'Unknown')
        current_category = torrent.get('category', '')
        
        # Skip torrents that already have categories assigned
        #if current_category:
        #    logger.debug(f"Skipping {name} - already has category: {current_category}")
        #    continue
        
        # Check if it's from GazelleGames
        trackers = qb_client.get_torrent_trackers(hash_id)
        
        if is_gazelle_games_tracker(trackers):
            logger.info(f"Processing GazelleGames torrent: {name}")
            
            # Query GazelleGames API using torrent hash
            time.sleep(1)  # Rate limiting - wait 1 second between API calls
            api_data = ggn_client.get_torrent(hash_id)
            if not api_data:
                logger.warning(f"  Failed to get API data for torrent hash: {hash_id}")
                continue
            
            # Create category
            try:
                category = create_category(api_data, hash_id)
                if not category:
                    logger.warning(f"  Failed to create category for: {name} (category is None or empty)")
                    # Log some API data for debugging
                    group = api_data.get('group', {})
                    logger.debug(f"  API group keys available: {list(group.keys())}")
                    if 'platform' in group:
                        logger.debug(f"  Platform: '{group['platform']}'")
                    if 'name' in group:
                        logger.debug(f"  Game name: '{group['name']}'")
                    continue
                
                logger.info(f"  Created category: {category}")
                
                # Update torrent category (will create category if it doesn't exist)
                if qb_client.set_torrent_category(hash_id, category):
                    logger.info(f"  Successfully updated category to: {category}")
                    
                    # Add GGn-Sorted tag to mark as processed
                    if qb_client.add_torrent_tags(hash_id, "GGn-Sorted"):
                        logger.debug(f"  Added 'GGn-Sorted' tag to: {name}")
                    else:
                        logger.warning(f"  Failed to add 'GGn-Sorted' tag to: {name}")
                    
                    updated_count += 1
                else:
                    logger.error(f"  Failed to update category for: {name} - qBittorrent API call failed")
            except Exception as e:
                logger.error(f"  Exception creating/setting category for {name}: {e}")
                logger.debug(f"  API data keys: {list(api_data.keys()) if api_data else 'None'}")
    
    logger.info(f"Successfully updated {updated_count} torrent categories")


if __name__ == "__main__":
    main()
