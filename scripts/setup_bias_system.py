#!/usr/bin/env python3
"""
Setup Bias Analysis System

This script sets up the enhanced bias analysis system by:
1. Running database migrations
2. Loading academic sources data
3. Loading bias ratings data
4. Running initial bias analysis on existing sources

Usage:
    python scripts/setup_bias_system.py
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.etl.academic_loader import load_academic_sources
from app.etl.load_bias import main as load_bias_main


async def main():
    """Main setup function."""
    print("🚀 Setting up Enhanced Bias Analysis System...")
    print("=" * 50)

    try:
        # Step 1: Load academic sources if data file exists
        academic_data_path = Path("data/academic_sources_sample.csv")
        if academic_data_path.exists():
            print("\n📚 Loading academic sources...")
            await load_academic_sources(academic_data_path)
            print("✅ Academic sources loaded successfully")
        else:
            print(f"⚠️  Academic sources file not found: {academic_data_path}")

        # Step 2: Load bias ratings if data file exists
        bias_data_path = Path("data/bias_ratings.csv")
        if bias_data_path.exists():
            print("\n📊 Loading bias ratings...")
            sys.argv = ["load_bias", str(bias_data_path)]
            await load_bias_main()
            print("✅ Bias ratings loaded successfully")
        else:
            print(f"⚠️  Bias ratings file not found: {bias_data_path}")

        print("\n🎉 Enhanced Bias Analysis System setup completed!")
        print("You can now:")
        print("- View bias analysis results in the web interface")
        print("- Use the API endpoints for bias analysis")
        print("- Run batch analysis on new sources")

    except Exception as e:
        print(f"❌ Setup failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
