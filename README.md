# Gaza Media Fact-Check Multi-Agent System 🔍

A sophisticated fact-checking system that analyzes Gaza media coverage across Western and Arabic sources to detect contradictions using AI.

## ✨ Latest UI/UX Enhancements

### 🎨 Modern Dashboard Design
- **Glassmorphism UI**: Beautiful transparent design with backdrop blur effects
- **Gradient Backgrounds**: Modern purple gradient background for visual appeal
- **Responsive Design**: Fully responsive layout that works on all device sizes
- **Font Awesome Icons**: Professional icons throughout the interface
- **Smooth Animations**: Hover effects and loading animations for better UX

### 📊 Enhanced Data Visualization
- **Interactive Charts**: Real-time doughnut charts using Chart.js
- **Metric Cards**: Hover-animated cards showing key statistics
- **Visual Status Indicators**: Color-coded status messages with icons
- **Loading States**: Professional loading spinners with disabled states

### 🔍 Improved Analysis Display
- **Contradiction Cards**: Beautifully designed cards for each contradiction
- **Severity Badges**: Color-coded severity indicators (High/Medium/Low)
- **Side-by-Side Comparison**: Clean source comparison layout
- **AI Analysis Highlighting**: Special styling for AI-detected contradictions
- **Claim Comparison**: Side-by-side display of conflicting claims

### 📱 Mobile-First Design
- **Responsive Grid**: Adapts to different screen sizes automatically
- **Touch-Friendly**: Large tap targets and optimized mobile experience
- **Stack Layout**: Cards stack vertically on mobile devices
- **Optimized Typography**: Readable text at all screen sizes

### 🚀 Enhanced User Experience
- **Real-time Feedback**: Immediate visual feedback for user actions
- **Error Handling**: User-friendly error messages with suggestions
- **Keyboard Support**: Enter key triggers analysis
- **Progressive Loading**: Content loads progressively for better performance
- **Status Tracking**: Visual indication of system status

### 📋 New API Documentation
- **Interactive Docs**: Beautiful API documentation page at `/api/docs`
- **System Status**: Detailed system status at `/api/status`
- **Endpoint Explorer**: Complete overview of all available endpoints

## 🚨 Current Issues & Solutions

Based on the terminal output, here are the main issues and how to fix them:

### 1. **Twitter Agent Startup Failure** ❌
**Problem**: Twitter agent fails to start after 30 attempts due to rate limiting and invalid API keys.

**Solution**: 
- The system uses placeholder/demo Twitter API keys
- Run `python config_setup.py` to check your configuration
- Either configure real Twitter API keys OR use simulation mode

### 2. **Rate Limiting** ⏳
**Problem**: "Rate limit exceeded. Sleeping for 901 seconds."

**Solution**: ✅ **FIXED** 
- Fixed by removing the automatic posting test that triggers rate limits
- Twitter agent now starts without testing posting capabilities
- Uses simulation mode by default to prevent rate limit issues

### 3. **Async/Await Error** ⚠️
**Problem**: "RuntimeWarning: coroutine 'notify_twitter_agent' was never awaited"

**Solution**: ✅ **FIXED** 
- Updated the async notification to run properly in a background thread
- No more blocking Flask requests due to async issues

### 4. **Missing API Keys** 🔑
**Problem**: System uses placeholder Google AI and Twitter API keys.

**Solution**:
- **Google AI API**: REQUIRED - Get from https://aistudio.google.com/app/apikey
- **Twitter API**: OPTIONAL - Get from https://developer.twitter.com/en/portal/dashboard

## 🚀 Quick Start

### Option 1: Check Configuration First (Recommended)
```bash
python config_setup.py
```

### Option 2: Run with Current Settings (Simulation Mode)
```bash
python setup.py
```

The system will work in simulation mode even without proper API keys configured.

## 🔧 Configuration

### Required: Google AI API
1. Go to https://aistudio.google.com/app/apikey
2. Create an API key
3. Edit `app.py`, find line with `GOOGLE_API_KEY = "YOUR_GOOGLE_API_KEY_HERE"`
4. Replace with your actual key

### Optional: Twitter API (for live posting)
1. Go to https://developer.twitter.com/en/portal/dashboard
2. Create app with Read+Write permissions
3. Get API keys
4. Edit `twitter_agent.py` and replace the demo keys

## 📊 System Components

