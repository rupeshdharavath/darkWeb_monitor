"""
File Analyzer Module
Performs forensic analysis on downloaded files using binwalk, exiftool, strings, and ClamAV
"""

import subprocess
import os
from app.utils import logger

# Configuration
ANALYSIS_TIMEOUT = 30  # Subprocess timeout in seconds
BINWALK_PATH = "/usr/bin/binwalk"
EXIFTOOL_PATH = "/usr/bin/exiftool"
CLAMSCAN_PATH = "/usr/bin/clamscan"


def run_command(command, timeout=ANALYSIS_TIMEOUT):
    """
    Run shell command with timeout protection
    
    Args:
        command: List of command parts
        timeout: Timeout in seconds
    
    Returns:
        dict: {"success": bool, "output": str, "error": str}
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }
    
    except subprocess.TimeoutExpired:
        logger.error(f"⏱️ Command timeout after {timeout}s: {' '.join(command)}")
        return {
            "success": False,
            "output": "",
            "error": f"Command timeout after {timeout} seconds"
        }
    
    except Exception as e:
        logger.error(f"❌ Error running command: {e}")
        return {
            "success": False,
            "output": "",
            "error": str(e)
        }


def analyze_with_strings(filepath):
    """Extract readable strings from binary file"""
    logger.info(f"🔍 Running strings analysis on {os.path.basename(filepath)}")
    
    result = run_command(
        ["strings", filepath],
        timeout=ANALYSIS_TIMEOUT
    )
    
    if result["success"]:
        strings_output = result["output"].split("\n")
        # Filter to meaningful strings (length > 7)
        filtered_strings = [s for s in strings_output if len(s) > 7]
        return {
            "success": True,
            "strings_found": len(filtered_strings),
            "sample_strings": filtered_strings[:20]  # First 20 strings
        }
    else:
        return {
            "success": False,
            "error": result["error"]
        }


def analyze_with_binwalk(filepath):
    """Perform binwalk signature analysis"""
    logger.info(f"🔎 Running binwalk analysis on {os.path.basename(filepath)}")
    
    if not os.path.exists(BINWALK_PATH):
        logger.warning("⚠️ binwalk not found, skipping binwalk analysis")
        return {
            "success": False,
            "error": "binwalk not installed"
        }
    
    result = run_command(
        [BINWALK_PATH, "-B", filepath],
        timeout=ANALYSIS_TIMEOUT
    )
    
    if result["success"]:
        # Parse binwalk output for signatures
        signatures = []
        for line in result["output"].split("\n"):
            if line.strip() and not line.startswith("DECIMAL"):
                signatures.append(line.strip())
        
        return {
            "success": True,
            "signatures": signatures[:10]  # First 10 signatures
        }
    else:
        return {
            "success": False,
            "output": result["output"],
            "error": result["error"]
        }


def analyze_with_exiftool(filepath):
    """Extract metadata using exiftool"""
    logger.info(f"📋 Running exiftool metadata extraction on {os.path.basename(filepath)}")
    
    if not os.path.exists(EXIFTOOL_PATH):
        logger.warning("⚠️ exiftool not found, skipping exiftool analysis")
        return {
            "success": False,
            "error": "exiftool not installed"
        }
    
    result = run_command(
        [EXIFTOOL_PATH, "-json", filepath],
        timeout=ANALYSIS_TIMEOUT
    )
    
    if result["success"]:
        try:
            import json
            metadata = json.loads(result["output"])
            if isinstance(metadata, list) and len(metadata) > 0:
                meta_dict = metadata[0]
                
                # List of common metadata fields to extract
                important_fields = [
                    # File info
                    "FileName", "FileSize", "FileType", "FileTypeExtension", "MimeType",
                    "FileModifyDate", "FileCreateDate", "FileAccessDate",
                    # Document properties
                    "Title", "Subject", "Author", "Creator", "Producer", 
                    "Keywords", "Comments", "Description",
                    # Image properties
                    "ImageWidth", "ImageHeight", "XResolution", "YResolution",
                    "ColorSpace", "ExifImageHeight", "ExifImageWidth",
                    # Camera/Device info
                    "Make", "Model", "Software", "Firmware", "DeviceModel",
                    # Image metadata
                    "DateTime", "DateTimeOriginal", "DateTimeDigitized", "CreateDate", "ModifyDate",
                    "GPSLatitude", "GPSLongitude", "GPSAltitude", "GPSDateStamp",
                    # Archive/Executable
                    "CompressedSize", "UncompressedSize", "CompressionRatio",
                    "EntryCount", "CodePage", "CharSet",
                    # Video
                    "Duration", "FrameRate", "TrackCreateDate", "TrackModifyDate",
                    # Audio
                    "AudioChannels", "AudioSampleRate", "BitRate",
                    # Web/URL
                    "URL", "TargetFrame", "Subject"
                ]
                
                extracted_metadata = {}
                for field in important_fields:
                    if field in meta_dict:
                        extracted_metadata[field] = meta_dict[field]
                
                # If no standard fields found, get all non-internal fields
                if not extracted_metadata:
                    extracted_metadata = {
                        k: v for k, v in meta_dict.items()
                        if not k.startswith("Source") and not k.startswith("UserComment")
                    }
                
                logger.info(f"✅ Extracted {len(extracted_metadata)} metadata fields")
                
                return {
                    "success": True,
                    "metadata": extracted_metadata,
                    "field_count": len(extracted_metadata)
                }
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️ Error parsing exiftool JSON: {e}")
            # Fallback to text parsing
            return parse_exiftool_text(result["output"])
        except Exception as e:
            logger.warning(f"⚠️ Unexpected error with exiftool: {e}")
        
        # Fallback to raw output parsing
        return parse_exiftool_text(result["output"])
    else:
        # Try again without JSON flag for more output
        result2 = run_command(
            [EXIFTOOL_PATH, filepath],
            timeout=ANALYSIS_TIMEOUT
        )
        
        if result2["success"]:
            return parse_exiftool_text(result2["output"])
        
        return {
            "success": False,
            "error": result["error"]
        }


def parse_exiftool_text(output):
    """Parse exiftool text output as fallback"""
    try:
        metadata = {}
        for line in output.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                if key and value and not key.startswith("----"):
                    metadata[key] = value
        
        if metadata:
            logger.info(f"✅ Parsed {len(metadata)} metadata fields from text output")
            return {
                "success": True,
                "metadata": metadata,
                "field_count": len(metadata),
                "parse_mode": "text"
            }
    except Exception as e:
        logger.warning(f"⚠️ Error parsing text output: {e}")
    
    return {
        "success": False,
        "error": "Could not parse exiftool output"
    }


def analyze_with_clamav(filepath):
    """
    Signature-based malware detection using ClamAV clamscan
    
    Returns:
        dict: {
            "clamav_status": "connected" | "not_installed" | "error",
            "clamav_detected": bool,
            "threats": list,
            "error": str (if any)
        }
    """
    logger.info(f"🦠 Running ClamAV malware scan on {os.path.basename(filepath)}")
    
    if not os.path.exists(CLAMSCAN_PATH):
        logger.warning("⚠️ clamscan not found, skipping ClamAV analysis")
        return {
            "clamav_status": "not_installed",
            "clamav_detected": False,
            "error": "clamscan not installed. Install with: sudo apt-get install clamav"
        }
    
    try:
        # Run clamscan on the file
        result = run_command(
            [CLAMSCAN_PATH, "--no-summary", filepath],
            timeout=ANALYSIS_TIMEOUT
        )
        
        logger.info("✅ ClamAV daemon connected")
        
        # clamscan returns:
        # - 0 if files are clean
        # - 1 if files are infected
        # - 2 if error occurred
        
        if result["success"]:
            # No threats detected (return code 0)
            logger.info("✅ ClamAV scan complete: No threats detected")
            return {
                "clamav_status": "connected",
                "clamav_detected": False,
                "threats": []
            }
        
        # Check if infected (return code 1)
        if "FOUND" in result["output"]:
            # Parse the output for threat details
            threats = []
            for line in result["output"].split("\n"):
                if "FOUND" in line:
                    # Format: filepath: ThreatName FOUND
                    parts = line.split(": ")
                    if len(parts) >= 2:
                        threat_info = parts[1].split(" FOUND")[0]
                        threats.append({
                            "file": os.path.basename(filepath),
                            "threat_type": "Unknown",
                            "threat_name": threat_info
                        })
                        logger.warning(f"🚨 MALWARE DETECTED: {threat_info}")
            
            return {
                "clamav_status": "connected",
                "clamav_detected": True,
                "threats": threats
            }
        
        # For any other case, consider it an error
        return {
            "clamav_status": "error",
            "clamav_detected": False,
            "error": result["error"]
        }
    
    except Exception as e:
        logger.error(f"❌ ClamAV scanning error: {e}")
        return {
            "clamav_status": "error",
            "clamav_detected": False,
            "error": str(e)
        }


def analyze_file(filepath):
    """
    Comprehensive file analysis using multiple tools
    
    Args:
        filepath: Path to downloaded file
    
    Returns:
        dict: Complete forensic analysis results including ClamAV malware detection
    """
    
    if not os.path.exists(filepath):
        logger.error(f"❌ File not found: {filepath}")
        return {
            "success": False,
            "error": "File not found"
        }
    
    file_size = os.path.getsize(filepath)
    filename = os.path.basename(filepath)
    
    logger.info(f"🔬 Starting forensic analysis on {filename} ({file_size / 1024:.2f} KB)")
    
    analysis_results = {
        "success": True,
        "filename": filename,
        "file_size": file_size,
        "binwalk": None,
        "exiftool": None,
        "strings": None,
        "clamav_status": None,
        "clamav_detected": None,
        "error": None
    }
    
    # Run all analyses
    try:
        analysis_results["strings"] = analyze_with_strings(filepath)
        analysis_results["binwalk"] = analyze_with_binwalk(filepath)
        analysis_results["exiftool"] = analyze_with_exiftool(filepath)
        
        # Run ClamAV malware detection
        clamav_result = analyze_with_clamav(filepath)
        analysis_results["clamav_status"] = clamav_result.get("clamav_status")
        analysis_results["clamav_detected"] = clamav_result.get("clamav_detected")
        analysis_results["clamav"] = clamav_result
        
    except Exception as e:
        logger.error(f"❌ Unexpected error during analysis: {e}")
        analysis_results["success"] = False
        analysis_results["error"] = str(e)
    
    logger.info(f"✅ Forensic analysis complete for {filename}")
    
    return analysis_results
