#!/usr/bin/env bash
# Exit on error
set -o errexit

# Update Pip
pip install --upgrade pip
pip install -r requirements.txt

# Create bin folder
mkdir -p bin

# Download FFmpeg (Static Build for Linux)
echo "Downloading FFmpeg..."
curl -L https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz -o ffmpeg.tar.xz

# Extract
tar -xf ffmpeg.tar.xz --strip-components=1 -C bin/

# Cleanup
rm ffmpeg.tar.xz
echo "FFmpeg Installed Successfully!"