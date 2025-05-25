from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import os
import json
import requests
import feedparser
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re
import time
import aiohttp
import uuid
from dataclasses import dataclass

# Import smolagents components
from smolagents import CodeAgent, tool

# Import Google Generative AI directly
import google.generativeai as genai

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Set your Google API key here
GOOGLE_API_KEY = "AIzaSyDwA6AGJp6SykOxNCJhT-vEzTcvzrmh93Q"

# Configure Google API directly
genai.configure(api_key=GOOGLE_API_KEY)


class A2AProtocol:
    """Agent-to-Agent communication protocol for fact-check agent"""
    
    def __init__(self, agent_id: str = "factcheck_agent_001", agent_name: str = "GazaFactCheckAgent"):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.message_queue = []
        self.session = None
    
    async def init_session(self):
        """Initialize HTTP session for A2A communication"""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close_session(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
    
    def create_message(self, message_type: str, payload: dict, target_agent: str = None) -> dict:
        """Create standardized A2A message"""
        return {
            'message_id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'source_agent': {
                'id': self.agent_id,
                'name': self.agent_name
            },
            'target_agent': target_agent,
            'message_type': message_type,
            'payload': payload,
            'protocol_version': '1.0'
        }
    
    async def send_message(self, target_url: str, message: dict) -> dict:
        """Send message to another agent"""
        await self.init_session()
        
        try:
            async with self.session.post(
                f"{target_url}/a2a/receive",
                json=message,
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"❌ A2A Message failed: {response.status}")
                    return {'status': 'error', 'message': f'HTTP {response.status}'}
        except Exception as e:
            print(f"❌ A2A Communication error: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def receive_message(self, message: dict) -> dict:
        """Process received A2A message"""
        print(f"📨 Received A2A message: {message['message_type']} from {message['source_agent']['name']}")
        
        # Add to message queue for processing
        self.message_queue.append(message)
        
        return {
            'status': 'received',
            'message_id': message['message_id'],
            'timestamp': datetime.now().isoformat()
        }


# Initialize A2A protocol
a2a_protocol = A2AProtocol()


@tool
def search_western_media_news(query: str = "Gaza Israel", hours_back: int = 24) -> list:
    """
    Search recent news from Western media outlets about Gaza/Israel conflict
    
    Args:
        query: Search keywords to look for in article titles and summaries
        hours_back: How many hours back to search for articles (default 24 hours)
        
    Returns:
        List of dictionaries containing article information (title, url, source, summary, published date)
    """
    print(f"🔍 Searching Western media for: '{query}' (last {hours_back} hours)")
    
    western_sources = {
        "CNN": "http://rss.cnn.com/rss/edition.rss",
        "BBC": "http://feeds.bbci.co.uk/news/world/middle_east/rss.xml",
        "Reuters": "https://feeds.reuters.com/reuters/worldNews",
        "AP News": "https://feeds.apnews.com/rss/apf-topnews",
        "Guardian": "https://www.theguardian.com/world/middleeast/rss",
        "Washington Post": "https://feeds.washingtonpost.com/rss/world",
        "New York Times": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"
    }
    
    all_articles = []
    cutoff_time = datetime.now() - timedelta(hours=hours_back)
    
    for source_name, rss_url in western_sources.items():
        try:
            print(f"  📰 Fetching {source_name}...")
            feed = feedparser.parse(rss_url)
            
            for entry in feed.entries[:10]:
                title_text = entry.get('title', '').lower()
                summary_text = entry.get('summary', '').lower()
                
                if any(keyword in title_text or keyword in summary_text 
                      for keyword in query.lower().split()):
                    
                    pub_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6])
                    
                    if pub_date and pub_date >= cutoff_time:
                        all_articles.append({
                            'title': entry.get('title', 'No title'),
                            'url': entry.get('link', ''),
                            'source': source_name,
                            'summary': entry.get('summary', 'No summary')[:500],
                            'published': pub_date.isoformat(),
                            'category': 'western_media'
                        })
                        
            print(f"    ✅ Found articles from {source_name}")
            
        except Exception as e:
            print(f"    ❌ Error with {source_name}: {e}")
            continue
    
    all_articles.sort(key=lambda x: x['published'], reverse=True)
    print(f"✅ Found {len(all_articles)} Western media articles")
    return all_articles[:10]


@tool
def search_arabic_media_news(query: str = "غزة إسرائيل", hours_back: int = 24) -> list:
    """
    Search recent news from Arabic media outlets about Gaza/Israel conflict
    
    Args:
        query: Search keywords in Arabic to look for in article titles and summaries
        hours_back: How many hours back to search for articles (default 24 hours)
        
    Returns:
        List of dictionaries containing Arabic article information (title, url, source, summary, published date)
    """
    print(f"🔍 Searching Arabic media for: '{query}' (last {hours_back} hours)")
    
    arabic_sources = {
        "Al Jazeera Arabic": "https://www.aljazeera.net/rss/all.xml",
        "BBC Arabic": "https://feeds.bbci.co.uk/arabic/rss.xml", 
        "RT Arabic": "https://arabic.rt.com/rss/",
        "Sky News Arabic": "https://www.skynewsarabia.com/rss.xml",
        "Al Arabiya": "https://www.alarabiya.net/ar/rss.xml"
    }
    
    all_articles = []
    cutoff_time = datetime.now() - timedelta(hours=hours_back)
    
    for source_name, rss_url in arabic_sources.items():
        try:
            print(f"  📰 Fetching {source_name}...")
            feed = feedparser.parse(rss_url)
            
            for entry in feed.entries[:15]:
                title_text = entry.get('title', '').lower()
                summary_text = entry.get('summary', '').lower()
                
                keywords = ['غزة', 'إسرائيل', 'فلسطين', 'gaza', 'israel', 'palestine']
                
                if any(keyword in title_text or keyword in summary_text 
                      for keyword in keywords):
                    
                    pub_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6])
                    
                    if pub_date and pub_date >= cutoff_time:
                        all_articles.append({
                            'title': entry.get('title', 'No title'),
                            'url': entry.get('link', ''),
                            'source': source_name,
                            'summary': entry.get('summary', 'No summary')[:500],
                            'published': pub_date.isoformat(),
                            'category': 'arabic_media'
                        })
                        
            print(f"    ✅ Found articles from {source_name}")
            
        except Exception as e:
            print(f"    ❌ Error with {source_name}: {e}")
            continue
    
    all_articles.sort(key=lambda x: x['published'], reverse=True)
    print(f"✅ Found {len(all_articles)} Arabic media articles")
    return all_articles[:10]


