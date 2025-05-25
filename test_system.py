#!/usr/bin/env python3
"""
Quick test script to verify the Gaza Media Fact-Check System is working
"""

import requests
import json
import time

def test_health_checks():
    """Test if both agents are responding"""
    print("🔍 Testing system health...")
    
    # Test fact-check agent
    try:
        response = requests.get("http://localhost:5000/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Fact-Check Agent: HEALTHY")
        else:
            print(f"❌ Fact-Check Agent: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Fact-Check Agent: {e}")
        return False
    
    # Test Twitter agent
    try:
        response = requests.get("http://localhost:5001/a2a/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Twitter Agent: {data['status']} ({data['twitter_client_status']})")
        else:
            print(f"❌ Twitter Agent: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Twitter Agent: {e}")
        return False
    
    return True

def test_simple_analysis():
    """Test a simple media analysis"""
    print("\n🧪 Testing simple media analysis...")
    
    try:
        # Simple analysis request
        payload = {
            "western_query": "Gaza news",
            "arabic_query": "أخبار غزة"
        }
        
        print("📤 Sending analysis request...")
        response = requests.post(
            "http://localhost:5000/api/analyze", 
            json=payload, 
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Analysis completed: {data['status']}")
            print(f"   Western sources: {data['summary']['western_sources_analyzed']}")
            print(f"   Arabic sources: {data['summary']['arabic_sources_analyzed']}")
            print(f"   Matched pairs: {data['summary']['matched_pairs_found']}")
            print(f"   Contradictions: {data['summary'].get('contradictions_found', 0)}")
            
            return True
        else:
            print(f"❌ Analysis failed: HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        return False

def test_twitter_simulation():
    """Test Twitter agent simulation"""
    print("\n🐦 Testing Twitter agent simulation...")
    
    try:
        # Test simulation
        payload = {"dry_run": True}
        
        response = requests.post(
            "http://localhost:5001/test_tweet", 
            json=payload, 
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Twitter simulation: {data['status']}")
            print(f"   Live posting enabled: {data['live_posting_enabled']}")
            return True
        else:
            print(f"❌ Twitter simulation failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Twitter simulation error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Gaza Media Fact-Check System Test")
    print("=" * 50)
    
    # Test health
    if not test_health_checks():
        print("\n❌ System health check failed!")
        print("Make sure to run: python setup.py")
        return
    
    print("\n✅ System is healthy and running!")
    
    # Test basic functionality
    print("\n" + "="*50)
    
    # Test analysis (might take time)
    if test_simple_analysis():
        print("✅ Media analysis is working!")
    
    # Test Twitter simulation
    if test_twitter_simulation():
        print("✅ Twitter agent is working!")
    
    print("\n🎉 SYSTEM TEST COMPLETE!")
    print("=" * 50)
    print("📊 Dashboard: http://localhost:5000")
    print("🔧 API: http://localhost:5000/api/analyze")
    print("🐦 Twitter Agent: http://localhost:5001/a2a/status")

if __name__ == "__main__":
    main() 