# TabBehavior Extension

A Chrome extension for real-time tracking of user tab behavior and sending data to a backend for AI analysis.

## Features

- Every 10s, gathers all open tabs
- Sends data to `http://localhost:8000/api/tabs` with a stored auth token
- Token managed via popup UI

## Setup

1. Clone this repo
2. Open `chrome://extensions`
3. Enable Developer Mode
4. Click “Load unpacked” and select this folder

## Server Endpoint

Expect POST to:

```json
POST /api/tabs
Authorization: Bearer <token>
Body: { "tabs": [ { "title": "...", "url": "...", "active": true } ] }
```
