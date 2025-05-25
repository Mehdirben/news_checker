import tweepy
import json
import hashlib
import uuid
import secrets
import base64
import os
from datetime import datetime
from typing import Dict, List
from flask import Flask, request, jsonify, redirect, session
import google.generativeai as genai

# Twitter API Configuration - ONLY NEED THESE TWO + BEARER TOKEN
TWITTER_API_KEY = "M9CyMxvJUpsnJLVu4N4f4lTkm"
TWITTER_API_SECRET = "eIbh3pf6LFeSCD1ux3Ar50oxSQpyOBOy28zXMvuIgrCueJ6xM7" 
TWITTER_BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAJrj1wEAAAAAmpUyQJxeg8WudmrlL8xmbhb0W%2BU%3Dbxh3djXuELMjepOUGNv6Ctk87IWr14U1HdSxDLRUXw1udQPtd9"

# OAuth 2.0 Configuration - UPDATE THIS AFTER DEPLOYMENT
REDIRECT_URI ="https://news-checker-b32vxc0zk-ayoubs-projects-fd268e73.vercel.app/oauth/callback"
SCOPES = ["tweet.read", "tweet.write", "users.read"]

# Configure Google API
GOOGLE_API_KEY = "AIzaSyDwA6AGJp6SykOxNCJhT-vEzTcvzrmh93Q"
genai.configure(api_key=GOOGLE_API_KEY)

class TwitterOAuthManager:
    """Handles Twitter OAuth 2.0 flow for Vercel deployment"""
    
    def __init__(self):
        self.auth_handler = tweepy.OAuth2UserHandler(
            client_id=TWITTER_API_KEY,
            redirect_uri=REDIRECT_URI,
            scope=SCOPES,
            client_secret=TWITTER_API_SECRET
        )
        self.authenticated_client = None
        self.access_token = None
        
    def get_authorization_url(self):
        """Step 1: Get authorization URL"""
        print("🔐 Creating OAuth authorization URL...")
        try:
            authorization_url = self.auth_handler.get_authorization_url()
            print(f"✅ Authorization URL created: {authorization_url}")
            return authorization_url
        except Exception as e:
            print(f"❌ Error creating auth URL: {e}")
            return None
    
    def handle_callback(self, authorization_response_url):
        """Step 2: Handle OAuth callback"""
        print("🔄 Processing OAuth callback...")
        try:
            # Extract access token from callback
            access_token = self.auth_handler.fetch_token(authorization_response_url)
            self.access_token = access_token
            
            # Create authenticated client
            self.authenticated_client = tweepy.Client(
                bearer_token=TWITTER_BEARER_TOKEN,
                consumer_key=TWITTER_API_KEY,
                consumer_secret=TWITTER_API_SECRET,
                access_token=access_token["access_token"],
                wait_on_rate_limit=True
            )
            
            # Test the connection
            user = self.authenticated_client.get_me()
            print(f"✅ OAuth successful! Connected as: @{user.data.username}")
            return True
            
        except Exception as e:
            print(f"❌ OAuth callback error: {e}")
            return False
    
    def is_authenticated(self):
        """Check if we have a valid authenticated client"""
        return self.authenticated_client is not None

