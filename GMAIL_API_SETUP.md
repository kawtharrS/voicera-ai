# Gmail API Setup Guide

## Overview

The Gmail agent requires OAuth 2.0 credentials to access Gmail API. This guide walks you through setting up the necessary credentials.

---

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click the project dropdown at the top
3. Click **NEW PROJECT**
4. Enter project name: `Voicera`
5. Click **CREATE**
6. Wait for the project to be created (may take a minute)

---

## Step 2: Enable Gmail API

1. In Google Cloud Console, search for **Gmail API** in the search bar
2. Click on **Gmail API**
3. Click **ENABLE**
4. Wait for it to enable

---

## Step 3: Create OAuth 2.0 Credentials

### 3A: Configure OAuth Consent Screen

1. In Google Cloud Console, go to **APIs & Services** → **Credentials**
2. Click **CONFIGURE CONSENT SCREEN** (blue button)
3. Select **External** as the user type
4. Click **CREATE**
5. Fill in the OAuth consent screen form:
   - **App name**: `Voicera`
   - **User support email**: your email
   - **Developer contact information**: your email
6. Click **SAVE AND CONTINUE**
7. On **Scopes** page:
   - Click **ADD OR REMOVE SCOPES**
   - In the search box, paste: `https://www.googleapis.com/auth/gmail.modify`
   - Check the box next to **Gmail API** scopes (it should show Gmail API with .modify scope)
   - Click **UPDATE**
8. Click **SAVE AND CONTINUE**
9. On **Test users** page, click **ADD USERS**
10. Add your Google email address
11. Click **SAVE AND CONTINUE**
12. Review your configuration and click **BACK TO DASHBOARD**

### 3B: Create OAuth Client Credentials

1. In **APIs & Services** → **Credentials**, click **+ CREATE CREDENTIALS**
2. Select **OAuth client ID**
3. Application type: **Desktop application**
4. Name: `Voicera Gmail Client`
5. Click **CREATE**
6. A modal will appear with your credentials
7. Click **DOWNLOAD JSON** (the download icon on the right)
8. Save this file as `credentials.json`

---

## Step 4: Place Credentials File

1. Move the downloaded `credentials.json` to one of these locations:

**Option A: Root of api folder** (recommended for API)

```
C:\Users\user\Desktop\Voicera\api\credentials.json
```

**Option B: Tools folder** (alternative location)

```
C:\Users\user\Desktop\Voicera\langgraph\src\tools\credentials.json
```

---

## Step 5: Update gmailTools.py Path (If Needed)

If your credentials are in a different location, update the path in [gmailTools.py](langgraph/src/tools/gmailTools.py):

```python
# Around line 33-34, update:
flow = InstalledAppFlow.from_client_secrets_file(
    'path/to/credentials.json', SCOPES)  # Add full path here
```

---

## Step 6: First Run Authentication

When you first run the Gmail agent:

1. A browser window will automatically open
2. Sign in with your Google account
3. Grant permission to access Gmail (read/write)
4. You'll be redirected to localhost
5. A `token.json` file will be automatically created
6. The token is saved for future runs

---

## Troubleshooting

### Error: "invalid_scope: Bad Request"

**Cause**: The Gmail API scope was not properly added to the OAuth consent screen.

**Solution**:

1. Go to [Google Cloud Console](https://console.cloud.google.com/) → **APIs & Services** → **OAuth consent screen**
2. Click **EDIT APP**
3. Go to **Scopes** section
4. Click **ADD OR REMOVE SCOPES**
5. Search for: `gmail.modify` or paste the full scope: `https://www.googleapis.com/auth/gmail.modify`
6. **Make sure it's checked** (highlighted in blue)
7. Click **UPDATE**
8. **Delete `token.json`** from your system (first run will re-authenticate with correct scopes)
9. Restart the API and try again

### Error: "[Errno 2] No such file or directory: 'credentials.json'"

**Solution**:

- Verify `credentials.json` is in the correct directory
- If running from `api/` folder, file should be at `api/credentials.json`
- If running from `langgraph/` folder, file should be at `langgraph/src/tools/credentials.json`
- Check the current working directory when starting the API

### Error: "Invalid client secret"

**Solution**:

- Download a new `credentials.json` from Google Cloud Console
- Make sure it's the OAuth 2.0 client secret, not a service account key
- **Important**: Do NOT use a service account key - it will fail with this error

### Error: "Redirect URI mismatch"

**Solution**:

- The authorized redirect URI should be `http://localhost:PORT` where PORT is any available port
- This is handled automatically by `InstalledAppFlow`
- Ensure you're not blocking localhost in your firewall

### Token.json issues

**Solution**:

- Delete `token.json` file
- Next run will trigger re-authentication
- New `token.json` will be created automatically

---

## File Locations Summary

After setup, you should have:

```
C:\Users\user\Desktop\Voicera\
├── api/
│   ├── credentials.json          ← Place here
│   ├── main.py
│   └── ...
├── langgraph/
│   ├── src/
│   │   ├── tools/
│   │   │   └── gmailTools.py
│   │   └── ...
│   └── token.json                ← Auto-created after first run
└── ...
```

---

## Testing Gmail Authentication

Once credentials are set up, test with this endpoint:

```bash
curl -X POST http://localhost:8000/gmail/test-categorize \
  -H "Content-Type: application/json" \
  -d '{
    "email_subject": "Test email",
    "email_body": "Testing Gmail setup"
  }'
```

---

## Security Notes

⚠️ **Important**:

- **Never commit** `credentials.json` or `token.json` to version control
- Both files are already in `.gitignore`
- Keep these files private and secure
- Use environment variables for production deployments

---

## Next Steps

1. ✅ Create Google Cloud Project
2. ✅ Enable Gmail API
3. ✅ Create OAuth 2.0 credentials
4. ✅ Download and place `credentials.json`
5. ✅ Run API and authenticate on first use
6. ✅ Verify with test endpoint

Once complete, your Gmail agent is ready to use!
