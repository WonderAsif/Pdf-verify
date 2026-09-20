[app]

# Title of your application
title = PDF Verify by WonderAsif

# Package name
package.name = pdfstamper

# Package domain (needed for android/ios packaging)
package.domain = org.pdfstamper

# Source code directory
source.dir = .

# Source files to include
source.include_exts = py,pdf,png,jpg,kv

# Application version
version = 0.1

# Requirements (libraries)
requirements = python3,kivy,pypdf,plyer

# Orientation
orientation = portrait

# Fullscreen mode
fullscreen = 0

# Android specific settings
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,READ_MEDIA_DOCUMENTS

# Android API settings
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33

# Architecture
android.archs = arm64-v8a, armeabi-v7a

# Buildozer settings
[buildozer]
log_level = 2
warn_on_root = 1
