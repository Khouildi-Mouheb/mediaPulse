class User {
  final int? id;
  final String firstName;
  final String lastName;
  final String birthDate;
  final String occupation;
  final String sex;
  final String region;
  final String? phoneNumber;
  final String email;
  final String? password;
  final int points;

  User({
    this.id,
    required this.firstName,
    required this.lastName,
    required this.birthDate,
    required this.occupation,
    required this.sex,
    required this.region,
    this.phoneNumber,
    required this.email,
    this.password,
    this.points = 0,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'],
      firstName: json['first_name'] ?? '',
      lastName: json['last_name'] ?? '',
      birthDate: json['birth_date'] ?? '',
      occupation: json['occupation'] ?? '',
      sex: json['sex'] ?? 'male',
      region: json['region'] ?? 'Tunis',
      phoneNumber: json['phone_number'],
      email: json['email'] ?? '',
      password: json['password'],
      points: json['points'] ?? 0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'first_name': firstName,
      'last_name': lastName,
      'birth_date': birthDate,
      'occupation': occupation,
      'sex': sex,
      'region': region,
      'phone_number': phoneNumber,
      'email': email,
      'password': password,
      'points': points,
    };
  }
}
