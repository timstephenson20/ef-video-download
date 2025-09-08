#!/usr/bin/env python3
"""
Video Download Tool for EazyFlicks
Extracts and downloads .mp4 video files from collection landing pages
"""

# Configuration
# EazyFlicks URL for collection you need to download from
startURL = "https://eazyflicks.com/App/YOURACCOUNT/your-collection-to-download/"
 
 # destination folder for downloaded videos
outputPath = "mediafiles"

#stop editing here :)




import requests
import re
import os
import sys
import time
from urllib.parse import urlparse, urljoin
from pathlib import Path
import hashlib
from typing import List, Set, Tuple, Optional



class VideoDownloader:
    def __init__(self, start_url: str, output_dir: str, skip_summary: bool = False):
        self.start_url = start_url
        self.output_dir = Path(output_dir)
        self.skip_summary = skip_summary
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Statistics
        self.total_found = 0
        self.total_downloaded = 0
        self.failed_downloads = []
        
    def fetch_page(self, url: str) -> Optional[str]:
        """Fetch the HTML content of a page with error handling and retries"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"Fetching page: {url} (attempt {attempt + 1}/{max_retries})")
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                print(f"Error fetching page (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    print(f"Failed to fetch page after {max_retries} attempts")
                    return None
    
    def extract_video_urls(self, html_content: str) -> Set[str]:
        """Extract video URLs from dropdown-content blocks containing myfunction() calls"""
        video_urls = set()
        
        # Find all dropdown-content divs
        dropdown_pattern = r'<div class="dropdown-content"[^>]*>(.*?)</div>'
        dropdown_matches = re.findall(dropdown_pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        print(f"Found {len(dropdown_matches)} dropdown-content blocks")
        
        # Extract myfunction URLs from each dropdown block
        myfunction_pattern = r"myfunction\(['\"]([^'\"]+)['\"]"
        
        for dropdown_content in dropdown_matches:
            urls_in_block = re.findall(myfunction_pattern, dropdown_content, re.IGNORECASE)
            for url in urls_in_block:
                if url.endswith('.mp4'):
                    video_urls.add(url)
                    print(f"Found video URL: {url}")
        
        # Also check dropdown-content1 blocks (alternative class name found in HTML)
        dropdown1_pattern = r'<div class="dropdown-content1"[^>]*>(.*?)</div>'
        dropdown1_matches = re.findall(dropdown1_pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        print(f"Found {len(dropdown1_matches)} dropdown-content1 blocks")
        
        for dropdown_content in dropdown1_matches:
            urls_in_block = re.findall(myfunction_pattern, dropdown_content, re.IGNORECASE)
            for url in urls_in_block:
                if url.endswith('.mp4'):
                    video_urls.add(url)
                    print(f"Found video URL: {url}")
        
        self.total_found = len(video_urls)
        print(f"\nTotal unique video URLs found: {self.total_found}")
        return video_urls
    
    def get_file_size(self, url: str) -> Optional[int]:
        """Get the size of a remote file without downloading it"""
        try:
            response = self.session.head(url, timeout=30)
            if response.status_code == 200:
                content_length = response.headers.get('content-length')
                if content_length:
                    return int(content_length)
        except requests.RequestException as e:
            print(f"Error getting file size for {url}: {e}")
        return None
    
    def clean_filename(self, filename: str) -> str:
        """Clean filename by removing timestamp numbers and replacing dashes with spaces"""
        # Remove .mp4 extension temporarily
        name_without_ext = filename.replace('.mp4', '')
        
        # Remove the two sets of numbers at the end (e.g., "-1652393410-9")
        # Pattern: remove -[numbers]-[numbers] from the end
        import re
        cleaned_name = re.sub(r'-\d+-\d+$', '', name_without_ext)
        
        # Replace remaining dashes with spaces
        cleaned_name = cleaned_name.replace('-', ' ')
        
        # Add back the .mp4 extension
        return cleaned_name + '.mp4'
    
    def download_video(self, url: str) -> bool:
        """Download a single video file with size verification and progress tracking"""
        try:
            # Extract filename from URL
            parsed_url = urlparse(url)
            original_filename = os.path.basename(parsed_url.path)
            if not original_filename.endswith('.mp4'):
                original_filename += '.mp4'
            
            # Clean the filename
            filename = self.clean_filename(original_filename)

            # Get expected file size
            expected_size = self.get_file_size(url)

            # Find available filename to avoid overwriting files with different sizes
            base_name = filename[:-4]  # Remove .mp4 extension
            ext = '.mp4'
            counter = 1
            while True:
                if counter == 1:
                    candidate_filename = filename
                else:
                    candidate_filename = f"{base_name} ({counter}){ext}"
                candidate_path = self.output_dir / candidate_filename
                if not candidate_path.exists():
                    file_path = candidate_path
                    break
                else:
                    existing_size = candidate_path.stat().st_size
                    if expected_size and existing_size == expected_size:
                        print(f"File already exists with matching size: {candidate_filename}")
                        return True
                    else:
                        counter += 1
            if expected_size:
                print(f"Downloading {filename} ({expected_size:,} bytes)...")
            else:
                print(f"Downloading {filename} (size unknown)...")
            
            # Download with streaming and progress tracking
            response = self.session.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            downloaded_size = 0
            chunk_size = 8192  # 8KB chunks
            last_progress = -1
            start_time = time.time()
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # Update progress bar every 5% for cleaner output
                        if expected_size:
                            progress = (downloaded_size / expected_size) * 100
                            # Update every 5% or when complete
                            if progress - last_progress >= 5 or downloaded_size >= expected_size:
                                # Calculate transfer rate
                                elapsed_time = time.time() - start_time
                                if elapsed_time > 0:
                                    bytes_per_sec = downloaded_size / elapsed_time
                                    mbits_per_sec = (bytes_per_sec * 8) / (1024 * 1024)  # Convert to Mbit/s
                                    rate_str = f"{mbits_per_sec:.1f} Mbit/s"
                                else:
                                    rate_str = "calculating..."
                                
                                # Create visual progress bar
                                bar_length = 30  # Shorter to fit rate info
                                filled_length = int(bar_length * progress / 100)
                                bar = '█' * filled_length + '░' * (bar_length - filled_length)
                                
                                # Format file size
                                if expected_size > 1024 * 1024 * 1024:  # GB
                                    size_str = f"{downloaded_size/(1024*1024*1024):.1f}/{expected_size/(1024*1024*1024):.1f} GB"
                                elif expected_size > 1024 * 1024:  # MB
                                    size_str = f"{downloaded_size/(1024*1024):.1f}/{expected_size/(1024*1024):.1f} MB"
                                else:  # KB or bytes
                                    size_str = f"{downloaded_size:,}/{expected_size:,} bytes"
                                
                                print(f"\r[{bar}] {progress:.1f}% ({size_str}) @ {rate_str}", end='', flush=True)
                                last_progress = progress
                        else:
                            # For unknown size, show downloaded amount every 50MB
                            if downloaded_size % (50 * 1024 * 1024) == 0 or downloaded_size < chunk_size:
                                elapsed_time = time.time() - start_time
                                if elapsed_time > 0:
                                    bytes_per_sec = downloaded_size / elapsed_time
                                    mbits_per_sec = (bytes_per_sec * 8) / (1024 * 1024)
                                    rate_str = f"@ {mbits_per_sec:.1f} Mbit/s"
                                else:
                                    rate_str = ""
                                
                                if downloaded_size > 1024 * 1024:
                                    print(f"\rDownloaded: {downloaded_size/(1024*1024):.1f} MB {rate_str}", end='', flush=True)
                                else:
                                    print(f"\rDownloaded: {downloaded_size:,} bytes {rate_str}", end='', flush=True)
            
            # Print newline after progress bar completion
            print()
            
            # Verify file size
            actual_size = file_path.stat().st_size
            if expected_size and actual_size != expected_size:
                print(f"ERROR: Size mismatch for {filename}")
                print(f"Expected: {expected_size:,} bytes, Got: {actual_size:,} bytes")
                file_path.unlink()  # Delete incomplete file
                return False
            
            print(f"Successfully downloaded: {filename} ({actual_size:,} bytes)")
            return True
            
        except requests.RequestException as e:
            print(f"Network error downloading {url}: {e}")
            return False
        except IOError as e:
            print(f"File I/O error downloading {url}: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error downloading {url}: {e}")
            return False
    
    def download_all_videos(self, video_urls: Set[str]) -> None:
        """Download all video files with retry logic"""
        if not video_urls:
            print("No video URLs to download")
            return
        
        print(f"\nStarting download of {len(video_urls)} videos...")
        print(f"Output directory: {self.output_dir.absolute()}")
        print("-" * 60)
        
        for i, url in enumerate(sorted(video_urls), 1):
            print(f"\n[{i}/{len(video_urls)}] Processing: {url}")
            
            # Retry logic for each download
            max_retries = 3
            success = False
            
            for attempt in range(max_retries):
                if attempt > 0:
                    print(f"Retry attempt {attempt + 1}/{max_retries}")
                    time.sleep(2 ** attempt)  # Exponential backoff
                
                success = self.download_video(url)
                if success:
                    self.total_downloaded += 1
                    break
            
            if not success:
                self.failed_downloads.append(url)
                print(f"FAILED: Could not download {url} after {max_retries} attempts")
    
    def print_summary(self) -> None:
        """Print download summary statistics"""
        print("\n" + "=" * 60)
        print("DOWNLOAD SUMMARY")
        print("=" * 60)
        print(f"Total URLs found: {self.total_found}")
        print(f"Successfully downloaded: {self.total_downloaded}")
        print(f"Failed downloads: {len(self.failed_downloads)}")
        
        if self.failed_downloads:
            print("\nFailed URLs:")
            for url in self.failed_downloads:
                print(f"  - {url}")
        
        print(f"\nFiles saved to: {self.output_dir.absolute()}")
        
        # List downloaded files
        if self.output_dir.exists():
            downloaded_files = list(self.output_dir.glob("*.mp4"))
            if downloaded_files:
                print(f"\nDownloaded files ({len(downloaded_files)}):")
                total_size = 0
                for file_path in sorted(downloaded_files):
                    size = file_path.stat().st_size
                    total_size += size
                    print(f"  - {file_path.name} ({size:,} bytes)")
                print(f"\nTotal size: {total_size:,} bytes ({total_size / (1024*1024):.1f} MB)")

    @staticmethod
    def print_final_summary(total_found: int, total_downloaded: int, failed_downloads: List[str], output_dir: Path) -> None:
        """Print final download summary statistics for multiple URLs"""
        print("\n" + "=" * 60)
        print("FINAL DOWNLOAD SUMMARY")
        print("=" * 60)
        print(f"Total URLs found across all galleries: {total_found}")
        print(f"Successfully downloaded: {total_downloaded}")
        print(f"Failed downloads: {len(failed_downloads)}")

        if failed_downloads:
            print("\nFailed URLs:")
            for url in failed_downloads:
                print(f"  - {url}")

        print(f"\nFiles saved to: {output_dir.absolute()}")

        # List downloaded files
        if output_dir.exists():
            downloaded_files = list(output_dir.glob("*.mp4"))
            if downloaded_files:
                print(f"\nDownloaded files ({len(downloaded_files)}):")
                total_size = 0
                for file_path in sorted(downloaded_files):
                    size = file_path.stat().st_size
                    total_size += size
                    print(f"  - {file_path.name} ({size:,} bytes)")
                print(f"\nTotal size: {total_size:,} bytes ({total_size / (1024*1024):.1f} MB)")

    def run(self) -> None:
        """Main execution method"""
        print(f"EazyFlicks Video Downloader - Processing: {self.start_url}")
        print("=" * 40)

        # Fetch the start page
        html_content = self.fetch_page(self.start_url)
        if not html_content:
            print("ERROR: Could not fetch the start page")
            return

        # Extract video URLs
        video_urls = self.extract_video_urls(html_content)
        if not video_urls:
            print("ERROR: No video URLs found")
            return

        # Download all videos
        self.download_all_videos(video_urls)

        # Print summary if not skipped
        if not self.skip_summary:
            self.print_summary()

def main():
    """Main entry point"""
    try:
        # Parse startURL: if contains ';', split into list, else single URL
        if ';' in startURL:
            urls = [u.strip() for u in startURL.split(';') if u.strip()]
        else:
            urls = [startURL]

        print(f"EazyFlicks Video Downloader")
        print(f"Processing {len(urls)} gallery URL(s)")
        print("=" * 40)

        # Initialize accumulators
        total_found = 0
        total_downloaded = 0
        all_failed = []

        # Process each URL
        for i, url in enumerate(urls, 1):
            print(f"\n{'='*60}")
            print(f"GALLERY {i}/{len(urls)}: {url}")
            print(f"{'='*60}")

            downloader = VideoDownloader(url, outputPath, skip_summary=True)
            downloader.run()

            # Accumulate statistics
            total_found += downloader.total_found
            total_downloaded += downloader.total_downloaded
            all_failed.extend(downloader.failed_downloads)

        # Print final summary
        output_dir = Path(outputPath)
        VideoDownloader.print_final_summary(total_found, total_downloaded, all_failed, output_dir)

    except KeyboardInterrupt:
        print("\n\nDownload interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
