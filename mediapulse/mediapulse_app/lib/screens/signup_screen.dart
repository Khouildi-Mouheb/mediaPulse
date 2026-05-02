import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/user.dart';
import '../services/storage_service.dart';
import '../services/api_service.dart';
import 'home_screen.dart';

class SignupScreen extends StatefulWidget {
  const SignupScreen({super.key});

  @override
  State<SignupScreen> createState() => _SignupScreenState();
}

class _SignupScreenState extends State<SignupScreen> {
  final _formKey1 = GlobalKey<FormState>();
  final _formKey2 = GlobalKey<FormState>();
  
  int _step = 1;
  bool _isLoading = false;

  // Step 1 controllers
  final _firstNameController = TextEditingController();
  final _lastNameController = TextEditingController();
  final _birthDateController = TextEditingController();
  String _sex = 'male';

  // Step 2 controllers
  final _occupationController = TextEditingController();
  String _region = 'Tunis';
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  final ApiService _apiService = ApiService();
  final StorageService _storageService = StorageService();

  final List<String> _regions = [
    'Tunis', 'Ariana', 'Ben Arous', 'Manouba', 'Nabeul', 'Zaghouan', 
    'Bizerte', 'Béja', 'Jendouba', 'Kef', 'Siliana', 'Sousse', 
    'Monastir', 'Mahdia', 'Sfax', 'Kairouan', 'Kasserine', 
    'Sidi Bouzid', 'Gabès', 'Medenine', 'Tataouine', 'Gafsa', 
    'Tozeur', 'Kebili'
  ];

  Future<void> _selectDate(BuildContext context) async {
    final DateTime? picked = await showDatePicker(
      context: context,
      initialDate: DateTime(2000, 1, 1),
      firstDate: DateTime(1920),
      lastDate: DateTime.now(),
      builder: (context, child) {
        return Theme(
          data: Theme.of(context).copyWith(
            colorScheme: const ColorScheme.light(
              primary: Color(0xFF6B4EFF),
              onPrimary: Colors.white,
              onSurface: Color(0xFF111827),
            ),
          ),
          child: child!,
        );
      },
    );
    if (picked != null) {
      setState(() {
        _birthDateController.text = DateFormat('yyyy-MM-dd').format(picked);
      });
    }
  }

