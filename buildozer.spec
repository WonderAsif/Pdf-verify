[app]

title = PDF Signature Stamper
package.name = pdfstamper
package.domain = org.pdfstamper
source.dir = .
source.include_exts = py,pdf,png,jpg,kv
version = 0.1

requirements = python3,kivy==2.3.0,pypdf,plyer

orientation = portrait
fullscreen = 0

android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

android.archs = arm64-v8a

# Add these lines
android.api = 33
android.minapi = 24
android.ndk = 25b

[buildozer]
log_level = 2
warn_on_root = 1
