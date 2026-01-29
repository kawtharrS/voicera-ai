import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:timezone/data/latest.dart' as tz;
import 'package:timezone/timezone.dart' as tz;

class NotificationService {
  static final NotificationService _instance = NotificationService._internal();
  static int _notificationId = 0;

  late final FlutterLocalNotificationsPlugin _notificationsPlugin;

  factory NotificationService() {
    return _instance;
  }

  NotificationService._internal() {
    _notificationsPlugin = FlutterLocalNotificationsPlugin();
  }

  Future<void> init() async {
    tz.initializeTimeZones();

    const androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');

    final initializationSettings = InitializationSettings(
      android: androidSettings,
      iOS: const DarwinInitializationSettings(),
    );

    await _notificationsPlugin.initialize(
      initializationSettings,
    );

    await createNotificationChannel();
  }



  Future<void> createNotificationChannel() async {
    final androidImplementation = _notificationsPlugin
        .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>();

    if (androidImplementation == null) {
      return;
    }

    await androidImplementation.createNotificationChannel(
      const AndroidNotificationChannel(
        'check_in_channel',
        'Emotional Check-In',
        description: 'Channel for emotional well-being check-ins',
        importance: Importance.max,
        enableVibration: true,
      ),
    );
  }

  Future<void> scheduleCheckIn({int minutes = 30}) async {
    if (!await requestNotificationPermission()) {
      return;
    }

    final notificationId = generateNotificationId();
    final scheduleTime = calculateScheduleTime(minutes);

    await scheduleNotification(notificationId, scheduleTime);
  }

  Future<bool> requestNotificationPermission() async {
    final permission = await Permission.notification.request();
    return permission.isGranted;
  }

  int generateNotificationId() {
    _notificationId++;
    return _notificationId;
  }

  tz.TZDateTime calculateScheduleTime(int minutes) {
    final now = tz.TZDateTime.now(tz.local);
    return now.add(Duration(minutes: minutes));
  }

  Future<void> scheduleNotification(int notificationId, tz.TZDateTime scheduleTime) async {
    await _notificationsPlugin.zonedSchedule(
      notificationId,
      'Checking In',
      'How are you feeling now? Do you want to talk?',
      scheduleTime,
      buildNotificationDetails(),
      androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
      uiLocalNotificationDateInterpretation:
          UILocalNotificationDateInterpretation.absoluteTime,
    );
  }

  NotificationDetails buildNotificationDetails() {
    return const NotificationDetails(
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
    );
  }
}