@tool
def find_matching_articles(western_articles_json: str, arabic_articles_json: str) -> str:
    """
    Use AI to intelligently find Western and Arabic articles that cover the same Gaza war events
    
    Args:
        western_articles_json: JSON string containing list of Western media articles
        arabic_articles_json: JSON string containing list of Arabic media articles
        
    Returns:
        JSON string containing AI-matched article pairs with semantic similarity and analysis
    """
    print("🤖 Using AI to find matching articles about Gaza war between Western and Arabic media...")
    
    try:
        western_articles = json.loads(western_articles_json) if isinstance(western_articles_json, str) else western_articles_json
        arabic_articles = json.loads(arabic_articles_json) if isinstance(arabic_articles_json, str) else arabic_articles_json
    except:
        return json.dumps({"error": "Invalid input format for articles"})
    
    # Use AI to analyze and match articles
    matching_prompt = f"""
You are an expert news analyst specializing in the Israeli war on Gaza. I need you to intelligently match Western and Arabic news articles that cover the same events or closely related incidents in this conflict.

**WESTERN ARTICLES:**
{json.dumps([{
    'id': i,
    'title': article['title'],
    'summary': article['summary'][:300],
    'source': article['source'],
    'published': article['published']
} for i, article in enumerate(western_articles)], indent=2)}

**ARABIC ARTICLES:**
{json.dumps([{
    'id': i,
    'title': article['title'], 
    'summary': article['summary'][:300],
    'source': article['source'],
    'published': article['published']
} for i, article in enumerate(arabic_articles)], indent=2)}

Please analyze these articles and identify which Western and Arabic articles are covering the same Gaza war events. Look for:

1. **Same specific incidents**: Military operations, strikes, casualties in same locations
2. **Same timeframe**: Events happening around the same time
3. **Same key figures**: Mentions of same officials, locations, or organizations
4. **Same casualty numbers**: Similar death/injury counts (even if slightly different)
5. **Same locations**: Gaza neighborhoods, hospitals, schools, etc.
6. **Related story developments**: Follow-ups, investigations, or responses to same events

For each match, consider:
- **Semantic similarity**: Do they describe the same underlying event?
- **Temporal proximity**: How close in time were they published?
- **Factual overlap**: Do they mention similar facts, numbers, or locations?
- **Story significance**: Major events vs minor incidents

Respond in JSON format with matched pairs:
{{
    "matches": [
        {{
            "western_article_id": 0,
            "arabic_article_id": 1,
            "confidence_score": 0.85,
            "matching_reason": "Both articles cover the same Israeli strike on Nasser Hospital in Khan Younis, with similar casualty numbers and timeframe",
            "shared_elements": ["Nasser Hospital", "Khan Younis", "Israeli strike", "15 casualties"],
            "time_proximity_hours": 3.5,
            "semantic_similarity": "high",
            "event_significance": "major"
        }}
    ],
    "analysis_summary": "Found X high-confidence matches covering major Gaza war events including hospital strikes, evacuation orders, and humanitarian situations"
}}

Be thorough but only match articles that genuinely appear to cover the same or very closely related events in the Gaza conflict.
"""

    try:
        print("🤖 Sending articles to AI for intelligent matching...")
        model = DirectGeminiModel("gemini-1.5-flash")
        ai_response = model.complete(matching_prompt)
        
        print("✅ AI matching analysis completed")
        
        # Parse AI response
        try:
            # Extract JSON from AI response
            if "```json" in ai_response:
                json_start = ai_response.find("```json") + 7
                json_end = ai_response.find("```", json_start)
                ai_response = ai_response[json_start:json_end].strip()
            elif "{" in ai_response:
                json_start = ai_response.find("{")
                json_end = ai_response.rfind("}") + 1
                ai_response = ai_response[json_start:json_end]
            
            ai_matches = json.loads(ai_response)
            
            # Convert AI matches to the format expected by the rest of the system
            formatted_matches = []
            
            for match in ai_matches.get('matches', []):
                western_id = match.get('western_article_id')
                arabic_id = match.get('arabic_article_id')
                
                if (western_id is not None and arabic_id is not None and 
                    western_id < len(western_articles) and arabic_id < len(arabic_articles)):
                    
                    western_article = western_articles[western_id]
                    arabic_article = arabic_articles[arabic_id]
                    
                    formatted_match = {
                        'western_article': western_article,
                        'arabic_article': arabic_article,
                        'match_score': match.get('confidence_score', 0.5) * 10,  # Convert to 0-10 scale
                        'ai_confidence': match.get('confidence_score', 0.5),
                        'matching_reason': match.get('matching_reason', 'AI detected semantic similarity'),
                        'shared_elements': match.get('shared_elements', []),
                        'time_proximity_hours': match.get('time_proximity_hours', 0),
                        'semantic_similarity': match.get('semantic_similarity', 'medium'),
                        'event_significance': match.get('event_significance', 'medium'),
                        'common_keywords': match.get('shared_elements', []),  # For backward compatibility
                        'western_numbers': [],  # Will be filled below
                        'arabic_numbers': []   # Will be filled below
                    }
                    
                    # Extract numbers for backward compatibility
                    western_text = f"{western_article['title']} {western_article['summary']}".lower()
                    arabic_text = f"{arabic_article['title']} {arabic_article['summary']}".lower()
                    
                    western_numbers = re.findall(r'\b(\d+)\s*(?:killed|dead|deaths|casualties)', western_text)
                    arabic_numbers = re.findall(r'\b(\d+)\s*(?:قتل|شهيد|killed|dead|deaths)', arabic_text)
                    
                    formatted_match['western_numbers'] = [int(n) for n in western_numbers]
                    formatted_match['arabic_numbers'] = [int(n) for n in arabic_numbers]
                    
                    formatted_matches.append(formatted_match)
                    
                    print(f"🎯 AI Match Found:")
                    print(f"   🇺🇸 Western: {western_article['source']} - {western_article['title'][:60]}...")
                    print(f"   🇵🇸 Arabic: {arabic_article['source']} - {arabic_article['title'][:60]}...")
                    print(f"   📊 Confidence: {match.get('confidence_score', 0.5):.2f}")
                    print(f"   🔗 Reason: {match.get('matching_reason', 'N/A')[:100]}...")
                    print()
            
            # Sort by AI confidence score
            formatted_matches.sort(key=lambda x: x['ai_confidence'], reverse=True)
            
            print(f"✅ AI found {len(formatted_matches)} high-quality matches")
            print(f"📈 Analysis: {ai_matches.get('analysis_summary', 'AI matching completed')}")
            
            return json.dumps(formatted_matches)
            
        except json.JSONDecodeError as e:
            print(f"⚠️ Could not parse AI response as JSON: {e}")
            print(f"Raw AI response: {ai_response[:500]}...")
            
            # Fallback to simple matching if AI response is not parseable
            return simple_fallback_matching(western_articles, arabic_articles)
            
    except Exception as e:
        print(f"❌ AI matching failed: {e}")
        # Fallback to simple matching
        return simple_fallback_matching(western_articles, arabic_articles)


def simple_fallback_matching(western_articles, arabic_articles):
    """Fallback matching method if AI fails"""
    print("🔄 Using fallback matching method...")
    
    matches = []
    
    for i, western_article in enumerate(western_articles):
        western_text = f"{western_article['title']} {western_article['summary']}".lower()
        
        # Simple keyword matching for Gaza war content
        gaza_keywords = ['gaza', 'غزة', 'israel', 'إسرائيل', 'palestinian', 'فلسطين', 
                        'hamas', 'حماس', 'strike', 'قصف', 'killed', 'قتل', 'hospital', 'مستشفى']
        
        best_match = None
        best_score = 0
        
        for j, arabic_article in enumerate(arabic_articles):
            arabic_text = f"{arabic_article['title']} {arabic_article['summary']}".lower()
            
            # Count common keywords
            score = sum(1 for keyword in gaza_keywords if keyword in western_text and keyword in arabic_text)
            
            # Time proximity bonus
            try:
                western_time = datetime.fromisoformat(western_article['published'].replace('Z', '+00:00'))
                arabic_time = datetime.fromisoformat(arabic_article['published'].replace('Z', '+00:00'))
                time_diff = abs((western_time - arabic_time).total_seconds() / 3600)
                if time_diff <= 12:  # Within 12 hours
                    score += 1
            except:
                pass
            
            if score > best_score and score >= 2:  # Minimum threshold
                best_score = score
                best_match = {
                    'western_article': western_article,
                    'arabic_article': arabic_article,
                    'match_score': score,
                    'ai_confidence': score / 10.0,  # Convert to confidence
                    'matching_reason': f'Fallback matching found {score} common Gaza war keywords',
                    'shared_elements': [kw for kw in gaza_keywords if kw in western_text and kw in arabic_text],
                    'semantic_similarity': 'medium',
                    'event_significance': 'medium',
                    'common_keywords': [],
                    'western_numbers': [],
                    'arabic_numbers': []
                }
        
        if best_match:
            matches.append(best_match)
    
    print(f"✅ Fallback matching found {len(matches)} matches")
    return json.dumps(matches)


