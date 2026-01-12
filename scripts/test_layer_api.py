#!/usr/bin/env python3
"""
Layer.ai API Diagnostic Script

This script tests the Layer.ai API connection and generation capabilities.
Run this to diagnose issues with asset generation.

Usage:
    python scripts/test_layer_api.py
    python scripts/test_layer_api.py --style-id <style_id>
    python scripts/test_layer_api.py --test-generate
"""

import argparse
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.layer_client import LayerClientSync, LayerAPIError
from src.utils.helpers import get_settings


def print_header(title: str) -> None:
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def print_status(label: str, status: str, details: str = "") -> None:
    """Print a status line with color."""
    if status.lower() in ("ok", "pass", "complete", "success"):
        symbol = "✓"
        color = "\033[92m"  # Green
    elif status.lower() in ("warn", "warning"):
        symbol = "⚠"
        color = "\033[93m"  # Yellow
    else:
        symbol = "✗"
        color = "\033[91m"  # Red

    reset = "\033[0m"

    if details:
        print(f"  {color}{symbol}{reset} {label}: {status} - {details}")
    else:
        print(f"  {color}{symbol}{reset} {label}: {status}")


def test_connection(client: LayerClientSync) -> bool:
    """Test API connection."""
    print_header("Testing API Connection")

    try:
        info = client.get_workspace_info()
        print_status("Connection", "OK", f"Connected to workspace")
        print_status("Credits", "OK" if info.credits_available > 0 else "WARN",
                    f"{info.credits_available} credits available")
        print_status("Access", "OK" if info.has_access else "FAIL",
                    "Has workspace access" if info.has_access else "No access")
        return True
    except LayerAPIError as e:
        print_status("Connection", "FAIL", str(e))
        return False


def test_list_styles(client: LayerClientSync) -> list:
    """Test listing styles."""
    print_header("Testing Style Listing")

    try:
        styles = client.list_styles(limit=20)
        print_status("List Styles", "OK", f"Found {len(styles)} styles")

        if styles:
            print("\n  Available Styles:")
            print("  " + "-" * 50)
            for style in styles[:10]:  # Show first 10
                status = style.get("status", "?")
                stype = style.get("type", "?")
                name = style.get("name", "Unnamed")[:30]
                sid = style.get("id", "?")[:20]

                status_ok = status == "COMPLETE"
                type_ok = stype != "MODEL_URL"

                status_marker = "✓" if status_ok else "⚠"
                type_marker = "✓" if type_ok else "⚠"

                print(f"    [{status_marker}] {name:<30} | {status:<10} | {stype}")
                print(f"        ID: {sid}")

            if len(styles) > 10:
                print(f"\n  ... and {len(styles) - 10} more styles")

        return styles
    except LayerAPIError as e:
        print_status("List Styles", "FAIL", str(e))
        return []


def test_style_validation(client: LayerClientSync, style_id: str) -> dict:
    """Test getting a specific style."""
    print_header(f"Testing Style: {style_id[:30]}...")

    try:
        style = client.get_style(style_id)

        name = style.get("name", "Unknown")
        status = style.get("status", "Unknown")
        stype = style.get("type", "Unknown")

        print_status("Style Found", "OK", name)
        print_status("Status", "OK" if status == "COMPLETE" else "FAIL", status)
        print_status("Type", "OK" if stype != "MODEL_URL" else "WARN", stype)

        if stype == "MODEL_URL":
            print("\n  ⚠ Warning: MODEL_URL styles (base models) may have generation restrictions.")
            print("    Consider using a custom-trained LAYER_TRAINED_CHECKPOINT style.")

        return style
    except LayerAPIError as e:
        print_status("Style", "FAIL", str(e))
        return {}


def test_generation(client: LayerClientSync, style_id: str, prompt: str = "simple red gem") -> bool:
    """Test image generation."""
    print_header("Testing Image Generation")

    print(f"  Style ID: {style_id[:40]}...")
    print(f"  Prompt: {prompt}")
    print()

    try:
        print("  Generating... (this may take 10-60 seconds)")
        result = client.generate_with_polling(prompt=prompt, style_id=style_id)

        if result.image_url:
            print_status("Generation", "OK", "Image generated successfully!")
            print(f"\n  Image URL: {result.image_url[:80]}...")
            print(f"  Duration: {result.duration_seconds:.1f}s")
            return True
        else:
            print_status("Generation", "FAIL", result.error_message or "No image URL returned")
            return False

    except LayerAPIError as e:
        print_status("Generation", "FAIL", str(e))

        # Provide specific advice based on error
        error_str = str(e).lower()
        if "pixel wizards" in error_str:
            print("\n  Likely causes:")
            print("    1. The style may have content restrictions")
            print("    2. The prompt may trigger content filters")
            print("    3. Rate limiting on the workspace")
            print("\n  Try:")
            print("    - Using a custom-trained style instead of a base model")
            print("    - Simplifying the prompt")
            print("    - Waiting a few minutes and trying again")
        elif "401" in error_str or "authentication" in error_str:
            print("\n  Your API key appears to be invalid.")
            print("  Check LAYER_API_KEY in your .env file.")
        elif "403" in error_str:
            print("\n  Access forbidden. Check:")
            print("    - LAYER_WORKSPACE_ID is correct")
            print("    - Your API key has workspace access")

        return False


def main():
    parser = argparse.ArgumentParser(description="Layer.ai API Diagnostic Tool")
    parser.add_argument("--style-id", help="Specific style ID to test")
    parser.add_argument("--test-generate", action="store_true", help="Test image generation")
    parser.add_argument("--prompt", default="simple red gem", help="Prompt for generation test")
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("  Layer.ai API Diagnostic Tool")
    print("=" * 60)

    # Check environment
    settings = get_settings()

    print("\n  Configuration:")
    print(f"    API URL: {settings.layer_api_url}")
    print(f"    Workspace ID: {settings.layer_workspace_id[:20]}..." if settings.layer_workspace_id else "    Workspace ID: NOT SET")
    print(f"    API Key: {'***' + settings.layer_api_key[-8:] if settings.layer_api_key else 'NOT SET'}")

    if not settings.layer_api_key:
        print("\n  ✗ ERROR: LAYER_API_KEY not set in environment or .env file")
        return 1

    if not settings.layer_workspace_id:
        print("\n  ✗ ERROR: LAYER_WORKSPACE_ID not set in environment or .env file")
        return 1

    # Create client
    client = LayerClientSync()

    # Run tests
    all_passed = True

    # Test 1: Connection
    if not test_connection(client):
        print("\n  ⚠ Connection failed. Skipping remaining tests.")
        return 1

    # Test 2: List styles
    styles = test_list_styles(client)

    # Test 3: Style validation (if specified or use first complete style)
    style_id = args.style_id
    if not style_id and styles:
        # Find first COMPLETE style
        for s in styles:
            if s.get("status") == "COMPLETE":
                style_id = s.get("id")
                break

    if style_id:
        style = test_style_validation(client, style_id)
        if not style:
            all_passed = False
    else:
        print("\n  ⚠ No style ID available for validation test")
        all_passed = False

    # Test 4: Generation (optional)
    if args.test_generate and style_id:
        if not test_generation(client, style_id, args.prompt):
            all_passed = False
    elif args.test_generate:
        print("\n  ⚠ Cannot test generation without a valid style ID")
        all_passed = False

    # Summary
    print_header("Summary")
    if all_passed:
        print("  All tests passed! Layer.ai API is working correctly.")
    else:
        print("  Some tests failed. Review the output above for details.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
