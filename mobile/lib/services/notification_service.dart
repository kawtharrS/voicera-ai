import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:timezone/data/latest.dart' as tz;
import 'package:timezone/timezone.dart' as tz;
import 'package:flutter/material.dart';

class NotificationService {
  static final NotificationService _instance = NotificationService._internal();
  static int _notificationId = 0;

  factory NotificationService() {
    return _instance;
  }

  NotificationService._internal();

  final FlutterLocalNotificationsPlugin flutterLocalNotificationsPlugin =
      FlutterLocalNotificationsPlugin();

  Future<void> init() async {
    tz.initializeTimeZones();

    const AndroidInitializationSettings initializationSettingsAndroid =
        AndroidInitializationSettings('@mipmap/ic_launcher');

    final InitializationSettings initializationSettings = InitializationSettings(
      android: initializationSettingsAndroid,
      iOS: DarwinInitializationSettings(),
    );

    await flutterLocalNotificationsPlugin.initialize(
      initializationSettings,
      onDidReceiveNotificationResponse: (NotificationResponse response) async {
        debugPrint('Notification tapped: ${response.payload}');
      },
    );
    
    await _createNotificationChannel();
    
    debugPrint('Notification service initialized');
  }
  
  Future<void> _createNotificationChannel() async {
    final AndroidFlutterLocalNotificationsPlugin? androidImplementation =
        flutterLocalNotificationsPlugin.resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>();

    if (androidImplementation != null) {
      await androidImplementation.createNotificationChannel(
        const AndroidNotificationChannel(
          'check_in_channel',
          'Emotional Check-In',
          description: 'Channel for emotional well-being check-ins',
          importance: Importance.max,
          enableVibration: true,
        ),
      );
      debugPrint('Notification channel created');
    }
  }

  Future<void> scheduleCheckIn({int minutes = 30}) async {
    final notificationPermission = await Permission.notification.request();
    debugPrint('Notification permission status: $notificationPermission');
      
    if (!notificationPermission.isGranted) {
      debugPrint('Notification permission not granted. Cannot schedule notification.');
      return;
    }

    _notificationId++;
    final notificationId = _notificationId;
      
    final now = tz.TZDateTime.now(tz.local);
    final scheduleTime = now.add(Duration(minutes: minutes));

    await flutterLocalNotificationsPlugin.zonedSchedule(
      notificationId,
      'Checking In',
      'How are you feeling now?',
      scheduleTime,
      const NotificationDetails(
        android: AndroidNotificationDetails(
          'check_in_channel',
          'Emotional Check-In',
          channelDescription: 'Channel for emotional well-being check-ins',
          importance: Importance.max,
          priority: Priority.high,
          enableVibration: true,
          playSound: true,
        ),
        iOS: DarwinNotificationDetails(
          presentAlert: true,
          presentBadge: true,
          presentSound: true,
        ),
      ),
      androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
      uiLocalNotificationDateInterpretation:
          UILocalNotificationDateInterpretation.absoluteTime,
    );
  }

}