class TwitterThreadCreator:
    """Twitter thread creator with OAuth 2.0 support"""
    
    def __init__(self):
        self.agent_id = "twitter_agent_oauth"
        self.agent_name = "TwitterContradictionBot_OAuth"
        self.oauth_manager = TwitterOAuthManager()
    
    def start_oauth_flow(self):
        """Start the OAuth flow"""
        return self.oauth_manager.get_authorization_url()
    
    def complete_oauth_flow(self, callback_url):
        """Complete the OAuth flow"""
        return self.oauth_manager.handle_callback(callback_url)
    
    def format_contradiction_for_twitter(self, contradiction_data: dict) -> List[dict]:
        """Format contradiction analysis for Twitter consumption"""
        print("📱 Formatting contradiction data for Twitter...")
        
        twitter_reports = []
        
        # Process detailed contradictions
        for detailed_analysis in contradiction_data.get('detailed_contradictions', []):
            if 'articles_analyzed' in detailed_analysis:
                
                # Extract main discrepancy
                main_discrepancy = detailed_analysis.get('contradiction_summary', {}).get(
                    'main_discrepancy', 'Media discrepancy detected'
                )
                
                # Extract contradictions
                contradictions = detailed_analysis.get('specific_contradictions', [])
                severity = detailed_analysis.get('contradiction_summary', {}).get('severity_level', 'medium')
                
                report = {
                    'report_id': f"CR_{hashlib.md5(str(detailed_analysis).encode()).hexdigest()[:8]}",
                    'main_headline': f"Media Contradiction Alert: {main_discrepancy[:100]}...",
                    'western_source': {
                        'outlet': detailed_analysis['articles_analyzed']['western']['source'],
                        'title': detailed_analysis['articles_analyzed']['western']['title'],
                        'url': detailed_analysis['articles_analyzed']['western']['url'],
                        'key_claim': self.extract_western_claim(contradictions)
                    },
                    'arabic_source': {
                        'outlet': detailed_analysis['articles_analyzed']['arabic']['source'],
                        'title': detailed_analysis['articles_analyzed']['arabic']['title'],
                        'url': detailed_analysis['articles_analyzed']['arabic']['url'],
                        'key_claim': self.extract_arabic_claim(contradictions)
                    },
                    'contradiction_summary': main_discrepancy,
                    'severity': severity,
                    'contradictions': contradictions,
                    'hashtags': self.generate_hashtags(severity, main_discrepancy)
                }
                
                twitter_reports.append(report)
        
        print(f"📱 Created {len(twitter_reports)} Twitter-ready reports")
        return twitter_reports
    
    def extract_western_claim(self, contradictions: List[dict]) -> str:
        """Extract main Western claim from contradictions"""
        if contradictions:
            return contradictions[0].get('western_claim', {}).get('exact_quote', '')[:200]
        return "Western media report"
    
    def extract_arabic_claim(self, contradictions: List[dict]) -> str:
        """Extract main Arabic claim from contradictions"""
        if contradictions:
            arabic_claim = contradictions[0].get('arabic_claim', {})
            return arabic_claim.get('english_translation', arabic_claim.get('exact_quote', ''))[:200]
        return "Arabic media report"
    
    def generate_hashtags(self, severity: str, discrepancy: str) -> List[str]:
        """Generate relevant hashtags"""
        base_tags = ['#FactCheck', '#MediaBias', '#Gaza', '#NewsAnalysis']
        
        if severity == 'critical':
            base_tags.append('#CriticalContradiction')
        elif severity == 'high':
            base_tags.append('#SignificantDiscrepancy')
        
        if 'casualt' in discrepancy.lower():
            base_tags.append('#CasualtyReporting')
        
        return base_tags
    
    def create_twitter_thread(self, report: dict, style: str = "engaging") -> List[dict]:
        """Create Twitter thread from contradiction report"""
        print(f"🧵 Creating Twitter thread in {style} style...")
        
        thread_tweets = []
        
        # Tweet 1: Main headline
        if style == "urgent":
            tweet1 = f"🚨 MEDIA CONTRADICTION ALERT 🚨\n\n{report['main_headline']}\n\n🧵 Thread below 👇"
        elif style == "engaging":
            tweet1 = f"🔍 Something doesn't add up in Gaza coverage...\n\n{report['main_headline']}\n\nLet's break this down 🧵"
        else:  # factual
            tweet1 = f"📊 Media Analysis Alert\n\n{report['main_headline']}\n\nDetailed analysis thread:"
        
        thread_tweets.append({
            'tweet_number': 1,
            'content': tweet1,
            'character_count': len(tweet1)
        })
        
        # Tweet 2: Western source
        western_claim = report['western_source']['key_claim'][:150]
        tweet2 = f"2/ 🇺🇸 WESTERN SOURCE: {report['western_source']['outlet']}\n\n\"{western_claim}...\"\n\n🔗 {report['western_source']['url']}"
        
        thread_tweets.append({
            'tweet_number': 2,
            'content': tweet2,
            'character_count': len(tweet2)
        })
        
        # Tweet 3: Arabic source  
        arabic_claim = report['arabic_source']['key_claim'][:150]
        tweet3 = f"3/ 🇵🇸 ARABIC SOURCE: {report['arabic_source']['outlet']}\n\n\"{arabic_claim}...\"\n\n🔗 {report['arabic_source']['url']}"
        
        thread_tweets.append({
            'tweet_number': 3,
            'content': tweet3,
            'character_count': len(tweet3)
        })
        
        # Tweet 4: Contradiction analysis
        tweet4 = f"4/ ⚡ CONTRADICTION DETECTED:\n\n{report['contradiction_summary']}\n\nSeverity: {report['severity'].upper()}"
        
        thread_tweets.append({
            'tweet_number': 4,
            'content': tweet4,
            'character_count': len(tweet4)
        })
        
        # Tweet 5: Call to action with hashtags
        hashtags = ' '.join(report['hashtags'])
        if style == "urgent":
            tweet5 = f"5/ 🎯 WHAT THIS MEANS:\n\nReaders deserve consistent, accurate reporting. Always cross-reference multiple sources.\n\n{hashtags}"
        elif style == "engaging":
            tweet5 = f"5/ 💭 TAKEAWAY:\n\nThis is why media literacy matters. Different sources, different stories.\n\nWhat do you think? 🤔\n\n{hashtags}"
        else:  # factual
            tweet5 = f"5/ 📋 ANALYSIS COMPLETE:\n\nRecommendation: Seek additional sources for verification.\n\n{hashtags}"
        
        thread_tweets.append({
            'tweet_number': 5,
            'content': tweet5,
            'character_count': len(tweet5)
        })
        
        print(f"🧵 Created {len(thread_tweets)}-tweet thread")
        return thread_tweets
    
    def post_twitter_thread(self, tweets: List[dict], dry_run: bool = True) -> dict:
        """Post Twitter thread using OAuth authenticated client"""
        print(f"🐦 {'Simulating' if dry_run else 'Posting'} Twitter thread...")
        
        if dry_run:
            # Simulate posting
            results = {
                'status': 'simulated',
                'tweets_posted': len(tweets),
                'simulation_results': [
                    {
                        'tweet_number': tweet['tweet_number'],
                        'simulated_tweet_id': f"sim_{hash(tweet['content']) % 10000000000000000000}",
                        'content': tweet['content'],
                        'character_count': tweet['character_count'],
                        'status': 'would_post_successfully'
                    }
                    for tweet in tweets
                ],
                'posted_at': datetime.now().isoformat()
            }
            
            print(f"✅ Simulated posting {len(tweets)} tweets")
            
            # Show the simulated tweets
            for tweet in results['simulation_results']:
                print(f"\n🐦 SIMULATED TWEET {tweet['tweet_number']}:")
                print(f"Content: {tweet['content']}")
                print(f"Characters: {tweet['character_count']}/280")
                print("-" * 50)
            
            return results
        
        else:
            # Check if we're authenticated
            if not self.oauth_manager.is_authenticated():
                return {
                    'status': 'error',
                    'error': 'Not authenticated. Please complete OAuth flow first.',
                    'fix_instructions': 'Visit /oauth/start to begin authentication'
                }
            
            # Actually post to Twitter using OAuth client
            posted_tweets = []
            reply_to_id = None
            
            try:
                for tweet in tweets:
                    # Post tweet using OAuth authenticated client
                    response = self.oauth_manager.authenticated_client.create_tweet(
                        text=tweet['content'],
                        in_reply_to_tweet_id=reply_to_id
                    )
                    
                    tweet_id = response.data['id']
                    reply_to_id = tweet_id  # Next tweet replies to this one
                    
                    posted_tweets.append({
                        'tweet_number': tweet['tweet_number'],
                        'tweet_id': tweet_id,
                        'content_preview': tweet['content'][:50] + "...",
                        'status': 'posted_successfully',
                        'url': f"https://twitter.com/user/status/{tweet_id}"
                    })
                    
                    print(f"✅ Posted tweet {tweet['tweet_number']}: {tweet_id}")
                    
                    # Rate limiting delay
                    import time
                    time.sleep(2)
                
                results = {
                    'status': 'posted',
                    'tweets_posted': len(posted_tweets),
                    'posting_results': posted_tweets,
                    'thread_url': posted_tweets[0]['url'] if posted_tweets else "",
                    'posted_at': datetime.now().isoformat()
                }
                
                print(f"🎉 Successfully posted {len(posted_tweets)}-tweet thread!")
                return results
                
            except Exception as e:
                error_msg = str(e)
                print(f"❌ Twitter posting error: {error_msg}")
                
                return {
                    'status': 'error',
                    'error': error_msg,
                    'tweets_posted': len(posted_tweets),
                    'partial_results': posted_tweets,
                    'fix_instructions': 'Check OAuth authentication and permissions'
                }
    
    def process_contradiction_and_tweet(self, contradiction_data: dict, style: str = "engaging", dry_run: bool = True):
        """Process contradiction data and create Twitter thread"""
        print(f"🤖 Processing contradiction data for Twitter...")
        
        # Format data for Twitter
        twitter_reports = self.format_contradiction_for_twitter(contradiction_data)
        
        if not twitter_reports:
            print("⚠️ No contradiction reports to process")
            return {"status": "no_data", "message": "No contradictions found to tweet about"}
        
        results = []
        
        # Create threads for each report
        for report in twitter_reports[:2]:  # Limit to 2 reports to avoid spam
            print(f"🧵 Creating thread for report: {report['report_id']}")
            
            # Create thread
            tweets = self.create_twitter_thread(report, style)
            
            # Post thread
            posting_result = self.post_twitter_thread(tweets, dry_run)
            
            results.append({
                'report_id': report['report_id'],
                'thread_created': True,
                'posting_result': posting_result
            })
        
        return {
            'status': 'success',
            'threads_created': len(results),
            'results': results
        }

