import 'package:flutter/material.dart';
import 'package:mobile/constants/colors.dart';
import 'package:mobile/constants/paddings.dart';

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
                onPressed: () {Navigator.pushNamed(context, '/login');},
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
          ],)),

      )
    );
  }

}