import tweepy
import json
import hashlib
import uuid
from datetime import datetime
from typing import Dict, List
from flask import Flask, request, jsonify
import google.generativeai as genai
import time

# Twitter API Configuration - YOU MUST REPLACE WITH YOUR ACTUAL KEYS
TWITTER_API_KEY = "66LubKev38oDzerpFaTQu9p9E"
TWITTER_API_SECRET = "PurRxYGyjns3F4sRWCuLhj0Ib4LSNt5VwWvv7JmHYtSw4JbU4s"
TWITTER_ACCESS_TOKEN = "1926411698446999552-xpRDbTJOEPy2xNObJXyS7pgDiPbm9C"
TWITTER_ACCESS_TOKEN_SECRET = "QU6POpXqtA7K19HXwxsxUxYQGYOmNOXibKFvMwxGnnKF1"

# Configure Google API
GOOGLE_API_KEY = "YOUR_GOOGLE_API_KEY_HERE" # Make sure to replace this with your actual Google API key
genai.configure(api_key=GOOGLE_API_KEY)

# Configure Twitter API v2 Client
print("🔧 Initializing Twitter client...")
try:
    twitter_client = tweepy.Client(
        consumer_key=TWITTER_API_KEY,
        consumer_secret=TWITTER_API_SECRET,
        access_token=TWITTER_ACCESS_TOKEN,
        access_token_secret=TWITTER_ACCESS_TOKEN_SECRET,
        wait_on_rate_limit=True
    )
    
    # Test connection and permissions
    print("🧪 Testing Twitter API connection...")
    try:
        user = twitter_client.get_me()
        print(f"✅ Connected to Twitter as: @{user.data.username}")
        
        # Test posting capability with a simple test
        print("🔍 Testing posting permissions...")
        test_response = twitter_client.create_tweet(text="🤖 Bot connection test - will delete shortly")
        if test_response.data:
            print("✅ Posting permissions: VERIFIED")
            # Delete the test tweet
            twitter_client.delete_tweet(test_response.data['id'])
            print("🗑️ Test tweet deleted")
        
        print("🔥 Twitter client ready for LIVE POSTING!")
        TWITTER_ENABLED = True
        
    except tweepy.Forbidden as e:
        print(f"❌ Twitter permissions error: {e}")
        print("🔧 REQUIRED FIXES:")
        print("   1. Go to https://developer.twitter.com/en/portal/dashboard")
        print("   2. Select your app → Settings → User authentication settings")
        print("   3. Enable OAuth2.0 with Read and Write permissions")
        print("   4. Generate new API keys after permission change")
        print("   5. Make sure your app has 'Write' permissions enabled")
        TWITTER_ENABLED = False
        
    except tweepy.Unauthorized as e:
        print(f"❌ Twitter authentication failed: {e}")
        print("🔧 AUTHENTICATION FIXES:")
        print("   1. Regenerate ALL API keys in Twitter Developer Portal")
        print("   2. Copy the new keys to this file")
        print("   3. Make sure Bearer Token is included")
        print("   4. Wait 15 minutes after regenerating keys")
        TWITTER_ENABLED = False
        
    except Exception as e:
        print(f"❌ Twitter connection error: {e}")
        TWITTER_ENABLED = False
        
except Exception as e:
    print(f"❌ Twitter client initialization failed: {e}")
    print("🔄 Running in simulation mode")
    TWITTER_ENABLED = False


