#!/bin/bash

# AI Support Chatbot - Push to GitHub Script

echo "🚀 Pushing AI Support Chatbot to GitHub..."

# Configure Git (replace with your details)
git config --global user.name "DakshethG"
git config --global user.email "dakshith31@gmail.com"

# Add any remaining files
git add .
git commit -m "Final commit: Complete AI Support Chatbot ready for deployment"

# Push to GitHub
echo "📤 Pushing to https://github.com/DakshethG/AI_Support_Chatbot..."
git push -u origin main

echo "✅ Success! Your AI Support Chatbot is now on GitHub!"
echo "🌐 View at: https://github.com/DakshethG/AI_Support_Chatbot"