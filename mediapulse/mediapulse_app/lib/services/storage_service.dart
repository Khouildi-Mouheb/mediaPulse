import 'dart:convert';
import 'dart:io';
import 'package:path_provider/path_provider.dart';
import '../models/user.dart';

class StorageService {
  static const String _fileName = 'mediapulse_db.json';
  
  Future<File> get _localFile async {
    final directory = await getApplicationDocumentsDirectory();
    return File('${directory.path}/$_fileName');
  }

  Future<Map<String, dynamic>> _readDatabase() async {
    try {
      final file = await _localFile;
      if (!await file.exists()) {
        return {'users': [], 'currentUser': null};
      }
      String contents = await file.readAsString();
      return jsonDecode(contents);
    } catch (e) {
      return {'users': [], 'currentUser': null};
    }
  }

  Future<void> _writeDatabase(Map<String, dynamic> data) async {
    final file = await _localFile;
    await file.writeAsString(jsonEncode(data));
  }

  Future<List<User>> getUsers() async {
    final db = await _readDatabase();
    final List<dynamic> userList = db['users'] ?? [];
    return userList.map((json) => User.fromJson(json)).toList();
  }

  Future<User?> getUserByEmail(String email) async {
    final users = await getUsers();
    try {
      return users.firstWhere((u) => u.email.toLowerCase() == email.toLowerCase());
    } catch (e) {
      return null;
    }
  }

  Future<void> saveUser(User user) async {
    final db = await _readDatabase();
    List<dynamic> userList = db['users'] ?? [];
    
    int index = userList.indexWhere((u) => u['email'] == user.email);
    if (index >= 0) {
      userList[index] = user.toJson();
    } else {
      final userData = user.toJson();
      if (userData['id'] == null) {
        userData['id'] = DateTime.now().millisecondsSinceEpoch;
      }
      userList.add(userData);
    }
    
    db['users'] = userList;
    await _writeDatabase(db);
  }

  Future<void> setCurrentUser(User? user) async {
    final db = await _readDatabase();
    db['currentUser'] = user?.toJson();
    await _writeDatabase(db);
  }

  Future<User?> getCurrentUser() async {
    final db = await _readDatabase();
    final userData = db['currentUser'];
    if (userData != null) {
      return User.fromJson(userData);
    }
    return null;
  }
}