@tool
def fetch_full_article_content(url: str) -> str:
    """
    Fetch the full content of a news article for deep AI analysis
    
    Args:
        url: URL of the article to fetch full content from
        
    Returns:
        JSON string containing the full article text or error message
    """
    print(f"📖 Fetching full content from: {url[:50]}...")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Try to find article content (common selectors)
        content_selectors = [
            'article', '.article-body', '.story-body', '.entry-content',
            '.post-content', '.content', '.article-content', '#article-body',
            '.article-text', '.story-content', '.post-text'
        ]
        
        article_text = ""
        for selector in content_selectors:
            content_div = soup.select_one(selector)
            if content_div:
                article_text = content_div.get_text(strip=True)
                break
        
        if not article_text:
            # Fallback: get all paragraph text
            paragraphs = soup.find_all('p')
            article_text = '\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        
        # Limit content length for AI processing
        article_text = article_text[:4000]  # Keep first 4000 characters
        
        print(f"✅ Fetched {len(article_text)} characters")
        
        return json.dumps({
            'url': url,
            'content': article_text,
            'length': len(article_text),
            'success': True
        })
        
    except Exception as e:
        print(f"❌ Error fetching {url}: {e}")
        return json.dumps({
            'url': url,
            'content': '',
            'error': str(e),
            'success': False
        })


@tool
def ai_analyze_article_contradictions(western_article_json: str, arabic_article_json: str, western_content_json: str, arabic_content_json: str) -> str:
    """
    Use AI to deeply analyze contradictions and differences between matched Western and Arabic articles
    
    Args:
        western_article_json: JSON string of Western article metadata
        arabic_article_json: JSON string of Arabic article metadata  
        western_content_json: JSON string of Western article full content
        arabic_content_json: JSON string of Arabic article full content
        
    Returns:
        JSON string containing detailed AI analysis with specific contradictions highlighted
    """
    print("🔍 Starting deep AI contradiction analysis...")
    
    try:
        western_article = json.loads(western_article_json)
        arabic_article = json.loads(arabic_article_json)
        western_content = json.loads(western_content_json)
        arabic_content = json.loads(arabic_content_json)
    except:
        return json.dumps({"error": "Invalid input format for AI analysis"})
    
    # Enhanced analysis prompt focusing on specific contradictions
    analysis_prompt = f"""
You are an expert fact-checker and media analyst specializing in the Gaza conflict. Analyze these two articles covering the same event and identify SPECIFIC CONTRADICTIONS with exact quotes and evidence.

**WESTERN ARTICLE ({western_article['source']}):**
Title: {western_article['title']}
URL: {western_article['url']}
Content: {western_content.get('content', 'Content not available')[:2500]}

**ARABIC ARTICLE ({arabic_article['source']}):**
Title: {arabic_article['title']}
URL: {arabic_article['url']}
Content: {arabic_content.get('content', 'Content not available')[:2500]}

FIND AND DOCUMENT SPECIFIC CONTRADICTIONS:

1. **FACTUAL CONTRADICTIONS** - Find exact discrepancies:
   - Different casualty numbers for the same incident
   - Different locations or timing of events
   - Conflicting accounts of what happened
   - Different identification of perpetrators/victims

2. **ATTRIBUTION CONTRADICTIONS** - Who is blamed/credited:
   - Different parties blamed for the same action
   - Different motivations attributed to actors
   - Conflicting accounts of responsibility

3. **SEQUENCE CONTRADICTIONS** - Order of events:
   - Different timelines of what happened when
   - Conflicting cause-and-effect relationships

4. **CONTEXT CONTRADICTIONS** - Background information:
   - Different historical context provided
   - Conflicting explanations of why events occurred

5. **SOURCE CONTRADICTIONS** - Information sources:
   - Different official statements quoted
   - Conflicting witness accounts
   - Different evidence presented

For each contradiction found, provide:
- EXACT QUOTES from both articles
- Clear explanation of the discrepancy
- Assessment of which version is more credible and why
- Potential reasons for the contradiction (bias, different sources, propaganda)

Respond in JSON format:
{{
    "contradiction_summary": {{
        "total_contradictions_found": 3,
        "severity_level": "high/medium/low",
        "main_discrepancy": "brief description of biggest contradiction"
    }},
    "specific_contradictions": [
        {{
            "contradiction_id": 1,
            "type": "factual/attribution/sequence/context/source",
            "category": "casualty_numbers/location/timing/responsibility/other",
            "severity": "critical/high/medium/low",
            "western_claim": {{
                "exact_quote": "exact text from western article",
                "context": "surrounding context of the quote",
                "source_attribution": "who/what is cited as source"
            }},
            "arabic_claim": {{
                "exact_quote": "exact text from arabic article (in original language if needed)",
                "english_translation": "english translation if arabic quote",
                "context": "surrounding context of the quote",
                "source_attribution": "who/what is cited as source"
            }},
            "discrepancy_explanation": "clear explanation of how these contradict each other",
            "credibility_assessment": {{
                "more_credible": "western/arabic/unclear",
                "reasoning": "why one seems more credible",
                "verification_status": "verifiable/unverifiable/conflicting_sources"
            }},
            "potential_causes": ["bias", "different_sources", "propaganda", "translation_error", "timing_difference"],
            "impact_on_understanding": "how this contradiction affects overall truth"
        }}
    ],
    "bias_patterns": {{
        "western_bias_indicators": [
            {{
                "bias_type": "language/sourcing/omission/emphasis",
                "example": "specific example from text",
                "explanation": "how this shows bias"
            }}
        ],
        "arabic_bias_indicators": [
            {{
                "bias_type": "language/sourcing/omission/emphasis", 
                "example": "specific example from text",
                "explanation": "how this shows bias"
            }}
        ]
    }},
    "information_gaps": {{
        "western_omissions": [
            {{
                "missing_info": "what important info is missing",
                "present_in_arabic": "corresponding info from arabic article",
                "significance": "why this omission matters"
            }}
        ],
        "arabic_omissions": [
            {{
                "missing_info": "what important info is missing", 
                "present_in_western": "corresponding info from western article",
                "significance": "why this omission matters"
            }}
        ]
    }},
    "overall_assessment": {{
        "reliability_ranking": "which_article_more_reliable",
        "truth_likelihood": "assessment of what probably actually happened",
        "reader_recommendation": "how readers should approach these conflicting accounts",
        "verification_needed": ["specific claims that need independent verification"]
    }}
}}

Be extremely thorough and specific. Use exact quotes and clear explanations for every contradiction identified."""
    
    # Use the DirectGeminiModel to analyze
    try:
        model = DirectGeminiModel("gemini-1.5-flash")
        
        print("🤖 Sending articles to AI for deep contradiction analysis...")
        ai_response = model.complete(analysis_prompt)
        
        print("✅ AI contradiction analysis completed")
        
        # Try to parse the AI response as JSON
        try:
            # Extract JSON from AI response if it's wrapped in text
            if "```json" in ai_response:
                json_start = ai_response.find("```json") + 7
                json_end = ai_response.find("```", json_start)
                ai_response = ai_response[json_start:json_end].strip()
            elif "{" in ai_response:
                json_start = ai_response.find("{")
                json_end = ai_response.rfind("}") + 1
                ai_response = ai_response[json_start:json_end]
            
            # Parse and validate the JSON
            analysis_result = json.loads(ai_response)
            
            # Add metadata and enhance for UI display
            analysis_result['ai_analysis'] = True
            analysis_result['analysis_timestamp'] = datetime.now().isoformat()
            analysis_result['articles_analyzed'] = {
                'western': {
                    'title': western_article['title'],
                    'source': western_article['source'],
                    'url': western_article['url']
                },
                'arabic': {
                    'title': arabic_article['title'],
                    'source': arabic_article['source'],
                    'url': arabic_article['url']
                }
            }
            
            # Log contradiction findings for debugging
            if 'specific_contradictions' in analysis_result:
                print(f"🔍 Found {len(analysis_result['specific_contradictions'])} specific contradictions:")
                for i, contradiction in enumerate(analysis_result['specific_contradictions'][:3]):  # Show first 3
                    print(f"   {i+1}. {contradiction.get('type', 'unknown')} - {contradiction.get('discrepancy_explanation', 'N/A')[:100]}...")
            
            return json.dumps(analysis_result)
            
        except json.JSONDecodeError:
            # If JSON parsing fails, return the raw AI analysis
            print("⚠️ AI response not in JSON format, returning raw analysis")
            return json.dumps({
                'ai_analysis': True,
                'raw_analysis': ai_response,
                'articles_analyzed': {
                    'western': western_article['title'],
                    'arabic': arabic_article['title']
                },
                'note': 'AI provided analysis in text format rather than structured JSON'
            })
            
    except Exception as e:
        print(f"❌ AI analysis error: {e}")
        return json.dumps({
            'error': f'AI analysis failed: {str(e)}',
            'fallback_available': True
        })


