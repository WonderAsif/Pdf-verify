import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:file_picker/file_picker.dart';
import 'package:path_provider/path_provider.dart';

void main() => runApp(const MyApp());

class MyApp extends StatelessWidget {
  const MyApp({super.key});
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Offline Python Stamper',
      theme: ThemeData(primarySwatch: Colors.blue),
      home: const PdfStamperHome(),
    );
  }
}

class PdfStamperHome extends StatefulWidget {
  const PdfStamperHome({super.key});
  @override
  State<PdfStamperHome> createState() => _PdfStamperHomeState();
}

class _PdfStamperHomeState extends State<PdfStamperHome> {
  static const platform = MethodChannel('com.example.pdfstamp/python');
  
  String _status = 'Ready to process';
  bool _isProcessing = false;
  final TextEditingController _passwordController = TextEditingController();

  @override
  void dispose() {
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _processPdfNatively() async {
    setState(() {
      _status = 'Selecting file...';
      _isProcessing = true;
    });

    try {
      FilePickerResult? result = await FilePicker.platform.pickFiles(
        type: FileType.custom, allowedExtensions: ['pdf'],
      );

      if (result == null) {
        setState(() { _status = 'Cancelled'; _isProcessing = false; });
        return;
      }

      setState(() => _status = 'Processing in offline Python...');

      File file = File(result.files.single.path!);
      Uint8List bytes = await file.readAsBytes();
      
      final Uint8List stampedBytes = await platform.invokeMethod('stampPdf', {
        'pdfBytes': bytes,
        'password': _passwordController.text,
      });

      Directory? outputDir = await getDownloadsDirectory(); 
      String fileName = file.path.split('/').last.replaceAll('.pdf', '_stamped.pdf');
      String outputPath = '${outputDir!.path}/$fileName';
      
      await File(outputPath).writeAsBytes(stampedBytes);

      setState(() {
        _status = '✓ Success!\n\nSaved to: $outputPath';
        _isProcessing = false;
      });

    } catch (e) {
      setState(() { _status = '✗ Error: $e'; _isProcessing = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Offline Python Stamper')),
      body: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(_status, textAlign: TextAlign.center),
              const SizedBox(height: 20),
              SizedBox(
                width: 300,
                child: TextField(
                  controller: _passwordController,
                  obscureText: true,
                  decoration: const InputDecoration(
                    labelText: 'PDF Password (Optional)',
                    border: OutlineInputBorder(),
                    prefixIcon: Icon(Icons.lock),
                  ),
                ),
              ),
              const SizedBox(height: 20),
              ElevatedButton(
                onPressed: _isProcessing ? null : _processPdfNatively,
                child: _isProcessing 
                  ? const CircularProgressIndicator() 
                  : const Text('Select & Stamp PDF'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
