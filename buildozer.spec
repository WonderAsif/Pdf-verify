[app]

title = PDF Signature Stamper
package.name = pdfstamper
package.domain = org.pdfstamper
source.dir = .
source.include_exts = py,pdf,png,jpg,kv
version = 0.1

requirements = python3,kivy,pypdf,plyer

orientation = portrait
fullscreen = 0

android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