# Initialize Twitter agent
twitter_creator = TwitterThreadCreator()

# Flask app with OAuth endpoints
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # For session management

# OAuth Routes
@app.route('/oauth/start')
def start_oauth():
    """Start OAuth flow"""
    print("🔐 Starting OAuth flow...")
    
    auth_url = twitter_creator.start_oauth_flow()
    if auth_url:
        print(f"🔗 Redirecting to Twitter OAuth: {auth_url}")
        return redirect(auth_url)
    else:
        return jsonify({
            'error': 'Failed to create authorization URL',
            'instructions': 'Check your Twitter API credentials'
        }), 500

@app.route('/oauth/callback')
def oauth_callback():
    """Handle OAuth callback"""
    print("🔄 Handling OAuth callback...")
    
    # Get the full callback URL
    callback_url = request.url
    print(f"📥 Callback URL: {callback_url}")
    
    # Complete OAuth flow
    success = twitter_creator.complete_oauth_flow(callback_url)
    
    if success:
        return jsonify({
            'status': 'success',
            'message': 'OAuth authentication completed successfully!',
            'next_steps': [
                'You can now post tweets using /test_thread',
                'Or send contradiction data to /a2a/receive'
            ]
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'OAuth authentication failed',
            'try_again': '/oauth/start'
        }), 400

