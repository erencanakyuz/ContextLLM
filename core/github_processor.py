#!/usr/bin/env python3
"""
GitHub Repository Processor
Handles GitHub repository fetching and processing via API.
"""

import os
import requests
import re
import time
from typing import Dict, List, Optional, Tuple, Set, Union, TypedDict
from urllib.parse import urlparse, quote

class RateLimitStatus(TypedDict):
    remaining: int
    limit: int
    reset: int
    reset_time: str
    session_duration: int

class GitHubProcessor:
    def __init__(self):
        self.api_base = "https://api.github.com"
        self.rate_limit_remaining = 60  # Anonymous limit
        self.rate_limit_reset = 0
        self.session = requests.Session()
        
        # Internal rate limiting per user session
        self.user_request_count = 0
        self.user_session_start = time.time()
        
        # Check for optional user token
        self.user_token = os.getenv('GITHUB_TOKEN', '').strip()
        
        # Set headers
        headers = {
            'User-Agent': 'ContextLLM/1.0 (Open Source Code Analysis Tool)',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Add auth if user provided token
        if self.user_token:
            headers['Authorization'] = f'token {self.user_token}'
            self.user_request_limit = 5000  # Authenticated limit
            self.is_authenticated = True
        else:
            # Pure anonymous mode - use GitHub's full anonymous limit
            self.user_request_limit = 60  # GitHub's anonymous limit per hour
            self.is_authenticated = False
        
        self.session.headers.update(headers)
        
        # Code file extensions to download
        self.code_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.hpp',
            '.cs', '.php', '.rb', '.go', '.rs', '.kt', '.swift', '.scala', '.clj',
            '.html', '.css', '.scss', '.sass', '.less', '.vue', '.svelte',
            '.json', '.xml', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
            '.sql', '.sh', '.bat', '.ps1', '.dockerfile', '.md', '.txt', '.rst',
            '.gradle', '.pom', '.gemfile', '.podfile', '.makefile', '.cmake'
        }
        
        # Always exclude these patterns
        self.exclude_patterns = {
            'node_modules', '__pycache__', '.git', '.vscode', '.idea', 
            'dist', 'build', 'target', 'bin', 'obj', '.next', '.nuxt',
            'coverage', '.coverage', '.pytest_cache', '.mypy_cache',
            'vendor', 'packages', '.gradle', '.mvn'
        }
        
        # Binary file extensions to skip
        self.binary_extensions = {
            '.exe', '.dll', '.so', '.dylib', '.a', '.lib', '.o', '.obj',
            '.zip', '.tar', '.gz', '.rar', '.7z', '.bz2', '.xz',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.ico',
            '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.mkv', '.flv',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.woff', '.woff2', '.ttf', '.otf', '.eot',
            '.db', '.sqlite', '.mdb', '.accdb',
            '.pyc', '.pyo', '.pyd', '.class', '.jar', '.war'
        }
    
    def parse_github_url(self, url: str) -> Optional[Dict[str, str]]:
        """
        Parse GitHub URL and extract owner, repo, and branch info
        Supports various GitHub URL formats
        """
        try:
            # Clean URL
            url = url.strip().rstrip('/')
            
            # Remove protocol if present
            if url.startswith('http://') or url.startswith('https://'):
                url = urlparse(url).path.lstrip('/')
            
            # Remove github.com if present
            if url.startswith('github.com/'):
                url = url[11:]
            
            # Parse different URL formats
            patterns = [
                r'^([^/]+)/([^/]+)/?$',  # user/repo
                r'^([^/]+)/([^/]+)/tree/([^/]+)/?.*$',  # user/repo/tree/branch
                r'^([^/]+)/([^/]+)/blob/([^/]+)/.*$',  # user/repo/blob/branch/file
                r'^([^/]+)/([^/]+)/commits/([^/]+)/?.*$',  # user/repo/commits/branch
            ]
            
            for pattern in patterns:
                match = re.match(pattern, url)
                if match:
                    owner = match.group(1)
                    repo = match.group(2)
                    branch = match.group(3) if len(match.groups()) > 2 else 'main'
                    
                    return {
                        'owner': owner,
                        'repo': repo,
                        'branch': branch,
                        'url': f"https://github.com/{owner}/{repo}"
                    }
            
            return None
            
        except Exception as e:
            print(f"Error parsing GitHub URL: {e}")
            return None
    
    def check_user_rate_limit(self) -> RateLimitStatus:
        """Check user session rate limit status"""
        current_time = time.time()
        session_duration = current_time - self.user_session_start
        
        # Reset counter if more than 1 hour passed
        if session_duration > 3600:  # 1 hour
            self.user_request_count = 0
            self.user_session_start = current_time
            session_duration = 0
        
        remaining = max(0, self.user_request_limit - self.user_request_count)
        reset_time = self.user_session_start + 3600  # 1 hour from session start
        
        return {
            'remaining': remaining,
            'limit': self.user_request_limit,
            'reset': int(reset_time),
            'reset_time': time.strftime('%H:%M:%S', time.localtime(reset_time)),
            'session_duration': int(session_duration)
        }
    
    def can_make_request(self) -> bool:
        """Check if user can make another request"""
        status = self.check_user_rate_limit()
        return status['remaining'] > 0
    
    def verify_repository(self, owner: str, repo: str) -> Tuple[bool, str]:
        """Verify if repository exists and is accessible"""
        try:
            # Check user rate limit first
            if not self.can_make_request():
                status = self.check_user_rate_limit()
                return False, f"⚠️ Session limit reached ({self.user_request_limit}/hour). Resets at {status['reset_time']}"
            
            # Make request
            response = self.session.get(f"{self.api_base}/repos/{owner}/{repo}")
            self.user_request_count += 1  # Track request
            
            if response.status_code == 200:
                repo_data = response.json()
                return True, f"✅ Repository found: {repo_data.get('full_name', 'Unknown')}"
            elif response.status_code == 404:
                return False, "❌ Repository not found or private"
            elif response.status_code == 403:
                return False, "❌ GitHub rate limit exceeded globally. Try again later."
            else:
                return False, f"❌ Error: {response.status_code}"
                
        except Exception as e:
            return False, f"❌ Connection error: {str(e)}"
    
    def get_repository_tree(self, owner: str, repo: str, branch: str = 'main') -> Tuple[List[Dict], Set[str], str]:
        """
        Get repository file tree using GitHub API
        Returns: (files_list, extensions_set, status_message)
        """
        try:
            # Check user rate limit first
            if not self.can_make_request():
                status = self.check_user_rate_limit()
                return [], set(), f"⚠️ Session limit reached ({self.user_request_limit}/hour). Resets at {status['reset_time']}"
            
            # First get the default branch if 'main' doesn't exist
            if branch == 'main':
                repo_response = self.session.get(f"{self.api_base}/repos/{owner}/{repo}")
                if repo_response.status_code == 200:
                    repo_data = repo_response.json()
                    branch = repo_data.get('default_branch', 'main')
            
            # Get repository tree
            tree_url = f"{self.api_base}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
            response = self.session.get(tree_url)
            self.user_request_count += 1  # Track request
            
            if response.status_code == 404:
                # Check if we can make another request
                if not self.can_make_request():
                    status = self.check_user_rate_limit()
                    return [], set(), f"⚠️ Session limit reached. Resets at {status['reset_time']}"
                
                # Try with 'master' branch
                tree_url = f"{self.api_base}/repos/{owner}/{repo}/git/trees/master?recursive=1"
                response = self.session.get(tree_url)
                self.user_request_count += 1  # Track request
                branch = 'master'
            
            if response.status_code != 200:
                if response.status_code == 403:
                    return [], set(), "⚠️ Rate limit exceeded"
                return [], set(), f"❌ Failed to fetch repository tree: {response.status_code}"
            
            tree_data = response.json()
            files_list = []
            extensions_set = set()
            
            for item in tree_data.get('tree', []):
                if item['type'] == 'blob':  # It's a file
                    file_path = item['path']
                    
                    # Skip excluded patterns
                    if self.should_exclude_path(file_path):
                        continue
                    
                    # Get file extension
                    file_ext = self.get_file_extension(file_path)
                    
                    # Skip binary files
                    if file_ext in self.binary_extensions:
                        continue
                    
                    # Only include code files
                    if file_ext in self.code_extensions or file_ext == '':
                        files_list.append({
                            'path': file_path,
                            'relative_path': file_path,
                            'extension': file_ext,
                            'download_url': f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{quote(file_path)}",
                            'size': item.get('size', 0)
                        })
                        
                        if file_ext:
                            extensions_set.add(file_ext)
            
            status_msg = f"✅ Found {len(files_list)} code files in {owner}/{repo}:{branch}"
            remaining = self.check_user_rate_limit()['remaining']
            auth_type = "Authenticated" if self.is_authenticated else "Anonymous"
            status_msg += f" ({auth_type}: {remaining}/{self.user_request_limit} requests left)"
            return files_list, extensions_set, status_msg
            
        except Exception as e:
            return [], set(), f"❌ Error fetching repository: {str(e)}"
    
    def download_file_content(self, download_url: str) -> Optional[str]:
        """Download file content from GitHub raw URL"""
        try:
            response = self.session.get(download_url, timeout=30)
            
            if response.status_code == 200:
                # Update rate limit
                self.rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', self.rate_limit_remaining - 1))
                
                # Try to decode as UTF-8
                try:
                    return response.text
                except UnicodeDecodeError:
                    # Skip binary files
                    return None
            else:
                print(f"Failed to download {download_url}: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error downloading {download_url}: {e}")
            return None
    
    def should_exclude_path(self, path: str) -> bool:
        """Check if file path should be excluded"""
        path_lower = path.lower()
        path_parts = path.split('/')
        
        # Check exclude patterns
        for pattern in self.exclude_patterns:
            if pattern in path_parts or pattern in path_lower:
                return True
        
        # Skip hidden files and directories
        for part in path_parts:
            if part.startswith('.') and part not in {'.gitignore', '.env.example', '.dockerignore'}:
                return True
        
        return False
    
    def get_file_extension(self, file_path: str) -> str:
        """Get file extension from path"""
        if '.' not in file_path:
            return ''
        
        ext = '.' + file_path.split('.')[-1].lower()
        
        # Special cases
        if file_path.lower().endswith('.dockerfile'):
            return '.dockerfile'
        elif file_path.lower() in ['makefile', 'gemfile', 'podfile']:
            return f'.{file_path.lower()}'
        
        return ext
    
    def get_rate_limit_status(self) -> str:
        """Get formatted rate limit status"""
        status = self.check_user_rate_limit()
        remaining = status['remaining']
        limit = status['limit']
        
        # Show authentication status
        auth_indicator = "🔑 Authenticated" if self.is_authenticated else "👤 Anonymous"
        
        if self.is_authenticated:
            # Authenticated users - higher limits
            if remaining > 100:
                return f"🟢 {auth_indicator}: {remaining:,}/{limit:,} requests left"
            elif remaining > 50:
                return f"🟡 {auth_indicator}: {remaining:,}/{limit:,} requests left"
            elif remaining > 0:
                return f"🟠 {auth_indicator}: {remaining:,}/{limit:,} requests left"
            else:
                return f"🔴 {auth_indicator}: Rate limit reached. Resets at {status['reset_time']}"
        else:
            # Anonymous users - hourly limits
            if remaining > 45:
                return f"🟢 {auth_indicator}: {remaining}/{limit} requests/hour"
            elif remaining > 20:
                return f"🟡 {auth_indicator}: {remaining}/{limit} requests/hour"
            elif remaining > 0:
                return f"🟠 {auth_indicator}: {remaining}/{limit} requests/hour"
            else:
                return f"🔴 {auth_indicator}: Rate limit reached. Resets at {status['reset_time']}"