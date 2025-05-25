#!/usr/bin/env python3
"""
Gaza Media Fact-Check System Configuration Setup
This script helps you configure API keys and understand what's needed.
"""

def check_configuration():
    """Check current configuration status"""
    print("🔍 Gaza Media Fact-Check System Configuration Check")
    print("=" * 60)
    
    # Check Google API Key
    try:
        from app import DirectGeminiModel
        print("✅ Google AI (Gemini) integration: CONFIGURED")
        google_configured = True
    except Exception as e:
        print("❌ Google AI (Gemini) integration: NOT CONFIGURED")
        print(f"   Error: {e}")
        google_configured = False
    
    # Check Twitter API
    try:
        from twitter_agent import TWITTER_ENABLED, TWITTER_API_KEY
        if TWITTER_ENABLED:
            print("✅ Twitter API integration: CONFIGURED")
            twitter_configured = True
        else:
            if TWITTER_API_KEY == "66LubKev38oDzerpFaTQu9p9E":
                print("⚠️ Twitter API integration: USING DEMO KEYS (SIMULATION MODE)")
            else:
                print("❌ Twitter API integration: INVALID KEYS")
            twitter_configured = False
    except Exception as e:
        print("❌ Twitter API integration: NOT CONFIGURED")
        print(f"   Error: {e}")
        twitter_configured = False
    
    print("\n📊 System Status:")
    print(f"   Fact-checking: {'✅ READY' if google_configured else '❌ NEEDS SETUP'}")
    print(f"   Twitter posting: {'✅ READY' if twitter_configured else '⚠️ SIMULATION MODE'}")
    
    if google_configured and twitter_configured:
        print("\n🎉 FULL SYSTEM READY!")
        print("   You can run: python setup.py")
    elif google_configured:
        print("\n⚠️ PARTIAL SYSTEM READY!")
        print("   Fact-checking works, Twitter in simulation mode")
        print("   You can run: python setup.py")
    else:
        print("\n❌ SYSTEM NEEDS CONFIGURATION!")
        
    return google_configured, twitter_configured

def show_setup_instructions():
    """Show detailed setup instructions"""
    print("\n🔧 SETUP INSTRUCTIONS")
    print("=" * 60)
    
    print("\n1. GOOGLE AI (GEMINI) API SETUP:")
    print("   a) Go to: https://aistudio.google.com/app/apikey")
    print("   b) Create a new API key")
    print("   c) Copy your API key")
    print("   d) Edit app.py and replace 'YOUR_GOOGLE_API_KEY_HERE' with your key")
    print("   e) Line to find: GOOGLE_API_KEY = \"YOUR_GOOGLE_API_KEY_HERE\"")
    
    print("\n2. TWITTER API SETUP (Optional - for live posting):")
    print("   a) Go to: https://developer.twitter.com/en/portal/dashboard")
    print("   b) Create a new app or use existing one")
    print("   c) Set permissions to 'Read and Write'")
    print("   d) Generate API keys:")
    print("      - API Key")
    print("      - API Secret Key")
    print("      - Access Token")
    print("      - Access Token Secret")
    print("   e) Edit twitter_agent.py and replace the demo keys:")
    print("      - TWITTER_API_KEY = \"your_api_key\"")
    print("      - TWITTER_API_SECRET = \"your_api_secret\"")
    print("      - TWITTER_ACCESS_TOKEN = \"your_access_token\"")
    print("      - TWITTER_ACCESS_TOKEN_SECRET = \"your_access_token_secret\"")
    
    print("\n3. RUNNING THE SYSTEM:")
    print("   a) With Google API configured: python setup.py")
    print("   b) System will work in fact-checking mode")
    print("   c) Twitter integration will be in simulation mode unless configured")
    
    print("\n⚠️ MINIMUM REQUIREMENT:")
    print("   You MUST configure Google AI API for the system to work!")
    print("   Twitter API is optional - system works in simulation mode without it.")

def create_env_template():
    """Create a template .env file"""
    env_content = """# Gaza Media Fact-Check System Configuration
# Copy this to .env and fill in your API keys

# REQUIRED: Google AI (Gemini) API Key
# Get it from: https://aistudio.google.com/app/apikey
GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY_HERE

# OPTIONAL: Twitter API Keys (for live posting)
# Get them from: https://developer.twitter.com/en/portal/dashboard
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret

# System Configuration
DRY_RUN=false
DEBUG=true
"""
    
    with open('.env.template', 'w') as f:
        f.write(env_content)
    
    print("📁 Created .env.template file")
    print("   Copy it to .env and fill in your API keys")

def main():
    """Main configuration check"""
    print("🚀 Gaza Media Fact-Check System Configuration")
    print("=" * 60)
    
    google_ok, twitter_ok = check_configuration()
    
    if not google_ok:
        show_setup_instructions()
        create_env_template()
    else:
        print("\n✅ System is ready to run!")
        print("   Run: python setup.py")
        
        if not twitter_ok:
            print("\n💡 TIP: Configure Twitter API for live posting")
            print("   Currently running in simulation mode")

if __name__ == "__main__":
    main() 