### Fact-Check Agent (Port 5000)
- ✅ **Working**: Analyzes Western vs Arabic media coverage
- ✅ **Working**: Detects contradictions using AI
- ✅ **Working**: Enhanced web dashboard at http://localhost:5000
- ✅ **NEW**: Interactive charts and modern UI design
- ✅ **NEW**: API documentation at http://localhost:5000/api/docs
- ⚠️ **Needs**: Google AI API key for full functionality

### Twitter Agent (Port 5001)
- ✅ **Working**: Receives contradiction reports
- ✅ **Working**: Creates tweet content
- ⚠️ **Simulation Mode**: Posts are simulated unless Twitter API configured
- 🔄 **Status**: Starts successfully now (fixed startup issues)

## 🎯 What Works Now

Even with the current issues:

1. **Enhanced fact-checking system** - analyzes media sources with beautiful UI
2. **Modern web dashboard** - accessible at http://localhost:5000 with professional design
3. **Twitter agent starts successfully** - runs in simulation mode
4. **A2A communication works** - agents communicate with each other
5. **Interactive data visualization** - real-time charts and metrics
6. **Mobile-responsive design** - works perfectly on all devices
7. **No more async errors** - fixed the coroutine issue

## 📱 New Features & Pages

### 🏠 Main Dashboard: http://localhost:5000
- Modern glassmorphism design
- Interactive analysis interface
- Real-time charts and metrics
- Mobile-responsive layout

### 📚 API Documentation: http://localhost:5000/api/docs
- Complete endpoint documentation
- System features overview
- Analysis process explanation
- Interactive design

### 📊 System Status: http://localhost:5000/api/status
- Real-time component status
- Performance metrics
- Agent connectivity check
- Configuration overview

## 📝 Current Status

```
✅ Fact-Check Agent: READY (Enhanced UI)
✅ Twitter Agent: READY (Simulation Mode)
✅ Web Dashboard: READY (Modern Design)
✅ A2A Communication: READY
✅ Data Visualization: READY (Charts & Metrics)
✅ Mobile Experience: READY (Responsive)
⚠️ Live Twitter Posting: Needs API Configuration
```

## 🛠️ Next Steps

1. **Run the system as-is**: It works in simulation mode with beautiful UI
2. **Configure Google AI API**: Required for fact-checking to work properly
3. **Configure Twitter API**: Optional, for live tweet posting
4. **Test the enhanced UI**: Experience the modern dashboard design

## 🔍 Testing the Enhanced UI

1. Start the system: `python setup.py`
2. Open browser: http://localhost:5000
3. Experience the new modern design:
   - Glassmorphism effects
   - Interactive charts
   - Animated loading states
   - Mobile-responsive layout
4. Enter search terms:
   - Western: "Gaza hospital strike"
   - Arabic: "قصف مستشفى غزة"
5. Click "Analyze Media Coverage"
6. View enhanced results with charts and visual comparisons

## 📞 Support

If you need help configuring API keys or encounter other issues:
1. Run `python config_setup.py` for detailed setup instructions
2. Check the terminal output for specific error messages
3. Review the configuration status in the output
4. Visit http://localhost:5000/api/docs for API documentation

## 🔐 Security Note

The current Twitter API keys in the code are demo/placeholder keys and should be replaced with your own for security and functionality.

## 🎨 UI/UX Design Features

### Visual Design
- **Modern Color Palette**: Professional blues, purples, and gradients
- **Typography**: Clean, readable fonts with proper hierarchy
- **Spacing**: Consistent padding and margins throughout
- **Shadows**: Subtle drop shadows for depth and layering

### Interactive Elements
- **Hover Effects**: Smooth transitions on interactive elements
- **Loading States**: Professional loading animations
- **Form Validation**: Real-time input validation and feedback
- **Button States**: Clear visual feedback for button interactions

### Data Presentation
- **Chart Integration**: Interactive doughnut charts for metrics
- **Card Layout**: Information presented in clean, organized cards
- **Color Coding**: Consistent color system for different types of data
- **Visual Hierarchy**: Clear information hierarchy with proper sizing

### Accessibility
- **Responsive Design**: Works on all screen sizes
- **High Contrast**: Good color contrast for readability
- **Keyboard Navigation**: Full keyboard support
- **Screen Reader Friendly**: Proper semantic HTML structure 