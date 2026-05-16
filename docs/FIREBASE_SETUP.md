# Firebase Setup for Om (Google Login + Cloud Sync)

Free. No credit card. Takes 5 minutes.

## Step 1: Create a Firebase Project

1. Go to **https://console.firebase.google.com**
2. Click **"Create a project"** (or "Add project")
3. Project name: **`om-agent`** (or anything you like)
4. Disable Google Analytics (not needed) → **Create project**
5. Wait ~30 seconds → Click **Continue**

## Step 2: Enable Google Authentication

1. In the Firebase console, click **Authentication** (left sidebar)
2. Click **Get started**
3. Click **Google** under "Sign-in providers"
4. Toggle **Enable** → select your email as support email → **Save**

## Step 3: Create Firestore Database

1. Click **Firestore Database** (left sidebar)
2. Click **Create database**
3. Choose a location near your users (e.g., `us-central1` or `asia-south1`)
4. Select **Start in production mode** → **Create**
5. Go to the **Rules** tab, replace the rules with:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users can only read/write their own data
    match /users/{userId}/{document=**} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
  }
}
```

6. Click **Publish**

## Step 4: Add Web App & Get Config

1. Click the **gear icon** (Project settings) at the top left
2. Scroll down → Click **</>** (Add web app)
3. App nickname: **`om-web`** → **Register app**
4. You'll see a config block like this:

```javascript
const firebaseConfig = {
  apiKey: "AIzaSyB...",
  authDomain: "om-agent.firebaseapp.com",
  projectId: "om-agent",
  storageBucket: "om-agent.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abc123def456"
};
```

5. **Copy these values**

## Step 5: Add Config to Om

1. Open `docs/index.html`
2. Find the `FIREBASE_CONFIG` section (search for `FIREBASE_API_KEY_HERE`)
3. Replace the placeholder values with your real Firebase config:

```javascript
const FIREBASE_CONFIG = {
  apiKey: "AIzaSyB...",           // ← your apiKey
  authDomain: "om-agent.firebaseapp.com",  // ← your authDomain
  projectId: "om-agent",          // ← your projectId
  storageBucket: "om-agent.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abc123def456"
};
```

4. Save, commit, and push to GitHub:

```bash
git add docs/index.html
git commit -m "Add Firebase config for Google login"
git push origin main
```

## Step 6: Add GitHub Pages Domain to Firebase

1. In Firebase Console → **Authentication** → **Settings** tab
2. Under **Authorized domains**, click **Add domain**
3. Add: **`kdarshuchiha.github.io`**
4. Save

## Done!

Your Om app now has:
- ✅ Google Sign-In (one tap on mobile)
- ✅ Chat history synced across all devices
- ✅ API key encrypted and stored in the cloud
- ✅ Works offline too (falls back to localStorage)
- ✅ Firestore security rules ensure only you can read your data

## Cost

Firebase free tier (Spark plan) includes:
- **Unlimited** authentication users
- **1 GB** Firestore storage
- **50K reads/day**, **20K writes/day**

This is more than enough for personal use and hundreds of users.
