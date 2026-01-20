import 'package:flutter/material.dart';

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
                  color: Color(0xFF4DB6AC)),
              ),
              const SizedBox(height:16),
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
                  onPressed: () {Navigator.pushNamed(context, '/chat');},
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Color(0xFFFF9500),
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
            ],)
      ))
        );

  }
}