@tool
def comprehensive_contradiction_analysis(matches_json: str) -> str:
    """
    Perform comprehensive AI-powered contradiction analysis with detailed visualization data
    
    Args:
        matches_json: JSON string containing matched article pairs from find_matching_articles
        
    Returns:
        JSON string containing detailed AI contradiction analysis and visualization-ready data
    """
    print("🔍 Starting comprehensive AI contradiction analysis with visualization...")
    
    try:
        matches = json.loads(matches_json) if isinstance(matches_json, str) else matches_json
    except:
        return json.dumps({"error": "Invalid input format for matches"})
    
    all_contradictions = []
    
    # Analyze each matched pair with AI for contradictions
    for i, match in enumerate(matches[:3]):  # Limit to 3 pairs for performance
        western_article = match['western_article']
        arabic_article = match['arabic_article']
        
        print(f"\n🔍 Contradiction Analysis {i+1}/{min(len(matches), 3)}:")
        print(f"  🇺🇸 Western: {western_article['source']} - {western_article['title'][:60]}...")
        print(f"  🇵🇸 Arabic: {arabic_article['source']} - {arabic_article['title'][:60]}...")
        
        # Fetch full content for both articles
        print("📖 Fetching full article content for deep contradiction analysis...")
        western_content = fetch_full_article_content(western_article['url'])
        arabic_content = fetch_full_article_content(arabic_article['url'])
        
        # Perform detailed AI contradiction analysis
        contradiction_analysis_result = ai_analyze_article_contradictions(
            json.dumps(western_article),
            json.dumps(arabic_article), 
            western_content,
            arabic_content
        )
        
        contradiction_data = json.loads(contradiction_analysis_result)
        contradiction_data['match_id'] = i + 1
        contradiction_data['match_score'] = match.get('match_score', 0)
        
        all_contradictions.append(contradiction_data)
        
        # Log findings
        if 'specific_contradictions' in contradiction_data:
            contradictions_found = len(contradiction_data.get('specific_contradictions', []))
            print(f"🚨 Found {contradictions_found} specific contradictions in this pair")
        
        print(f"✅ Contradiction analysis {i+1} completed")
    
    # Calculate aggregate statistics
    total_contradictions = sum(len(analysis.get('specific_contradictions', [])) for analysis in all_contradictions)
    contradiction_types = {}
    severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
    
    for analysis in all_contradictions:
        for contradiction in analysis.get('specific_contradictions', []):
            cont_type = contradiction.get('type', 'unknown')
            severity = contradiction.get('severity', 'medium')
            
            contradiction_types[cont_type] = contradiction_types.get(cont_type, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
    
    # Combine everything with visualization-ready data
    result = {
        'ai_powered_analysis': True,
        'analysis_type': 'comprehensive_contradiction_analysis',
        'total_pairs_analyzed': len(all_contradictions),
        'detailed_contradictions': all_contradictions,
        'summary_insights': {'note': 'Summary insights generated'},
        'aggregate_statistics': {
            'total_contradictions_found': total_contradictions,
            'contradiction_types_distribution': contradiction_types,
            'severity_distribution': severity_counts,
            'average_contradictions_per_pair': total_contradictions / max(len(all_contradictions), 1)
        },
        'analysis_timestamp': datetime.now().isoformat(),
        'methodology': 'Deep AI analysis of full article content with specific contradiction identification and exact quote extraction'
    }
    
    print(f"\n✅ Comprehensive contradiction analysis complete!")
    print(f"   - {len(all_contradictions)} article pairs analyzed")
    print(f"   - {total_contradictions} specific contradictions identified")
    print(f"   - Contradiction types: {list(contradiction_types.keys())}")
    print(f"   - Severity breakdown: {severity_counts}")
    
    return json.dumps(result)


class DirectGeminiModel:
    """Custom model wrapper that uses Google's API directly, bypassing LiteLLM"""
    
    def __init__(self, model_name="gemini-1.5-flash"):
        self.model = genai.GenerativeModel(model_name)
        self.model_name = model_name
        print(f"✅ Initialized Direct Gemini Model: {model_name}")
    
    def generate(self, messages, **kwargs):
        """Generate method that smolagents expects"""
        try:
            # Extract the prompt from messages
            if isinstance(messages, list) and len(messages) > 0:
                # Get the last user message
                user_message = messages[-1]
                if isinstance(user_message, dict) and 'content' in user_message:
                    prompt = user_message['content']
                elif hasattr(user_message, 'content'):
                    prompt = user_message.content
                else:
                    prompt = str(user_message)
            else:
                prompt = str(messages)
            
            print(f"🤖 Gemini processing prompt: {prompt[:100]}...")
            
            # Generate response using Google's API
            response = self.model.generate_content(prompt)
            
            print(f"✅ Gemini response generated successfully")
            
            # Return in the format smolagents expects
            class MockResponse:
                def __init__(self, content):
                    self.content = content
                    
                def __str__(self):
                    return self.content
            
            return MockResponse(response.text)
            
        except Exception as e:
            print(f"❌ Direct Gemini error: {e}")
            # Return error response
            class MockResponse:
                def __init__(self, content):
                    self.content = content
                    
                def __str__(self):
                    return self.content
            
            return MockResponse(f"Error generating response: {str(e)}")
    
    def __call__(self, messages, **kwargs):
        """Handle direct calls to the model"""
        return self.generate(messages, **kwargs)
    
    def complete(self, prompt, **kwargs):
        """Alternative completion method"""
        try:
            print(f"🤖 Gemini completing prompt: {prompt[:100]}...")
            response = self.model.generate_content(str(prompt))
            print(f"✅ Gemini completion successful")
            return response.text
        except Exception as e:
            print(f"❌ Direct Gemini completion error: {e}")
            return f"Error: {str(e)}"


async def notify_twitter_agent(analysis_results: dict, twitter_agent_url: str = "http://localhost:5001"):
    """Send contradiction analysis to Twitter agent via A2A protocol"""
    
    print(f"📡 Notifying Twitter agent about contradictions...")
    
    # Create A2A message
    a2a_message = a2a_protocol.create_message(
        message_type="contradiction_report",
        payload=analysis_results,
        target_agent="twitter_agent"
    )
    
    # Send to Twitter agent
    response = await a2a_protocol.send_message(twitter_agent_url, a2a_message)
    
    if response.get('status') == 'received':
        print(f"✅ Twitter agent notified successfully")
    else:
        print(f"⚠️ Twitter agent notification failed: {response}")


def create_media_factcheck_agent():
    """Create a smolagents agent using direct Google API"""
    
    print("🤖 Creating agent with Direct Gemini Model...")
    
    # Create direct Gemini model (bypassing LiteLLM)
    model = DirectGeminiModel("gemini-1.5-flash")
    
    # Create agent with enhanced AI analysis tools
    agent = CodeAgent(
        tools=[
            search_western_media_news,
            search_arabic_media_news,
            find_matching_articles,
            fetch_full_article_content,
            ai_analyze_article_contradictions,
            comprehensive_contradiction_analysis
        ],
        model=model,
        max_steps=20  # Increased for more thorough AI analysis
    )
    
    print("✅ Agent created successfully with Direct Gemini integration!")
    return agent


@app.route('/')
def index():
    """Serve the enhanced dashboard page"""
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Gaza Media Fact-Check Dashboard</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
                line-height: 1.6;
            }
            
            .dashboard {
                max-width: 1400px;
                margin: 0 auto;
                display: grid;
                grid-template-columns: 1fr;
                gap: 20px;
            }
            
            .header {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 30px;
                text-align: center;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            
            .header h1 {
                color: #2c3e50;
                font-size: 2.5rem;
                font-weight: 700;
                margin-bottom: 10px;
                background: linear-gradient(45deg, #667eea, #764ba2);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            
            .header p {
                color: #6c757d;
                font-size: 1.1rem;
                margin-bottom: 20px;
            }
            
            .status-indicator {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                background: #d4edda;
                color: #155724;
                padding: 8px 16px;
                border-radius: 25px;
                font-size: 0.9rem;
                font-weight: 500;
            }
            
            .analysis-panel {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 30px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            
            .input-section {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin-bottom: 30px;
            }
            
            .form-group {
                position: relative;
            }
            
            .form-group label {
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                color: #2c3e50;
                font-size: 1rem;
            }
            
            .form-group input {
                width: 100%;
                padding: 15px 20px;
                border: 2px solid #e9ecef;
                border-radius: 12px;
                font-size: 1rem;
                transition: all 0.3s ease;
                background: rgba(255, 255, 255, 0.8);
            }
            
            .form-group input:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
                background: white;
            }
            
            .analyze-btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 15px 40px;
                border-radius: 12px;
                font-size: 1.1rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
                min-height: 55px;
                position: relative;
                overflow: hidden;
            }
            
            .analyze-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
            }
            
            .analyze-btn:active {
                transform: translateY(0);
            }
            
            .analyze-btn:disabled {
                opacity: 0.7;
                cursor: not-allowed;
                transform: none;
            }
            
            .loading-spinner {
                display: none;
                width: 20px;
                height: 20px;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-top: 2px solid white;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .results-container {
                display: none;
                margin-top: 30px;
            }
            
            .status-message {
                padding: 15px 20px;
                border-radius: 12px;
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                gap: 10px;
                font-weight: 500;
            }
            
            .status-success {
                background: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }
            
            .status-error {
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }
            
            .status-loading {
                background: #cce5f0;
                color: #0c5460;
                border: 1px solid #bee5eb;
            }
            
            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-bottom: 30px;
            }
            
            .metric-card {
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                padding: 20px;
                border-radius: 15px;
                text-align: center;
                border: 1px solid rgba(0, 0, 0, 0.05);
                transition: transform 0.3s ease;
            }
            
            .metric-card:hover {
                transform: translateY(-3px);
            }
            
            .metric-value {
                font-size: 2rem;
                font-weight: 700;
                color: #2c3e50;
                margin-bottom: 5px;
            }
            
            .metric-label {
                color: #6c757d;
                font-size: 0.9rem;
                font-weight: 500;
            }
            
            .chart-container {
                background: white;
                border-radius: 15px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
            }
            
            .contradictions-section {
                margin-top: 30px;
            }
            
            .contradiction-card {
                background: white;
                border-radius: 15px;
                padding: 25px;
                margin-bottom: 20px;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
                border-left: 4px solid #e74c3c;
                transition: all 0.3s ease;
            }
            
            .contradiction-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
            }
            
            .contradiction-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
            }
            
            .contradiction-title {
                font-size: 1.2rem;
                font-weight: 600;
                color: #2c3e50;
            }
            
            .severity-badge {
                padding: 5px 12px;
                border-radius: 20px;
                font-size: 0.8rem;
                font-weight: 600;
                text-transform: uppercase;
            }
            
            .severity-high { background: #fee; color: #dc3545; }
            .severity-medium { background: #fff3cd; color: #856404; }
            .severity-low { background: #d1ecf1; color: #0c5460; }
            
            .source-comparison {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin-bottom: 20px;
            }
            
            .source-card {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 12px;
                border: 1px solid #e9ecef;
            }
            
            .source-header {
                display: flex;
                align-items: center;
                gap: 10px;
                margin-bottom: 10px;
                font-weight: 600;
                color: #2c3e50;
            }
            
            .source-title {
                font-size: 0.95rem;
                line-height: 1.4;
                color: #495057;
                margin-bottom: 8px;
            }
            
            .source-url {
                font-size: 0.8rem;
                color: #6c757d;
                word-break: break-all;
            }
            
            .ai-contradictions {
                background: #fff8e1;
                border-radius: 10px;
                padding: 15px;
                border: 1px solid #ffe082;
            }
            
            .ai-contradiction-item {
                background: white;
                padding: 12px;
                border-radius: 8px;
                margin-bottom: 10px;
                border-left: 3px solid #ff9800;
            }
            
            .claim-comparison {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
                margin: 10px 0;
            }
            
            .claim-box {
                background: #f1f3f4;
                padding: 10px;
                border-radius: 8px;
                font-size: 0.9rem;
                line-height: 1.4;
            }
            
            .western-claim { border-left: 3px solid #3498db; }
            .arabic-claim { border-left: 3px solid #27ae60; }
            
            .no-results {
                text-align: center;
                padding: 40px;
                color: #6c757d;
                background: #f8f9fa;
                border-radius: 15px;
                margin-top: 20px;
            }
            
            @media (max-width: 768px) {
                .input-section {
                    grid-template-columns: 1fr;
                }
                
                .source-comparison {
                    grid-template-columns: 1fr;
                }
                
                .claim-comparison {
                    grid-template-columns: 1fr;
                }
                
                .metrics-grid {
                    grid-template-columns: repeat(2, 1fr);
                }
                
                .header h1 {
                    font-size: 2rem;
                }
            }
        </style>
    </head>
    <body>
        <div class="dashboard">
            <div class="header">
                <h1><i class="fas fa-search"></i> Gaza Media Fact-Check Dashboard</h1>
                <p>AI-powered analysis of media coverage contradictions between Western and Arabic sources</p>
                <div class="status-indicator">
                    <i class="fas fa-check-circle"></i>
                    System Online & Ready
                </div>
            </div>
            
            <div class="analysis-panel">
                <div class="input-section">
                    <div class="form-group">
                        <label for="western_query">
                            <i class="fas fa-globe-americas"></i> Western Media Query
                        </label>
                        <input type="text" id="western_query" value="Gaza hospital strike" 
                               placeholder="e.g., Gaza hospital strike, Israel operation">
                    </div>
                    
                    <div class="form-group">
                        <label for="arabic_query">
                            <i class="fas fa-globe-africa"></i> Arabic Media Query
                        </label>
                        <input type="text" id="arabic_query" value="قصف مستشفى غزة" 
                               placeholder="e.g., قصف مستشفى غزة، عملية إسرائيلية">
                    </div>
                </div>
                
                <button class="analyze-btn" onclick="analyzeMedia()" id="analyzeBtn">
                    <i class="fas fa-rocket" id="analyzeIcon"></i>
                    <span class="loading-spinner" id="loadingSpinner"></span>
                    <span id="btnText">Analyze Media Coverage</span>
                </button>
                
                <div class="results-container" id="resultsContainer">
                    <div id="statusMessage"></div>
                    <div id="metricsSection"></div>
                    <div id="chartSection"></div>
                    <div id="contradictionsSection"></div>
                </div>
            </div>
        </div>

        <script>
            let analysisData = null;

            function analyzeMedia() {
                const westernQuery = document.getElementById('western_query').value.trim();
                const arabicQuery = document.getElementById('arabic_query').value.trim();
                
                if (!westernQuery || !arabicQuery) {
                    showStatus('error', 'Please enter both Western and Arabic search queries');
                    return;
                }
                
                setLoadingState(true);
                showResults();
                showStatus('loading', 'Starting analysis... This may take 2-3 minutes. Please be patient.');
                
                clearResults();
                
                fetch('/api/analyze', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        western_query: westernQuery,
                        arabic_query: arabicQuery
                    })
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    return response.json();
                })
                .then(data => {
                    setLoadingState(false);
                    if (data.status === 'success') {
                        analysisData = data;
                        showStatus('success', 'Analysis completed successfully!');
                        displayMetrics(data.summary);
                        displayChart(data.summary);
                        displayContradictions(data.contradictions || []);
                        
                        if (data.summary.total_specific_contradictions > 0) {
                            showStatus('success', '🐦 Twitter agent has been notified about contradictions!', true);
                        }
                    } else {
                        showStatus('error', `Analysis failed: ${data.message || 'Unknown error'}`);
                    }
                })
                .catch(error => {
                    setLoadingState(false);
                    showStatus('error', `Request failed: ${error.message}`);
                    console.error('Analysis error:', error);
                });
            }
            
            function setLoadingState(loading) {
                const btn = document.getElementById('analyzeBtn');
                const icon = document.getElementById('analyzeIcon');
                const spinner = document.getElementById('loadingSpinner');
                const text = document.getElementById('btnText');
                
                btn.disabled = loading;
                
                if (loading) {
                    icon.style.display = 'none';
                    spinner.style.display = 'block';
                    text.textContent = 'Analyzing...';
                } else {
                    icon.style.display = 'block';
                    spinner.style.display = 'none';
                    text.textContent = 'Analyze Media Coverage';
                }
            }
            
            function showResults() {
                document.getElementById('resultsContainer').style.display = 'block';
            }
            
            function clearResults() {
                document.getElementById('metricsSection').innerHTML = '';
                document.getElementById('chartSection').innerHTML = '';
                document.getElementById('contradictionsSection').innerHTML = '';
            }
            
            function showStatus(type, message, append = false) {
                const statusDiv = document.getElementById('statusMessage');
                const iconMap = {
                    'success': 'fas fa-check-circle',
                    'error': 'fas fa-exclamation-triangle',
                    'loading': 'fas fa-spinner fa-spin'
                };
                
                const statusHtml = `
                    <div class="status-message status-${type}">
                        <i class="${iconMap[type]}"></i>
                        ${message}
                    </div>
                `;
                
                if (append) {
                    statusDiv.innerHTML += statusHtml;
                } else {
                    statusDiv.innerHTML = statusHtml;
                }
            }
            
            function displayMetrics(summary) {
                const metricsHtml = `
                    <div class="metrics-grid">
                        <div class="metric-card">
                            <div class="metric-value">${summary.western_sources_analyzed}</div>
                            <div class="metric-label">Western Sources</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">${summary.arabic_sources_analyzed}</div>
                            <div class="metric-label">Arabic Sources</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">${summary.matched_pairs_found}</div>
                            <div class="metric-label">Matched Pairs</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">${summary.total_specific_contradictions || 0}</div>
                            <div class="metric-label">Contradictions Found</div>
                        </div>
                    </div>
                `;
                document.getElementById('metricsSection').innerHTML = metricsHtml;
            }
            
            function displayChart(summary) {
                const chartHtml = `
                    <div class="chart-container">
                        <canvas id="analysisChart" width="400" height="200"></canvas>
                    </div>
                `;
                document.getElementById('chartSection').innerHTML = chartHtml;
                
                // Create chart
                const ctx = document.getElementById('analysisChart').getContext('2d');
                new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: ['Western Sources', 'Arabic Sources', 'Matched Pairs', 'Contradictions'],
                        datasets: [{
                            data: [
                                summary.western_sources_analyzed,
                                summary.arabic_sources_analyzed,
                                summary.matched_pairs_found,
                                summary.total_specific_contradictions || 0
                            ],
                            backgroundColor: [
                                '#3498db',
                                '#27ae60',
                                '#f39c12',
                                '#e74c3c'
                            ],
                            borderWidth: 0
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'bottom'
                            },
                            title: {
                                display: true,
                                text: 'Analysis Overview',
                                font: {
                                    size: 16,
                                    weight: 'bold'
                                }
                            }
                        }
                    }
                });
            }
            
            function displayContradictions(contradictions) {
                if (!contradictions || contradictions.length === 0) {
                    document.getElementById('contradictionsSection').innerHTML = `
                        <div class="no-results">
                            <i class="fas fa-info-circle" style="font-size: 2rem; margin-bottom: 10px; opacity: 0.5;"></i>
                            <h3>No Contradictions Found</h3>
                            <p>The analysis did not detect any significant contradictions between the matched articles.</p>
                        </div>
                    `;
                    return;
                }
                
                let contradictionsHtml = '<div class="contradictions-section"><h3><i class="fas fa-exclamation-triangle"></i> Detected Contradictions</h3>';
                
                contradictions.forEach((contradiction, index) => {
                    const severity = getSeverity(contradiction);
                    contradictionsHtml += `
                        <div class="contradiction-card">
                            <div class="contradiction-header">
                                <div class="contradiction-title">Contradiction #${index + 1}</div>
                                <div class="severity-badge severity-${severity}">${severity}</div>
                            </div>
                            
                            <div class="source-comparison">
                                <div class="source-card">
                                    <div class="source-header">
                                        <i class="fas fa-globe-americas"></i>
                                        Western Source
                                    </div>
                                    <div class="source-title">${contradiction.western_article.source}</div>
                                    <div class="source-title">${truncateText(contradiction.western_article.title, 120)}</div>
                                    <div class="source-url">${truncateText(contradiction.western_article.url, 60)}</div>
                                </div>
                                
                                <div class="source-card">
                                    <div class="source-header">
                                        <i class="fas fa-globe-africa"></i>
                                        Arabic Source
                                    </div>
                                    <div class="source-title">${contradiction.arabic_article.source}</div>
                                    <div class="source-title">${truncateText(contradiction.arabic_article.title, 120)}</div>
                                    <div class="source-url">${truncateText(contradiction.arabic_article.url, 60)}</div>
                                </div>
                            </div>
                            
                            ${displayAIContradictions(contradiction.ai_contradictions_found || [])}
                        </div>
                    `;
                });
                
                contradictionsHtml += '</div>';
                document.getElementById('contradictionsSection').innerHTML = contradictionsHtml;
            }
            
            function displayAIContradictions(aiContradictions) {
                if (!aiContradictions || aiContradictions.length === 0) {
                    return '<div style="text-align: center; color: #6c757d; padding: 15px;">No specific contradictions detected by AI analysis.</div>';
                }
                
                let html = '<div class="ai-contradictions"><h4><i class="fas fa-robot"></i> AI-Detected Contradictions</h4>';
                
                aiContradictions.forEach((contradiction, index) => {
                    html += `
                        <div class="ai-contradiction-item">
                            <div style="font-weight: 600; margin-bottom: 8px;">
                                ${contradiction.type || 'Factual'} Contradiction
                            </div>
                            <div class="claim-comparison">
                                <div class="claim-box western-claim">
                                    <strong>Western Claim:</strong><br>
                                    "${contradiction.western_claim?.exact_quote || contradiction.western_claim || 'N/A'}"
                                </div>
                                <div class="claim-box arabic-claim">
                                    <strong>Arabic Claim:</strong><br>
                                    "${contradiction.arabic_claim?.english_translation || contradiction.arabic_claim || 'N/A'}"
                                </div>
                            </div>
                            <div style="margin-top: 8px; font-size: 0.9rem; color: #6c757d;">
                                <strong>Analysis:</strong> ${contradiction.discrepancy_explanation || contradiction.significance || 'Contradiction detected by AI analysis'}
                            </div>
                        </div>
                    `;
                });
                
                html += '</div>';
                return html;
            }
            
            function getSeverity(contradiction) {
                if (contradiction.ai_contradictions_found && contradiction.ai_contradictions_found.length > 2) {
                    return 'high';
                } else if (contradiction.ai_contradictions_found && contradiction.ai_contradictions_found.length > 0) {
                    return 'medium';
                }
                return 'low';
            }
            
            function truncateText(text, maxLength) {
                if (!text) return 'N/A';
                return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
            }

            // Allow Enter key to trigger analysis
            document.addEventListener('DOMContentLoaded', function() {
                document.getElementById('western_query').addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') analyzeMedia();
                });
                document.getElementById('arabic_query').addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') analyzeMedia();
                });
            });
        </script>
    </body>
    </html>
    """)


@app.route('/api/analyze', methods=['POST'])
def analyze_coverage():
    """API endpoint to analyze media coverage using smolagents"""
    try:
        data = request.json
        western_query = data.get('western_query', 'Gaza Israel')
        arabic_query = data.get('arabic_query', 'غزة إسرائيل')
        
        print(f"📊 Starting analysis for: Western='{western_query}', Arabic='{arabic_query}'")
        
        # Get western articles
        western_articles = search_western_media_news(western_query, 24)
        print(f"📰 Got {len(western_articles)} Western articles")
        
        # Get Arabic articles  
        arabic_articles = search_arabic_media_news(arabic_query, 24)
        print(f"📰 Got {len(arabic_articles)} Arabic articles")
        
        # Find matches
        matches_json = find_matching_articles(json.dumps(western_articles), json.dumps(arabic_articles))
        matches = json.loads(matches_json)
        print(f"🔗 Found {len(matches)} matched pairs")
        
        if matches:
            # Analyze contradictions with AI
            print("🤖 Running AI-powered contradiction analysis...")
            ai_analysis_json = comprehensive_contradiction_analysis(matches_json)
            ai_analysis_data = json.loads(ai_analysis_json)
            
            # Extract terminology for display
            western_terms = ['military operation', 'targeted strike', 'casualties', 'investigation', 'security response']
            arabic_terms = ['عملية عسكرية', 'قصف', 'شهداء', 'اعتداء', 'مقاومة']
            
            # Format contradictions for UI
            formatted_contradictions = []
            for ai_analysis in ai_analysis_data.get('detailed_contradictions', []):
                if 'articles_analyzed' in ai_analysis:
                    formatted_contradiction = {
                        'match_id': ai_analysis.get('match_id', 1),
                        'western_article': {
                            'title': ai_analysis['articles_analyzed']['western']['title'],
                            'source': ai_analysis['articles_analyzed']['western']['source'],
                            'url': ai_analysis['articles_analyzed']['western']['url']
                        },
                        'arabic_article': {
                            'title': ai_analysis['articles_analyzed']['arabic']['title'],
                            'source': ai_analysis['articles_analyzed']['arabic']['source'],
                            'url': ai_analysis['articles_analyzed']['arabic']['url']
                        },
                        'ai_contradictions_found': ai_analysis.get('specific_contradictions', [])
                    }
                    formatted_contradictions.append(formatted_contradiction)
            
            print(f"🤖 Formatted {len(formatted_contradictions)} AI analyses for UI")
            
            # Auto-notify Twitter agent if significant contradictions found
            total_contradictions = ai_analysis_data.get('aggregate_statistics', {}).get('total_contradictions_found', 0)
            if total_contradictions > 0:
                print(f"📡 {total_contradictions} contradictions found - notifying Twitter agent...")
                try:
                    import asyncio
                    import threading
                    
                    def run_async_notify():
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            loop.run_until_complete(notify_twitter_agent(ai_analysis_data))
                        finally:
                            loop.close()
                    
                    # Run in background thread to avoid blocking
                    thread = threading.Thread(target=run_async_notify)
                    thread.daemon = True
                    thread.start()
                    
                except Exception as e:
                    print(f"⚠️ Could not notify Twitter agent: {e}")
            
            # Format response for UI
            response = {
                'status': 'success',
                'western_articles': western_articles,
                'arabic_articles': arabic_articles,
                'matches': matches,
                'fact_checks': [
                    {
                        'topic': 'AI-Powered Contradiction Analysis',
                        'analysis': f'Deep AI analysis of {len(formatted_contradictions)} matched article pairs',
                        'details': f'Found {total_contradictions} specific contradictions',
                        'western_terms': western_terms,
                        'arabic_terms': arabic_terms
                    }
                ],
                'contradictions': formatted_contradictions,
                'summary': {
                    'western_sources_analyzed': len(western_articles),
                    'arabic_sources_analyzed': len(arabic_articles),
                    'matched_pairs_found': len(matches),
                    'contradictions_found': len(formatted_contradictions),
                    'total_specific_contradictions': total_contradictions,
                    'fact_checks_performed': 1,
                    'analysis_timestamp': datetime.now().isoformat(),
                    'analysis_type': 'AI-powered deep contradiction analysis'
                }
            }
            
            print("✅ Response formatted successfully for UI")
            return jsonify(response)
        
        else:
            return jsonify({
                'status': 'success',
                'message': 'No matching articles found between Western and Arabic sources',
                'western_articles': western_articles,
                'arabic_articles': arabic_articles,
                'matches': [],
                'contradictions': [],
                'fact_checks': [],
                'summary': {
                    'western_sources_analyzed': len(western_articles),
                    'arabic_sources_analyzed': len(arabic_articles),
                    'matched_pairs_found': 0,
                    'contradictions_found': 0,
                    'fact_checks_performed': 0,
                    'analysis_timestamp': datetime.now().isoformat()
                }
            })
        
    except Exception as e:
        print(f"❌ Error in analysis: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'western_articles': [],
            'arabic_articles': [],
            'matches': [],
            'fact_checks': [],
            'contradictions': [],
            'summary': {
                'western_sources_analyzed': 0,
                'arabic_sources_analyzed': 0,
                'matched_pairs_found': 0,
                'contradictions_found': 0,
                'fact_checks_performed': 0
            }
        }), 500


@app.route('/a2a/receive', methods=['POST'])
def receive_a2a_message():
    """Endpoint to receive A2A messages from other agents"""
    message = request.json
    response = a2a_protocol.receive_message(message)
    
    # Process different message types
    if message['message_type'] == 'analysis_request':
        payload = message['payload']
        
        if payload.get('request_type') == 'contradiction_analysis':
            # Queue analysis request
            western_query = payload.get('western_query', 'Gaza Israel')
            arabic_query = payload.get('arabic_query', 'غزة إسرائيل')
            
            print(f"📨 Received analysis request via A2A: {western_query} / {arabic_query}")
            
            response['payload'] = {
                'status': 'analysis_queued',
                'estimated_completion': '2-3 minutes'
            }
    
    return jsonify(response)


@app.route('/a2a/status', methods=['GET']) 
def a2a_status():
    """Get A2A agent status"""
    return jsonify({
        'agent_id': a2a_protocol.agent_id,
        'agent_name': a2a_protocol.agent_name,
        'status': 'active',
        'capabilities': [
            'media_analysis', 
            'contradiction_detection', 
            'bias_analysis', 
            'fact_checking'
        ],
        'message_queue_size': len(a2a_protocol.message_queue),
        'connected_agents': ['twitter_agent'],
        'analysis_endpoints': ['/api/analyze', '/a2a/trigger_analysis']
    })


@app.route('/a2a/trigger_analysis', methods=['POST'])
def trigger_a2a_analysis():
    """Manually trigger analysis and send to Twitter agent"""
    data = request.json
    western_query = data.get('western_query', 'Gaza Israel') 
    arabic_query = data.get('arabic_query', 'غزة إسرائيل')
    
    try:
        print(f"🔍 A2A Triggered analysis: {western_query} / {arabic_query}")
        
        # Get articles and matches
        western_articles = search_western_media_news(western_query, 24)
        arabic_articles = search_arabic_media_news(arabic_query, 24)
        matches_json = find_matching_articles(json.dumps(western_articles), json.dumps(arabic_articles))
        matches = json.loads(matches_json)
        
        if matches:
            # Run contradiction analysis
            ai_analysis_json = comprehensive_contradiction_analysis(matches_json)
            ai_analysis_data = json.loads(ai_analysis_json)
            
            # Send to Twitter agent via A2A
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(notify_twitter_agent(ai_analysis_data))
            loop.close()
            
            return jsonify({
                'status': 'success',
                'analysis_completed': True,
                'contradictions_found': ai_analysis_data.get('aggregate_statistics', {}).get('total_contradictions_found', 0),
                'twitter_notified': True,
                'analysis_data': ai_analysis_data
            })
        else:
            return jsonify({
                'status': 'no_matches',
                'message': 'No matching articles found for analysis'
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'message': 'Gaza Media Fact-Check API with smolagents is running',
        'a2a_enabled': True,
        'connected_agents': ['twitter_agent']
    })


@app.route('/api/docs')
def api_docs():
    """Serve API documentation page"""
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>API Documentation - Gaza Media Fact-Check</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
                line-height: 1.6;
                margin: 0;
            }
            .container {
                max-width: 1000px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 30px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            }
            h1 { color: #2c3e50; text-align: center; margin-bottom: 30px; }
            h2 { color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
            .endpoint { background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 15px 0; }
            .method { font-weight: bold; color: #27ae60; }
            .url { font-family: monospace; background: #e9ecef; padding: 5px 10px; border-radius: 5px; }
            .back-btn { 
                display: inline-block; 
                background: #3498db; 
                color: white; 
                padding: 10px 20px; 
                text-decoration: none; 
                border-radius: 5px; 
                margin-bottom: 20px; 
            }
            .status-indicator {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                background: #d4edda;
                color: #155724;
                padding: 8px 16px;
                border-radius: 25px;
                font-size: 0.9rem;
                font-weight: 500;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-btn"><i class="fas fa-arrow-left"></i> Back to Dashboard</a>
            
            <h1><i class="fas fa-book"></i> API Documentation</h1>
            
            <div class="status-indicator">
                <i class="fas fa-check-circle"></i>
                System Online & Ready
            </div>
            
            <h2>Available Endpoints</h2>
            
            <div class="endpoint">
                <h3><span class="method">GET</span> <span class="url">/</span></h3>
                <p>Main dashboard interface for analyzing Gaza media coverage</p>
            </div>
            
            <div class="endpoint">
                <h3><span class="method">POST</span> <span class="url">/api/analyze</span></h3>
                <p>Analyze media coverage contradictions between Western and Arabic sources</p>
                <strong>Request Body:</strong>
                <pre>{
  "western_query": "Gaza hospital strike",
  "arabic_query": "قصف مستشفى غزة"
}</pre>
                <strong>Response:</strong> Analysis results with contradictions, matched pairs, and AI insights
            </div>
            
            <div class="endpoint">
                <h3><span class="method">GET</span> <span class="url">/api/health</span></h3>
                <p>System health check endpoint</p>
                <strong>Response:</strong> System status and configuration information
            </div>
            
            <div class="endpoint">
                <h3><span class="method">GET</span> <span class="url">/a2a/status</span></h3>
                <p>Agent-to-Agent communication status</p>
                <strong>Response:</strong> A2A protocol status and connected agents
            </div>
            
            <div class="endpoint">
                <h3><span class="method">POST</span> <span class="url">/a2a/trigger_analysis</span></h3>
                <p>Manually trigger analysis via A2A protocol</p>
                <strong>Request Body:</strong>
                <pre>{
  "western_query": "Gaza news",
  "arabic_query": "أخبار غزة"
}</pre>
            </div>
            
            <h2>System Features</h2>
            <ul>
                <li><i class="fas fa-robot"></i> AI-powered contradiction detection using Google Gemini</li>
                <li><i class="fas fa-globe"></i> Multi-source media analysis (Western and Arabic)</li>
                <li><i class="fas fa-chart-bar"></i> Real-time data visualization with charts</li>
                <li><i class="fas fa-twitter"></i> Automated Twitter notification system</li>
                <li><i class="fas fa-comments"></i> Agent-to-Agent communication protocol</li>
                <li><i class="fas fa-mobile-alt"></i> Responsive design for all devices</li>
            </ul>
            
            <h2>Analysis Process</h2>
            <ol>
                <li>Search Western media sources (CNN, BBC, Reuters, AP, Guardian, etc.)</li>
                <li>Search Arabic media sources (Al Jazeera, BBC Arabic, RT Arabic, etc.)</li>
                <li>AI-powered article matching based on semantic similarity</li>
                <li>Deep content analysis for contradiction detection</li>
                <li>Generate detailed reports with exact quotes and discrepancies</li>
                <li>Notify Twitter agent for public disclosure</li>
            </ol>
        </div>
    </body>
    </html>
    """)