  Future<void> _submit() async {
    if (!_formKey2.currentState!.validate()) return;

    setState(() => _isLoading = true);

    final email = _emailController.text.trim();
    final existingUser = await _storageService.getUserByEmail(email);
    
    if (existingUser != null) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Un compte avec cet email existe déjà.', style: TextStyle(color: Colors.white)), backgroundColor: Colors.red),
        );
      }
      setState(() => _isLoading = false);
      return;
    }

    User newUser = User(
      firstName: _firstNameController.text.trim(),
      lastName: _lastNameController.text.trim(),
      birthDate: _birthDateController.text.trim(),
      sex: _sex,
      occupation: _occupationController.text.trim(),
      region: _region,
      email: email,
      password: _passwordController.text,
    );

    // Try to register via API
    final apiUser = await _apiService.signup(newUser);
    
    if (apiUser != null) {
      newUser = apiUser;
    }

    // Save to local JSON database
    await _storageService.saveUser(newUser);
    await _storageService.setCurrentUser(newUser);

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
        title: const Text('Inscription', style: TextStyle(fontWeight: FontWeight.w700)),
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
              child: _step == 1 ? _buildStep1() : _buildStep2(),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildStep1() {
    return Form(
      key: _formKey1,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(child: Container(height: 6, decoration: BoxDecoration(color: Theme.of(context).primaryColor, borderRadius: BorderRadius.circular(3)))),
              const SizedBox(width: 8),
              Expanded(child: Container(height: 6, decoration: BoxDecoration(color: const Color(0xFFF3F4F6), borderRadius: BorderRadius.circular(3)))),
            ],
          ),
          const SizedBox(height: 32),
          const Text('Informations personnelles', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Color(0xFF111827))),
          const SizedBox(height: 8),
          const Text('Parlez-nous un peu de vous.', style: TextStyle(color: Color(0xFF6B7280))),
          const SizedBox(height: 24),
          Row(
            children: [
              Expanded(
                child: TextFormField(
                  controller: _firstNameController,
                  decoration: const InputDecoration(labelText: 'Prénom'),
                  validator: (value) => value!.isEmpty ? 'Requis' : null,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: TextFormField(
                  controller: _lastNameController,
                  decoration: const InputDecoration(labelText: 'Nom'),
                  validator: (value) => value!.isEmpty ? 'Requis' : null,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          TextFormField(
            controller: _birthDateController,
            readOnly: true,
            onTap: () => _selectDate(context),
            decoration: const InputDecoration(
              labelText: 'Date de naissance',
              hintText: 'Sélectionner une date',
              suffixIcon: Icon(Icons.calendar_today, color: Color(0xFF6B7280)),
            ),
            validator: (value) => value!.isEmpty ? 'Requis' : null,
          ),
          const SizedBox(height: 16),
          DropdownButtonFormField<String>(
            value: _sex,
            decoration: const InputDecoration(labelText: 'Sexe'),
            items: const [
              DropdownMenuItem(value: 'male', child: Text('Homme')),
              DropdownMenuItem(value: 'female', child: Text('Femme')),
            ],
            onChanged: (value) => setState(() => _sex = value!),
            icon: const Icon(Icons.keyboard_arrow_down, color: Color(0xFF6B7280)),
          ),
          const SizedBox(height: 32),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: () {
                if (_formKey1.currentState!.validate()) {
                  setState(() => _step = 2);
                }
              },
              child: const Text('Continuer'),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStep2() {
    return Form(
      key: _formKey2,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(child: Container(height: 6, decoration: BoxDecoration(color: Theme.of(context).primaryColor, borderRadius: BorderRadius.circular(3)))),
              const SizedBox(width: 8),
              Expanded(child: Container(height: 6, decoration: BoxDecoration(color: Theme.of(context).primaryColor, borderRadius: BorderRadius.circular(3)))),
            ],
          ),
          const SizedBox(height: 32),
          const Text('Profil et Compte', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Color(0xFF111827))),
          const SizedBox(height: 8),
          const Text('Finalisons votre inscription.', style: TextStyle(color: Color(0xFF6B7280))),
          const SizedBox(height: 24),
          DropdownButtonFormField<String>(
            value: _region,
            decoration: const InputDecoration(labelText: 'Région (Tunisie)'),
            items: _regions.map((region) => DropdownMenuItem(value: region, child: Text(region))).toList(),
            onChanged: (value) => setState(() => _region = value!),
            icon: const Icon(Icons.keyboard_arrow_down, color: Color(0xFF6B7280)),
          ),
          const SizedBox(height: 16),
          TextFormField(
            controller: _occupationController,
            decoration: const InputDecoration(labelText: 'Profession', hintText: 'Ex: Ingénieur, Étudiant...'),
            validator: (value) => value!.isEmpty ? 'Requis' : null,
          ),
          const SizedBox(height: 16),
          TextFormField(
            controller: _emailController,
            decoration: const InputDecoration(labelText: 'Email', hintText: 'votre@email.com'),
            keyboardType: TextInputType.emailAddress,
            validator: (value) => value!.isEmpty || !value.contains('@') ? 'Email invalide' : null,
          ),
          const SizedBox(height: 16),
          TextFormField(
            controller: _passwordController,
            decoration: const InputDecoration(labelText: 'Mot de passe'),
            obscureText: true,
            validator: (value) => value!.length < 4 ? 'Min. 4 caractères' : null,
          ),
          const SizedBox(height: 32),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _isLoading ? null : _submit,
              child: _isLoading 
                  ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  : const Text('Créer mon compte'),
            ),
          ),
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            child: TextButton(
              onPressed: () => setState(() => _step = 1),
              style: TextButton.styleFrom(foregroundColor: const Color(0xFF6B7280)),
              child: const Text('Retour'),
            ),
          ),
        ],
      ),
    );
  }
}
