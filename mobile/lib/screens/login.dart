import 'package:mobile/constants/paddings.dart';
import 'package:mobile/apis/auth_service.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:mobile/constants/colors.dart';


class LoginPage extends StatefulWidget{
  @override
  LoginPageState createState() => LoginPageState();
}

class LoginPageState extends State<LoginPage> {
  final emailController = TextEditingController();
  final passwordController = TextEditingController();

  @override
  void dispose(){
    emailController.dispose();
    passwordController.dispose();
    super.dispose();
  }

  @override 
  Widget build(BuildContext context){
    return Scaffold(
      body:Center(
        child: Padding(padding: const EdgeInsets.all(30.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Text(
                'Welcome Back',
                style: TextStyle(
                  fontFamily: 'Poppins',
                  fontWeight: FontWeight.bold,
                  fontSize: 26,
                  color: AppColors.orange),
              ),
              const SizedBox(height:AppPadding.vP),
              TextField(
                controller: emailController,
                decoration: InputDecoration(
                labelText: 'Email',
                border: OutlineInputBorder(),),
              ),
              const SizedBox(height:6),
              TextField(
                controller: passwordController,
                decoration: InputDecoration(
                  labelText: 'Password',
                  border: OutlineInputBorder(),
                ),
                obscureText:true,
              ),
              const SizedBox(height:26),
              SizedBox(
                width:double.infinity,
                height:49,
                child: ElevatedButton(
                  onPressed: () async {
                    if (emailController.text.isEmpty || passwordController.text.isEmpty) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Please enter email and password')),
                      );
                      return;
                    }

                    try {
                      final response = await http.post(
                        Uri.parse('${AuthService.goBaseUrl}/api/login'),
                        headers: {'Content-Type': 'application/json'},
                        body: jsonEncode({
                          'email': emailController.text,
                          'password': passwordController.text,
                        }),
                      );

                      final data = jsonDecode(response.body);
                      if (response.statusCode == 200 && data['ok'] == true) {
                        AuthService.token = data['token'];
                        if (mounted) Navigator.pushNamed(context, '/chat');
                      } else {
                        if (mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(content: Text(data['message'] ?? 'Login failed')),
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
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.orange,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                child: Text(
                  'Login',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                ),
              ),
              const SizedBox(height: 10),
              TextButton(
                onPressed: () => Navigator.pushNamed(context, '/signin'),
                child: const Text('Don\'t have an account? Sign In', style: TextStyle(color: AppColors.teal)),
              ),


            ],)
      ))
        );

  }
}