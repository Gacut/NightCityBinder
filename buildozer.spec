[app]
title = >NightCityBinder_
package.name = nightcitybinder
package.domain = com
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,xml,webp,txt
source.exclude_dirs = tests,docs,scripts,.local,.git,.venv,android,__pycache__,dist,bin,.buildozer,.pytest_cache,.ruff_cache
version = 1.0.18
requirements = python3,kivy==2.3.1,pyjnius,openssl,certifi,charset-normalizer==3.4.2
orientation = portrait
presplash.filename = %(source.dir)s/assets/presplash.png
android.presplash_color = #09070c
icon.filename = %(source.dir)s/assets/icon.png
icon.adaptive_foreground.filename = %(source.dir)s/assets/icon_foreground.png
icon.adaptive_background.filename = %(source.dir)s/assets/icon_background.png
fullscreen = 0
android.permissions = INTERNET,CAMERA
android.api = 35
android.minapi = 24
android.archs = arm64-v8a
android.enable_androidx = True
android.add_src = android/src
android.add_activities = org.nightcitybinder.ScannerActivity
# Kotlin 1.8 merged JDK7/JDK8 classes into stdlib. Align the compatibility
# modules too, so transitive 1.6.21 jars cannot introduce duplicate classes.
android.gradle_dependencies = androidx.activity:activity:1.9.3,androidx.camera:camera-camera2:1.3.4,androidx.camera:camera-lifecycle:1.3.4,androidx.camera:camera-view:1.3.4,com.google.mlkit:text-recognition:16.0.1,org.jetbrains.kotlin:kotlin-stdlib:1.8.22,org.jetbrains.kotlin:kotlin-stdlib-jdk7:1.8.22,org.jetbrains.kotlin:kotlin-stdlib-jdk8:1.8.22
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1

# Release candidate only: must pass docs/play/README.md before submission.
[app@play]
version = 1.0.18
android.numeric_version = 10018
android.api = 36
android.release_artifact = aab
android.allow_backup = False
android.gradle_dependencies = androidx.activity:activity:1.9.3,androidx.camera:camera-camera2:1.4.2,androidx.camera:camera-lifecycle:1.4.2,androidx.camera:camera-view:1.4.2,com.google.mlkit:text-recognition:16.0.1,org.jetbrains.kotlin:kotlin-stdlib:1.8.22,org.jetbrains.kotlin:kotlin-stdlib-jdk7:1.8.22,org.jetbrains.kotlin:kotlin-stdlib-jdk8:1.8.22