@app.route('/api/status')
def system_status():
    """Detailed system status endpoint"""
    try:
        # Test Google AI connection
        model = DirectGeminiModel("gemini-1.5-flash")
        test_response = model.complete("Test")
        google_ai_status = "operational" if test_response else "error"
    except:
        google_ai_status = "error"
    
    # Test Twitter agent connection
    try:
        import requests
        response = requests.get("http://localhost:5001/a2a/status", timeout=2)
        twitter_agent_status = "operational" if response.status_code == 200 else "error"
        twitter_data = response.json() if response.status_code == 200 else {}
    except:
        twitter_agent_status = "error"
        twitter_data = {}
    
    return jsonify({
        'system_status': 'operational',
        'timestamp': datetime.now().isoformat(),
        'components': {
            'fact_check_agent': {
                'status': 'operational',
                'port': 5000,
                'capabilities': ['media_analysis', 'contradiction_detection', 'ai_analysis']
            },
            'twitter_agent': {
                'status': twitter_agent_status,
                'port': 5001,
                'posting_enabled': twitter_data.get('posting_enabled', False),
                'mode': twitter_data.get('twitter_client_status', 'unknown')
            },
            'google_ai': {
                'status': google_ai_status,
                'model': 'gemini-1.5-flash',
                'integration': 'direct_api'
            },
            'a2a_protocol': {
                'status': 'operational',
                'message_queue_size': len(a2a_protocol.message_queue),
                'connected_agents': ['twitter_agent']
            }
        },
        'endpoints': {
            'dashboard': 'http://localhost:5000/',
            'api_analyze': 'http://localhost:5000/api/analyze',
            'api_docs': 'http://localhost:5000/api/docs',
            'health_check': 'http://localhost:5000/api/health',
            'twitter_agent': 'http://localhost:5001/a2a/status'
        }
    })