@app.route('/oauth/status')
def oauth_status():
    """Check OAuth authentication status"""
    is_auth = twitter_creator.oauth_manager.is_authenticated()
    
    return jsonify({
        'authenticated': is_auth,
        'status': 'ready_to_post' if is_auth else 'authentication_required',
        'auth_url': '/oauth/start' if not is_auth else None
    })

# Main Routes
@app.route('/')
def home():
    """Home page with instructions and configuration details"""
    is_auth = twitter_creator.oauth_manager.is_authenticated()
    
    # Get current domain for display
    current_domain = request.host_url.rstrip('/')
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Twitter Bot OAuth Setup</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
            .status {{ padding: 15px; border-radius: 8px; margin: 15px 0; }}
            .success {{ background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; }}
            .warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; color: #856404; }}
            .info {{ background-color: #d1ecf1; border: 1px solid #bee5eb; color: #0c5460; }}
            button {{ padding: 12px 24px; margin: 8px; background-color: #1da1f2; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; }}
            button:hover {{ background-color: #0d8bd9; }}
            button:disabled {{ background-color: #ccc; cursor: not-allowed; }}
            code {{ background-color: #f4f4f4; padding: 3px 6px; border-radius: 3px; font-family: monospace; }}
            .config-box {{ background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 20px; border-radius: 8px; margin: 15px 0; }}
        </style>
    </head>
    <body>
        <h1>🐦 Twitter Bot OAuth Setup</h1>
        
        <div class="status {'success' if is_auth else 'warning'}">
            <strong>🔐 Authentication Status:</strong> {'✅ Authenticated - Ready to post!' if is_auth else '⚠️ Not authenticated - Complete OAuth flow below'}
        </div>
        
        <div class="config-box">
            <h2>🔧 Twitter App Configuration</h2>
            <p><strong>Use these EXACT URLs in your Twitter Developer Portal:</strong></p>
            <table border="1" style="border-collapse: collapse; width: 100%;">
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Field</td>
                    <td style="padding: 8px; font-weight: bold;">Value</td>
                </tr>
                <tr>
                    <td style="padding: 8px;">Callback URL / Redirect URL</td>
                    <td style="padding: 8px;"><code>{current_domain}/oauth/callback</code></td>
                </tr>
                <tr>
                    <td style="padding: 8px;">Website URL</td>
                    <td style="padding: 8px;"><code>{current_domain}</code></td>
                </tr>
                <tr>
                    <td style="padding: 8px;">Terms of Service (optional)</td>
                    <td style="padding: 8px;"><code>{current_domain}/terms</code></td>
                </tr>
                <tr>
                    <td style="padding: 8px;">Privacy Policy (optional)</td>
                    <td style="padding: 8px;"><code>{current_domain}/privacy</code></td>
                </tr>
            </table>
        </div>
        
        <div class="status info">
            <strong>📝 Setup Steps:</strong><br>
            1. Copy the URLs above to your Twitter Developer Portal<br>
            2. Make sure app permissions are "Read and Write"<br>
            3. Click "Start OAuth Flow" below<br>
            4. Authorize the app on Twitter<br>
            5. Test with the buttons below
        </div>
        
        <h2>🚀 Authentication & Testing</h2>
        <div>
            {'<p style="color: green;">✅ OAuth completed! You can now test posting.</p>' if is_auth else '<button onclick="window.location.href=\'/oauth/start\'">🔐 Start OAuth Flow</button>'}
        </div>
        
        <h3>🧵 Test Thread Creation</h3>
        <button onclick="window.location.href='/test_thread?dry_run=true'" {'style="background-color: #28a745;"' if is_auth else 'disabled'}>
            🧪 Test Thread (Simulation)
        </button>
        <button onclick="window.location.href='/test_thread?dry_run=false'" {'style="background-color: #dc3545;"' if is_auth else 'disabled'}>
            🚀 Test Thread (Real Post)
        </button>
        
        <h2>📋 Available Endpoints</h2>
        <ul>
            <li><code>GET /oauth/start</code> - Start OAuth authentication</li>
            <li><code>GET /oauth/status</code> - Check authentication status</li>
            <li><code>POST /test_thread</code> - Test thread creation</li>
            <li><code>POST /a2a/receive</code> - Receive contradiction reports</li>
            <li><code>GET /a2a/status</code> - Agent status</li>
            <li><code>GET /terms</code> - Terms of Service</li>
            <li><code>GET /privacy</code> - Privacy Policy</li>
        </ul>
        
        <div class="status warning">
            <strong>⚠️ Important:</strong> Make sure your Twitter app has "Read and Write" permissions and the callback URLs match exactly.
        </div>
    </body>
    </html>
    """
    
    return html

@app.route('/terms')
def terms():
    """Terms of Service page for Twitter app configuration"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Terms of Service - Media Analysis Bot</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
            h1 { color: #1da1f2; }
        </style>
    </head>
    <body>
        <h1>Terms of Service</h1>
        <p><strong>Last updated:</strong> December 2024</p>
        
        <h2>1. Service Description</h2>
        <p>This bot analyzes media reports and posts analytical threads about contradictions in news coverage.</p>
        
        <h2>2. User Consent</h2>
        <p>By authorizing this application, you consent to automated posting of analytical content to your Twitter account.</p>
        
        <h2>3. Data Usage</h2>
        <p>This application only posts analytical content and does not store personal data beyond authentication tokens.</p>
        
        <h2>4. Contact</h2>
        <p>For questions about these terms, contact the application administrator.</p>
        
        <p><a href="/">← Back to Home</a></p>
    </body>
    </html>
    """
    return html

@app.route('/privacy')
def privacy():
    """Privacy Policy page for Twitter app configuration"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Privacy Policy - Media Analysis Bot</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
            h1 { color: #1da1f2; }
        </style>
    </head>
    <body>
        <h1>Privacy Policy</h1>
        <p><strong>Last updated:</strong> December 2024</p>
        
        <h2>1. Information We Collect</h2>
        <p>We collect only the minimum information necessary to operate:</p>
        <ul>
            <li>Twitter OAuth tokens for posting authorization</li>
            <li>Basic account information for authentication</li>
        </ul>
        
        <h2>2. How We Use Information</h2>
        <p>Information is used solely to:</p>
        <ul>
            <li>Authenticate with Twitter's API</li>
            <li>Post analytical content to authorized accounts</li>
        </ul>
        
        <h2>3. Data Retention</h2>
        <p>OAuth tokens are stored temporarily during the session and are not permanently retained.</p>
        
        <h2>4. Data Sharing</h2>
        <p>We do not share your data with third parties beyond Twitter's API for posting functionality.</p>
        
        <h2>5. Contact</h2>
        <p>For privacy questions, contact the application administrator.</p>
        
        <p><a href="/">← Back to Home</a></p>
    </body>
    </html>
    """
    return html

# A2A Routes (unchanged)
@app.route('/a2a/receive', methods=['POST'])
def receive_a2a_message():
    """Endpoint to receive A2A messages"""
    message = request.json
    
    print(f"📨 Received A2A message: {message['message_type']}")
    
    # Process the message
    if message['message_type'] == 'contradiction_report':
        # Check if authenticated first
        if not twitter_creator.oauth_manager.is_authenticated():
            return jsonify({
                'status': 'error',
                'message_id': message['message_id'],
                'error': 'Not authenticated. Complete OAuth flow first.',
                'auth_url': '/oauth/start'
            }), 401
        
        # Process Twitter posting
        contradiction_data = message['payload']
        
        print("🐦 Received contradiction report, creating Twitter thread...")
        try:
            result = twitter_creator.process_contradiction_and_tweet(
                contradiction_data, 
                style="engaging", 
                dry_run=False  # Set to False for real posting
            )
            print(f"✅ Twitter thread result: {result['status']}")
            
            response = {
                'status': 'received',
                'message_id': message['message_id'],
                'timestamp': datetime.now().isoformat(),
                'processing_result': result
            }
            
        except Exception as e:
            print(f"❌ Error creating Twitter thread: {e}")
            response = {
                'status': 'error',
                'message_id': message['message_id'],
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    else:
        response = {
            'status': 'received',
            'message_id': message['message_id'],
            'timestamp': datetime.now().isoformat()
        }
    
    return jsonify(response)

@app.route('/a2a/status', methods=['GET'])
def a2a_status():
    """Get A2A agent status"""
    return jsonify({
        'agent_id': twitter_creator.agent_id,
        'agent_name': twitter_creator.agent_name,
        'status': 'active',
        'capabilities': ['contradiction_reporting', 'twitter_posting', 'thread_creation'],
        'authentication_status': 'authenticated' if twitter_creator.oauth_manager.is_authenticated() else 'not_authenticated',
        'oauth_endpoints': {
            'start_auth': '/oauth/start',
            'check_status': '/oauth/status'
        },
        'version': 'vercel_oauth2_enabled'
    })

@app.route('/test_thread', methods=['POST'])
def test_thread():
    """Test endpoint to create a sample Twitter thread"""
    
    # Check authentication first for real posting
    dry_run = request.args.get('dry_run', 'true').lower() == 'true'
    
    if not dry_run and not twitter_creator.oauth_manager.is_authenticated():
        return jsonify({
            'status': 'error',
            'message': 'Not authenticated. Complete OAuth flow first.',
            'auth_url': '/oauth/start'
        }), 401
    
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
        }],
        'aggregate_statistics': {
            'total_contradictions_found': 1
        }
    }
    
    try:
        result = twitter_creator.process_contradiction_and_tweet(sample_data, style="engaging", dry_run=dry_run)
        return jsonify({
            'status': 'success',
            'message': f'Test thread {"simulated" if dry_run else "posted"} successfully',
            'result': result
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Modified for Vercel deployment
if __name__ == '__main__':
    print("🐦 Starting Twitter Bot with OAuth 2.0...")
    print("🌐 Vercel deployment ready")
    print("📡 A2A Protocol enabled")
    print("🔐 OAuth endpoints available")
    print("🧵 Thread testing available")
    print("📨 A2A endpoint: /a2a/receive")
    print("📊 Status: /a2a/status")
    print()
    print("🚀 SETUP INSTRUCTIONS:")
    print("   1. Deploy to Vercel to get live URLs")
    print("   2. Update REDIRECT_URI with your Vercel URL")
    print("   3. Configure Twitter app with live URLs")
    print("   4. Visit your live site and complete OAuth")
    print("   5. Test with simulated thread first")
    print("   6. Then try real posting!")
    
    # For Vercel deployment
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port)