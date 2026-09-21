import 'dart:io';
import 'dart:ui'; // Required for ImageFilter (Glassmorphism)
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:file_picker/file_picker.dart';
import 'package:permission_handler/permission_handler.dart';

void main() => runApp(const MyApp());

class MyApp extends StatelessWidget {
  const MyApp({super.key});
  
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'WonderPDF Stamper',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        // Transparent AppBar theme to match the glass design
        appBarTheme: const AppBarTheme(
          backgroundColor: Colors.transparent,
          elevation: 0,
          centerTitle: true,
          titleTextStyle: TextStyle(
            color: Colors.white, 
            fontSize: 22, 
            fontWeight: FontWeight.bold
          ),
        ),
      ),
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
  // Updated package name in the method channel
  static const platform = MethodChannel('com.example.wonderpdf/python');

  String _status = 'Ready to process';
  bool _isProcessing = false;
  final TextEditingController _passwordController = TextEditingController();

  @override
  void dispose() {
    _passwordController.dispose();
    super.dispose();
  }

  Future<bool> _requestPermissions() async {
    if (Platform.isAndroid) {
      if (await Permission.manageExternalStorage.isGranted) return true;
      var status = await Permission.manageExternalStorage.request();
      if (status.isGranted) return true;
      var legacyStatus = await Permission.storage.request();
      return legacyStatus.isGranted;
    }
    return true;
  }

  Future<void> _processPdfNatively() async {
    setState(() {
      _status = 'Requesting storage permissions...';
      _isProcessing = true;
    });

    bool hasPermission = await _requestPermissions();
    if (!hasPermission) {
      setState(() {
        _status = '✗ Error: Storage permission required to save anywhere.';
        _isProcessing = false;
      });
      return;
    }

    setState(() => _status = 'Selecting PDF file...');

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
      String fileName = file.path.split('/').last.replaceAll('.pdf', '_stamped.pdf');
      Uint8List bytes = await file.readAsBytes();

      final Uint8List stampedBytes = await platform.invokeMethod('stampPdf', {
        'pdfBytes': bytes,
        'password': _passwordController.text,
      });

      setState(() => _status = 'Select where to save the output...');

      String? selectedDirectory = await FilePicker.platform.getDirectoryPath(
        dialogTitle: 'Select folder to save stamped PDF',
      );

      if (selectedDirectory == null) {
        setState(() { _status = 'Save cancelled by user'; _isProcessing = false; });
        return;
      }

      String outputPath = '$selectedDirectory/$fileName';
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
      extendBodyBehindAppBar: true, // Allows the background gradient to flow behind the AppBar
      appBar: AppBar(title: const Text('WonderPDF Stamper')),
      body: Stack(
        children: [
          // 1. Colorful Background
          Container(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: [Color(0xFF8A2387), Color(0xFFE94057), Color(0xFFF27121)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
            ),
          ),
          
          // 2. Glassmorphism UI
          Center(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24.0),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(24),
                child: BackdropFilter(
                  filter: ImageFilter.blur(sigmaX: 15, sigmaY: 15),
                  child: Container(
                    width: double.infinity,
                    constraints: const BoxConstraints(maxWidth: 400),
                    padding: const EdgeInsets.all(32),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.15),
                      borderRadius: BorderRadius.circular(24),
                      border: Border.all(
                        color: Colors.white.withOpacity(0.3),
                        width: 1.5,
                      ),
                    ),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(
                          _status, 
                          textAlign: TextAlign.center,
                          style: const TextStyle(color: Colors.white, fontSize: 16),
                        ),
                        const SizedBox(height: 24),
                        
                        TextField(
                          controller: _passwordController,
                          obscureText: true,
                          style: const TextStyle(color: Colors.white),
                          decoration: InputDecoration(
                            labelText: 'PDF Password (Optional)',
                            labelStyle: TextStyle(color: Colors.white.withOpacity(0.8)),
                            prefixIcon: const Icon(Icons.lock, color: Colors.white),
                            enabledBorder: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(12),
                              borderSide: BorderSide(color: Colors.white.withOpacity(0.4)),
                            ),
                            focusedBorder: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(12),
                              borderSide: const BorderSide(color: Colors.white),
                            ),
                          ),
                        ),
                        const SizedBox(height: 24),
                        
                        ElevatedButton(
                          onPressed: _isProcessing ? null : _processPdfNatively,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.white.withOpacity(0.2),
                            foregroundColor: Colors.white,
                            disabledBackgroundColor: Colors.white.withOpacity(0.1),
                            disabledForegroundColor: Colors.white.withOpacity(0.5),
                            elevation: 0,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                              side: BorderSide(color: Colors.white.withOpacity(0.3)),
                            ),
                            padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                          ),
                          child: _isProcessing
                              ? const SizedBox(
                                  height: 20,
                                  width: 20,
                                  child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                                )
                              : const Text('Select & Stamp PDF', style: TextStyle(fontSize: 16)),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
