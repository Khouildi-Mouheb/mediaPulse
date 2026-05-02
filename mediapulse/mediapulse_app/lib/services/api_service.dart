import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/user.dart';

class ApiService {
  // Use 10.0.2.2 for Android Emulator. (If you use Linux Desktop, change this to 127.0.0.1)
  static const String baseUrl = 'http://10.0.2.2:8001';

  Future<User?> signup(User user) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/users/signup'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'first_name': user.firstName,
          'last_name': user.lastName,
          'birth_date': user.birthDate,
          'occupation': user.occupation,
          'sex': user.sex,
          'region': user.region,
          'phone_number': user.phoneNumber ?? '',
          'email': user.email,
          'consent_microphone': true,
          'consent_location': true,
          'consent_rewards': true,
          'consent_demographic_analytics': true
        }),
      ).timeout(const Duration(seconds: 3)); // Add 3-second timeout

      if (response.statusCode == 200 || response.statusCode == 201) {
        final data = jsonDecode(response.body);
        return User(
          id: data['id'],
          firstName: data['first_name'],
          lastName: data['last_name'],
          birthDate: data['birth_date'],
          occupation: data['occupation'],
          sex: data['sex'],
          region: data['region'],
          phoneNumber: data['phone_number'],
          email: data['email'],
          password: user.password,
          points: data['points'] ?? 0,
        );
      }
      return null;
    } catch (e) {
      print('API Error: $e');
      return null;
    }
  }
  
  Future<int?> getUserPoints(int userId) async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/users/$userId/points'))
          .timeout(const Duration(seconds: 3));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return data['points'];
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  Future<Map<String, dynamic>?> detectMedia(String filePath, int userId) async {
    try {
      final request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/detect-media'),
      );

      request.fields['user_id'] = userId.toString();
      request.fields['timestamp'] = DateTime.now().toUtc().toIso8601String();
      request.files.add(await http.MultipartFile.fromPath('audio', filePath));

      final response = await request.send().timeout(const Duration(seconds: 60));
      if (response.statusCode == 200) {
        final respStr = await response.stream.bytesToString();
        return jsonDecode(respStr);
      }
      return null;
    } catch (e) {
      print('Detect Media Error: $e');
      return null;
    }
  }

  Future<Map<String, dynamic>?> detectHashes(List<List<dynamic>> hashes, int userId) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/detect-hashes'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'user_id': userId,
          'timestamp': DateTime.now().toUtc().toIso8601String(),
          'hashes': hashes,
        }),
      ).timeout(const Duration(seconds: 15));

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
      return null;
    } catch (e) {
      print('Detect Hashes Error: $e');
      return null;
    }
  }
}
