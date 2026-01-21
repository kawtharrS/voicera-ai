import 'package:mobile/constants/paddings.dart';
import 'package:mobile/apis/auth_service.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:mobile/constants/colors.dart';

class SignInPage extends StatefulWidget{
  @override
  _SignInPageState createState() => _SignInPageState();
}
class _SignInPageState extends State<SignInPage> {
  final _usernameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();

  @override
  void dispose(){
    _usernameController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context)
  {
    return Scaffold(
      body: Center(
        child: Padding(padding: const EdgeInsets.all(30.0),
        child: Column(
          mainAxisAlignment : MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Text('Sign In',
            style: TextStyle(
              fontFamily: 'Poppins',
              fontWeight: FontWeight.bold,
              fontSize:26,
              color: AppColors.teal,
            ),),
            const SizedBox(height:6),
            TextField(
              controller: _usernameController,
              decoration: InputDecoration(
                labelText: 'username',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height:AppPadding.vP),
            TextField(
              controller: _emailController,
              decoration: InputDecoration(
                labelText:'email',
                border:OutlineInputBorder(),
              )
            ),
            const SizedBox(height:AppPadding.vP),
            TextField(
              controller: _passwordController,
              decoration: InputDecoration(
                labelText:'Password',
                border: OutlineInputBorder(),
              ),
              obscureText : true,
            ),
            const SizedBox(height:AppPadding.vP),
            TextField(
              controller: _confirmPasswordController,
              decoration: InputDecoration(
                labelText: 'Confirm Password',
                border: OutlineInputBorder(),
              ),
              obscureText: true,
            ),
            const SizedBox(height:AppPadding.vP),
            SizedBox(
              width:double.infinity,
              height:49,
              child: ElevatedButton(
                onPressed: () async {
                  if (_emailController.text.isEmpty || _passwordController.text.isEmpty || _usernameController.text.isEmpty) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Please fill all fields')),
                    );
                    return;
                  }

                  if (_passwordController.text != _confirmPasswordController.text) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Passwords do not match')),
                    );
                    return;
                  }

                  try {
                    final response = await http.post(
                      Uri.parse('${AuthService.goBaseUrl}/api/register'),
                      headers: {'Content-Type': 'application/json'},
                      body: jsonEncode({
                        'name': _usernameController.text,
                        'email': _emailController.text,
                        'password': _passwordController.text,
                        'confirmPassword': _confirmPasswordController.text,
                      }),
                    );

                    final data = jsonDecode(response.body);
                    if (response.statusCode == 201 && data['ok'] == true) {
                      AuthService.token = data['token'];
                      if (mounted) Navigator.pushNamed(context, '/chat');
                    } else {
                      if (mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(content: Text(data['message'] ?? 'Registration failed')),
                        );
                      }
                    }
                  } catch (e) {
                    if (mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text('Error: $e')),
                      );
                    }
                  }
                },
                style : ElevatedButton.styleFrom(
                  backgroundColor: AppColors.orange,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                ),
                child: Text(
                  'Sign In',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize:16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
            const SizedBox(height: 10),
            TextButton(
              onPressed: () => Navigator.pushNamed(context, '/login'),
              child: const Text('Already have an account? Log In', style: TextStyle(color: AppColors.teal)),
            ),


          ],)),

      )
    );
  }

}