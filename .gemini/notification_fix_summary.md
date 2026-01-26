# Push Notification Fix - Summary

## Problem
Mobile app was not sending push notifications after 1 minute when user expressed sadness, despite the emotion being correctly categorized as 'sadness' in the backend.

## Root Cause
**Emotion Mismatch**: The backend returns emotion categories as: `'joy'`, `'sadness'`, `'anger'`, `'fear'`, `'surprise'`, `'disgust'`, `'neutral'`, `'unknown'`

However, the mobile app was checking for: `'sad'`, `'angry'`, `'anxious'`, etc. (incorrect partial names)

When backend returned `'sadness'`, the mobile check for `'sad'` failed, so no notification was scheduled.

## Changes Made

### 1. Fixed Emotion Detection Logic (`voice_controller.dart`)
**Before:**
```dart
final negativeEmotions = ['sad', 'angry', 'anxious', 'depressed', 'frustrated', 'stressed', 'lonely', 'unhappy'];
```

**After:**
```dart
// Backend emotion categories: joy, sadness, anger, fear, surprise, disgust, neutral, unknown
final negativeEmotions = ['sadness', 'anger', 'fear', 'disgust'];
```

### 2. Added Notification Receivers (`AndroidManifest.xml`)
Added required receivers for background notification delivery:
- `ScheduledNotificationReceiver` - Handles notification delivery
- `ScheduledNotificationBootReceiver` - Reschedules notifications after device reboot

### 3. Enhanced Debugging (`notification_service.dart`)
Added detailed logging:
- Current time
- Scheduled notification time
- Time until notification (in seconds)
- Notification ID

## Testing Instructions

### 1. Clean Build
```bash
cd mobile
flutter clean
flutter pub get
flutter run
```

### 2. Test the Fix
1. Open the app and say "I'm feeling sad" or type it
2. Check the debug console for:
   ```
   Emotion detected: sadness
   Negative emotion detected: sadness. Scheduling check-in in 1 minute.
   === SCHEDULING NOTIFICATION ===
   Notification ID: X
   Current time: ...
   Schedule time: ...
   Time until notification: 60 seconds
   ✓ Check-in notification scheduled successfully
   ```
3. Wait 1 minute
4. You should receive a notification: "Checking In - How are you feeling now?"

### 3. Test Other Emotions
- **Sadness**: "I'm feeling sad", "I'm unhappy", "I feel down"
- **Anger**: "I'm angry", "I'm frustrated", "This makes me mad"
- **Fear**: "I'm anxious", "I'm worried", "I'm scared"
- **Disgust**: "That's disgusting", "I'm repulsed"

All should trigger a 1-minute notification.

### 4. Positive Emotions (Should NOT trigger notification)
- **Joy**: "I'm happy", "I feel great", "I'm excited"
- **Neutral**: "The weather is nice", "What time is it?"

## Permissions Required
Ensure these are granted on the device:
- Notification permission (POST_NOTIFICATIONS)
- Exact alarm permission (SCHEDULE_EXACT_ALARM) - For Android 12+

## Troubleshooting

### Issue: Still not receiving notifications
1. Check notification permissions in Settings > Apps > Voicera > Notifications
2. For Android 12+: Settings > Apps > Voicera > Set alarms and reminders (must be ON)
3. Check battery optimization: Settings > Apps > Voicera > Battery > Unrestricted

### Issue: Notifications delayed
- Some Android manufacturers (Samsung, Xiaomi, Huawei) have aggressive battery optimization
- Add app to "Don't optimize" list in battery settings

## Logs to Monitor
When a negative emotion is detected, you should see:
```
FastAPI Response - Emotion: 'sadness', Category: 'personal'
Converted Response - Emotion: 'sadness'
Emotion detected: sadness
Negative emotion detected: sadness. Scheduling check-in in 1 minute.
=== SCHEDULING NOTIFICATION ===
Notification ID: 1
Current time: 2026-01-26 10:41:00
Schedule time: 2026-01-26 10:42:00
Time until notification: 60 seconds
✓ Check-in notification scheduled successfully
```

## Files Modified
1. `mobile/lib/screens/chat/voice_controller.dart` - Fixed emotion matching
2. `mobile/android/app/src/main/AndroidManifest.xml` - Added notification receivers
3. `mobile/lib/services/notification_service.dart` - Enhanced logging