if __name__ == '__main__':
    print("🚀 Starting Gaza Media Fact-Check Server with Direct Gemini Integration...")
    print("📊 Dashboard available at: http://localhost:5000")
    print("🔧 API endpoint: http://localhost:5000/api/analyze")
    print("📡 A2A Protocol enabled at: http://localhost:5000/a2a/")
    print("🐦 Twitter agent communication: http://localhost:5001")
    print("❤️  Health check: http://localhost:5000/api/health")
    print("🤖 Agent: smolagents with Direct Gemini 1.5 Flash")
    print("✅ Bypassing LiteLLM - using Google API directly")
    
    # Test the Gemini connection before starting server
    try:
        test_model = DirectGeminiModel()
        test_response = test_model.complete('Hello, can you respond with "Connection successful"?')
        if 'successful' in str(test_response).lower():
            print("✅ Gemini API connection test passed!")
        else:
            print("⚠️  Gemini API responding but test message may have failed")
            print(f"Response: {test_response}")
    except Exception as e:
        print(f"❌ Gemini API connection test failed: {e}")
        print("The server will still start, but AI analysis may not work")
    
    print("\n🔗 A2A Protocol Status:")
    print(f"   Agent ID: {a2a_protocol.agent_id}")
    print(f"   Agent Name: {a2a_protocol.agent_name}")
    print("   Capabilities: Media Analysis, Contradiction Detection, Fact Checking")
    
    app.run(debug=True, host='0.0.0.0', port=5000)