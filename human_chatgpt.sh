#!/usr/bin/env bash
# human_chatgpt.sh - Get a more human, conversational response from ChatGPT.
# Usage: ./human_chatgpt.sh "Your message here"

set -e

if [ -z "$OPENAI_API_KEY" ]; then
  echo "OPENAI_API_KEY environment variable not set" >&2
  exit 1
fi

prompt="$*"

curl -s https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d "$(jq -n --arg prompt "$prompt" '{
    model: "gpt-4o-mini",
    messages: [
      {role: "system", content: "Talk like a real, friendly human. Use natural phrasing, small hesitations, and informal tone while staying helpful."},
      {role: "user", content: $prompt}
    ]
  }')" | jq -r '.choices[0].message.content'
