import 'package:flutter/material.dart';
import '../services/storage_service.dart';
import '../services/api_service.dart';
import '../models/user.dart';
import 'home_screen.dart';

class SigninScreen extends StatefulWidget {
  const SigninScreen({super.key});

  @override
  State<SigninScreen> createState() => _SigninScreenState();
}

class _SigninScreenState extends State<SigninScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  
  bool _isLoading = false;
  final StorageService _storageService = StorageService();
  final ApiService _apiService = ApiService();

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);

    final email = _emailController.text.trim();
    final password = _passwordController.text;

    final user = await _storageService.getUserByEmail(email);

    if (user == null || user.password != password) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Email ou mot de passe incorrect.', style: TextStyle(color: Colors.white)), backgroundColor: Colors.red),
        );
      }
      setState(() => _isLoading = false);
      return;
    }

    // Refresh points from backend if possible
    if (user.id != null) {
      final points = await _apiService.getUserPoints(user.id!);
      if (points != null && points != user.points) {
        final updatedUser = User(
          id: user.id,
          firstName: user.firstName,
          lastName: user.lastName,
          birthDate: user.birthDate,
          occupation: user.occupation,
          sex: user.sex,
          region: user.region,
          phoneNumber: user.phoneNumber,
          email: user.email,
          password: user.password,
          points: points,
        );
        await _storageService.saveUser(updatedUser);
        await _storageService.setCurrentUser(updatedUser);
      } else {
        await _storageService.setCurrentUser(user);
      }
    } else {
      await _storageService.setCurrentUser(user);
    }

    setState(() => _isLoading = false);

    if (mounted) {
      Navigator.pushAndRemoveUntil(
        context,
        MaterialPageRoute(builder: (context) => const HomeScreen()),
        (route) => false,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Connexion', style: TextStyle(fontWeight: FontWeight.w700)),
        centerTitle: true,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 16.0),
            child: Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.04),
                    blurRadius: 24,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Heureux de vous revoir !', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Color(0xFF111827))),
                    const SizedBox(height: 8),
                    const Text(
                      'Retrouvez votre espace 3sg Media Intelligence.',
                      style: TextStyle(color: Color(0xFF6B7280)),
                    ),
                    const SizedBox(height: 32),
                    TextFormField(
                      controller: _emailController,
                      decoration: const InputDecoration(labelText: 'Email', hintText: 'votre@email.com'),
                      keyboardType: TextInputType.emailAddress,
                      validator: (value) => value!.isEmpty ? 'Requis' : null,
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _passwordController,
                      decoration: const InputDecoration(labelText: 'Mot de passe'),
                      obscureText: true,
                      validator: (value) => value!.isEmpty ? 'Requis' : null,
                    ),
                    const SizedBox(height: 32),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: _isLoading ? null : _submit,
                        child: _isLoading 
                            ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                            : const Text('Se connecter'),
                      ),
                    ),
                    const SizedBox(height: 12),
                    SizedBox(
                      width: double.infinity,
                      child: TextButton(
                        onPressed: () => Navigator.pop(context),
                        style: TextButton.styleFrom(foregroundColor: const Color(0xFF6B7280)),
                        child: const Text('Retour'),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