class TwitterContradictionBot:
    """Single tweet contradiction reporter"""
    
    def __init__(self):
        self.agent_id = "twitter_agent_001"
        self.agent_name = "TwitterContradictionBot"
        self.posting_enabled = TWITTER_ENABLED
    
    def create_single_contradiction_tweet(self, contradiction_data: dict) -> str:
        """Create a single tweet summarizing the contradiction"""
        print("📝 Creating single contradiction tweet...")
        
        # Process the first detailed contradiction
        detailed_contradictions = contradiction_data.get('detailed_contradictions', [])
        if not detailed_contradictions:
            return None
            
        first_contradiction = detailed_contradictions[0]
        
        # Extract article information
        articles = first_contradiction.get('articles_analyzed', {})
        western_article = articles.get('western', {})
        arabic_article = articles.get('arabic', {})
        
        # Extract contradiction details
        contradictions = first_contradiction.get('specific_contradictions', [])
        contradiction_summary = first_contradiction.get('contradiction_summary', {})
        
        # Get the main claims
        western_claim = ""
        arabic_claim = ""
        
        if contradictions:
            western_claim = contradictions[0].get('western_claim', {}).get('exact_quote', '')[:60]
            arabic_claim_data = contradictions[0].get('arabic_claim', {})
            arabic_claim = arabic_claim_data.get('english_translation', 
                                               arabic_claim_data.get('exact_quote', ''))[:60]
        
        # Get sources
        western_source = western_article.get('source', 'Western Media')
        arabic_source = arabic_article.get('source', 'Arabic Media')
        
        # Get severity
        severity = contradiction_summary.get('severity_level', 'medium').upper()
        
        # Create the single tweet - compact format
        tweet_content = (
            f"🚨 MEDIA CONTRADICTION [{severity}]\n\n"
            f"📰 {western_source}: \"{western_claim}...\"\n"
            f"📰 {arabic_source}: \"{arabic_claim}...\"\n\n"
            f"Same event, different stories. Always verify multiple sources.\n\n"
            f"#FactCheck #MediaBias #Gaza #NewsAnalysis"
        )
        
        # Ensure tweet is under 280 characters
        if len(tweet_content) > 280:
            # Truncate claims if needed
            max_claim_length = 40
            western_claim_short = western_claim[:max_claim_length]
            arabic_claim_short = arabic_claim[:max_claim_length]
            
            tweet_content = (
                f"🚨 CONTRADICTION [{severity}]\n\n"
                f"📰 {western_source}: \"{western_claim_short}...\"\n"
                f"📰 {arabic_source}: \"{arabic_claim_short}...\"\n\n"
                f"Same event, different stories.\n\n"
                f"#FactCheck #MediaBias"
            )
        
        print(f"📝 Created tweet ({len(tweet_content)} chars): {tweet_content[:100]}...")
        return tweet_content
    
    def post_single_tweet(self, tweet_content: str, dry_run: bool = False) -> dict:
        """Post a single tweet about the contradiction"""
        
        if dry_run or not self.posting_enabled:
            return self._simulate_single_tweet(tweet_content)
        
        # ACTUAL TWITTER POSTING
        print("🐦 POSTING SINGLE TWEET TO TWITTER...")
        
        try:
            response = twitter_client.create_tweet(text=tweet_content)
            tweet_id = response.data['id']
            
            # Get authenticated user info for URL construction
            me = twitter_client.get_me()
            username = me.data.username
            tweet_url = f"https://twitter.com/{username}/status/{tweet_id}"
            
            result = {
                'status': 'LIVE_POSTED',
                'tweet_id': tweet_id,
                'url': tweet_url,
                'content': tweet_content,
                'character_count': len(tweet_content),
                'posted_at': datetime.now().isoformat(),
                'success': True
            }
            
            print(f"✅ SUCCESS! Posted tweet: {tweet_id}")
            print(f"🔗 Tweet URL: {tweet_url}")
            return result
            
        except tweepy.TooManyRequests as e:
            print(f"⏳ Rate limit hit: {e}")
            return {
                'status': 'RATE_LIMITED',
                'error': 'Hit Twitter rate limit - try again in 15 minutes',
                'retry_after': 900
            }
            
        except tweepy.Forbidden as e:
            print(f"❌ Permission denied: {e}")
            return {
                'status': 'PERMISSION_DENIED',
                'error': 'App lacks write permissions - check Twitter Developer Portal'
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Posting error: {error_msg}")
            return {
                'status': 'ERROR',
                'error': error_msg
            }
    
    def _simulate_single_tweet(self, tweet_content: str) -> dict:
        """Simulate posting a single tweet"""
        print("🎭 SIMULATION MODE - Single tweet")
        
        result = {
            'status': 'SIMULATED',
            'simulated_tweet_id': f"sim_{hash(tweet_content) % 1000000000000000000}",
            'content': tweet_content,
            'character_count': len(tweet_content),
            'posted_at': datetime.now().isoformat()
        }
        
        print(f"🐦 SIMULATED SINGLE TWEET:")
        print(f"Content: {tweet_content}")
        print(f"Characters: {len(tweet_content)}/280")
        print("-" * 50)
        
        return result
    
    def process_contradiction_and_tweet(self, contradiction_data: dict, dry_run: bool = False):
        """Process contradiction data and post a single tweet"""
        print(f"🤖 Processing contradiction for {'LIVE POSTING' if not dry_run and self.posting_enabled else 'simulation'}...")
        
        # Create single tweet content
        tweet_content = self.create_single_contradiction_tweet(contradiction_data)
        
        if not tweet_content:
            print("⚠️ No contradiction data to tweet about")
            return {"status": "no_data", "message": "No contradictions found to tweet about"}
        
        # Post the single tweet
        posting_result = self.post_single_tweet(tweet_content, dry_run)
        
        return {
            'status': 'success',
            'tweet_created': True,
            'live_posting_enabled': self.posting_enabled,
            'posting_result': posting_result
        }


# Initialize Twitter agent
twitter_bot = TwitterContradictionBot()

# Flask app for A2A communication
app = Flask(__name__)

@app.route('/a2a/receive', methods=['POST'])
def receive_a2a_message():
    """Endpoint to receive A2A messages - SINGLE TWEET POSTING"""
    message = request.json
    
    print(f"📨 Received A2A message: {message.get('message_type', 'Unknown Type')}")
    
    # Process the message
    if message.get('message_type') == 'contradiction_report':
        # Process Twitter posting - SINGLE TWEET MODE
        contradiction_data = message.get('payload')
        
        if not contradiction_data:
            print("❌ No 'payload' found in contradiction report message.")
            return jsonify({
                'status': 'error',
                'message_id': message.get('message_id', 'N/A'),
                'timestamp': datetime.now().isoformat(),
                'error': "Missing 'payload' in contradiction_report message"
            }), 400

        print("🐦 Received contradiction report, creating single tweet...")
        try:
            result = twitter_bot.process_contradiction_and_tweet(
                contradiction_data, 
                dry_run=False  # LIVE POSTING ENABLED
            )
            print(f"✅ Tweet posting result: {result['status']}")
            
            response = {
                'status': 'received',
                'message_id': message.get('message_id', 'N/A'),
                'timestamp': datetime.now().isoformat(),
                'processing_result': result,
                'live_posting': twitter_bot.posting_enabled
            }
            
        except Exception as e:
            print(f"❌ Error creating tweet: {e}")
            response = {
                'status': 'error',
                'message_id': message.get('message_id', 'N/A'),
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    else:
        response = {
            'status': 'received',
            'message_id': message.get('message_id', 'N/A'),
            'timestamp': datetime.now().isoformat(),
            'message': "Unknown message type or no specific processing needed"
        }
    
    return jsonify(response)

@app.route('/a2a/status', methods=['GET'])
def a2a_status():
    """Get A2A agent status"""
    return jsonify({
        'agent_id': twitter_bot.agent_id,
        'agent_name': twitter_bot.agent_name,
        'status': 'active',
        'capabilities': ['contradiction_reporting', 'single_tweet_posting'],
        'twitter_client_status': 'LIVE_POSTING_ENABLED' if twitter_bot.posting_enabled else 'SIMULATION_MODE',
        'version': 'single_tweet_v1.0',
        'posting_enabled': twitter_bot.posting_enabled,
        'posting_format': 'single_tweet'
    })

@app.route('/test_tweet', methods=['POST'])
def test_tweet():
    """Test endpoint to create a single sample tweet"""
    sample_data = {
        'detailed_contradictions': [{
            'articles_analyzed': {
                'western': {
                    'title': 'Israeli Strike Kills 15 in Gaza Hospital Area',
                    'source': 'CNN',
                    'url': 'https://example.com/western'
                },
                'arabic': {
                    'title': 'قصف إسرائيلي يستهدف مستشفى غزة ويقتل 23 مدنياً',
                    'source': 'Al Jazeera Arabic',
                    'url': 'https://example.com/arabic'
                }
            },
            'specific_contradictions': [{
                'western_claim': {'exact_quote': '15 casualties reported in targeted operation'},
                'arabic_claim': {
                    'exact_quote': '23 مدني قتلوا في القصف',
                    'english_translation': '23 civilians killed in bombing'
                }
            }],
            'contradiction_summary': {
                'severity_level': 'high',
                'main_discrepancy': 'Major discrepancy in casualty numbers: 8-person difference'
            }
        }]
    }
    
    # Get dry_run parameter from request
    dry_run = request.json.get('dry_run', True) if request.json else True
    
    try:
        result = twitter_bot.process_contradiction_and_tweet(
            sample_data, 
            dry_run=dry_run
        )
        return jsonify({
            'status': 'success',
            'message': f'Single tweet {"simulated" if dry_run else "posted live"} successfully',
            'live_posting_enabled': twitter_bot.posting_enabled,
            'result': result
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/post_live', methods=['POST'])
def post_live():
    """Force live posting endpoint - single tweet"""
    try:
        # Sample data for live test
        sample_data = {
            'detailed_contradictions': [{
                'articles_analyzed': {
                    'western': {
                        'title': 'Bot Test: Contradiction Detection Online',
                        'source': 'Bot Test Western',
                        'url': 'https://example.com/test'
                    },
                    'arabic': {
                        'title': 'اختبار البوت: كشف التناقضات متاح',
                        'source': 'Bot Test Arabic',
                        'url': 'https://example.com/test_ar'
                    }
                },
                'specific_contradictions': [{
                    'western_claim': {'exact_quote': 'Bot functioning normally'},
                    'arabic_claim': {
                        'exact_quote': 'البوت يعمل بشكل طبيعي',
                        'english_translation': 'Bot working normally'
                    }
                }],
                'contradiction_summary': {
                    'severity_level': 'low',
                    'main_discrepancy': 'Test contradiction for demo purposes'
                }
            }]
        }
        
        result = twitter_bot.process_contradiction_and_tweet(
            sample_data, 
            dry_run=False  # FORCE LIVE POSTING
        )
        
        return jsonify({
            'status': 'success',
            'message': 'LIVE single tweet posting attempted',
            'posting_enabled': twitter_bot.posting_enabled,
            'result': result
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    print("🐦 Starting Single Tweet Contradiction Agent...")
    print("📡 A2A Protocol enabled")
    print("🔧 Available at: http://localhost:5001")
    print("🐦 Single tweet mode: POST /test_tweet")
    print("🔥 Live posting: POST /post_live")
    print("📨 A2A endpoint: /a2a/receive")
    print("📊 Status: /a2a/status")
    
    if twitter_bot.posting_enabled:
        print("🚀 LIVE TWITTER POSTING ENABLED!")
        print("   ✅ Authentication successful")
        print("   ✅ Write permissions confirmed")
        print("   🐦 Single tweet format ready!")
    else:
        print("⚠️  SIMULATION MODE ACTIVE")
        print("🔧 TO ENABLE LIVE POSTING:")
        print("   1. Get Twitter API keys from https://developer.twitter.com")
        print("   2. Set app permissions to 'Read and Write'")
        print("   3. Replace API keys in the code")
        print("   4. Restart the agent")
    
    app.run(debug=True, host='0.0.0.0', port=5001)