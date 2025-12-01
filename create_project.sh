#!/bin/bash

# FuncApp4NAL2 Android项目创建脚本
# 此脚本将创建完整的Android原生项目结构

set -e

echo "🚀 开始创建FuncApp4NAL2 Android原生项目..."

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
RN_PROJECT_ROOT="$(cd "$PROJECT_ROOT/../FuncApp4NAL2" && pwd)"

# 创建目录结构
echo "📁 创建目录结构..."
mkdir -p "$PROJECT_ROOT/app/src/main/java/com/funcapp4nal2"
mkdir -p "$PROJECT_ROOT/app/src/main/java/com/funcapp4nal2/nal2"
mkdir -p "$PROJECT_ROOT/app/src/main/java/com/funcapp4nal2/server"
mkdir -p "$PROJECT_ROOT/app/src/main/java/com/funcapp4nal2/utils"
mkdir -p "$PROJECT_ROOT/app/src/main/java/com/funcapp4nal2/ui"
mkdir -p "$PROJECT_ROOT/app/src/main/java/com/funcapp4nal2/viewmodel"
mkdir -p "$PROJECT_ROOT/app/src/main/res/layout"
mkdir -p "$PROJECT_ROOT/app/src/main/res/values"
mkdir -p "$PROJECT_ROOT/app/src/main/res/drawable"
mkdir -p "$PROJECT_ROOT/app/src/main/res/xml"
mkdir -p "$PROJECT_ROOT/app/src/main/res/mipmap-hdpi"
mkdir -p "$PROJECT_ROOT/app/src/main/res/mipmap-mdpi"
mkdir -p "$PROJECT_ROOT/app/src/main/res/mipmap-xhdpi"
mkdir -p "$PROJECT_ROOT/app/src/main/res/mipmap-xxhdpi"
mkdir -p "$PROJECT_ROOT/app/src/main/res/mipmap-xxxhdpi"
mkdir -p "$PROJECT_ROOT/app/libs"
mkdir -p "$PROJECT_ROOT/gradle/wrapper"

# 复制NAL2库
echo "📦 复制NAL2库..."
if [ -f "$RN_PROJECT_ROOT/modules/nal2/android/libs/nl2-release.aar" ]; then
    cp "$RN_PROJECT_ROOT/modules/nal2/android/libs/nl2-release.aar" "$PROJECT_ROOT/app/libs/"
    echo "✅ NAL2库复制成功"
else
    echo "⚠️  警告: 未找到NAL2库文件，请手动复制"
fi

# 复制Nal2Manager.java
echo "📄 复制Nal2Manager.java..."
if [ -f "$RN_PROJECT_ROOT/modules/nal2/android/src/main/java/com/nal2/Nal2Manager.java" ]; then
    mkdir -p "$PROJECT_ROOT/app/src/main/java/com/nal2"
    cp "$RN_PROJECT_ROOT/modules/nal2/android/src/main/java/com/nal2/Nal2Manager.java" \
       "$PROJECT_ROOT/app/src/main/java/com/nal2/"
    echo "✅ Nal2Manager.java复制成功"
else
    echo "⚠️  警告: 未找到Nal2Manager.java"
fi

# 创建gradle wrapper
echo "⚙️  创建Gradle Wrapper..."
cat > "$PROJECT_ROOT/gradle/wrapper/gradle-wrapper.properties" << 'EOF'
distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\://services.gradle.org/distributions/gradle-8.2-bin.zip
networkTimeout=10000
validateDistributionUrl=true
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
EOF

# 创建gradlew脚本
echo "📝 创建gradlew脚本..."
cat > "$PROJECT_ROOT/gradlew" << 'EOF'
#!/bin/sh
exec "$(dirname "$0")/gradle/wrapper/gradle-wrapper.jar" "$@"
EOF
chmod +x "$PROJECT_ROOT/gradlew"

# 创建proguard规则
echo "🔒 创建ProGuard规则..."
cat > "$PROJECT_ROOT/app/proguard-rules.pro" << 'EOF'
# Add project specific ProGuard rules here.
-keep class com.nal2.** { *; }
-keep class com.funcapp4nal2.** { *; }
-keepclassmembers class * {
    native <methods>;
}
EOF

# 创建资源文件
echo "🎨 创建资源文件..."

# strings.xml
cat > "$PROJECT_ROOT/app/src/main/res/values/strings.xml" << 'EOF'
<resources>
    <string name="app_name">FuncApp4NAL2</string>
    <string name="server_running">服务器运行中</string>
    <string name="server_stopped">服务器已停止</string>
    <string name="ip_address">IP地址</string>
    <string name="port">端口</string>
    <string name="refresh">刷新</string>
    <string name="api_endpoint">API端点</string>
    <string name="copy_api_url">复制API地址</string>
    <string name="logs">日志</string>
    <string name="download_logs">下载日志</string>
    <string name="clear_logs">清除日志</string>
    <string name="global_variables">全局变量</string>
    <string name="version_info">版本信息</string>
</resources>
EOF

# colors.xml
cat > "$PROJECT_ROOT/app/src/main/res/values/colors.xml" << 'EOF'
<resources>
    <color name="purple_200">#FFBB86FC</color>
    <color name="purple_500">#FF6200EE</color>
    <color name="purple_700">#FF3700B3</color>
    <color name="teal_200">#FF03DAC5</color>
    <color name="teal_700">#FF018786</color>
    <color name="black">#FF000000</color>
    <color name="white">#FFFFFFFF</color>
    <color name="primary">#FF007AFF</color>
    <color name="success">#FF34C759</color>
    <color name="error">#FFFF3B30</color>
    <color name="background">#FFF5F5F5</color>
</resources>
EOF

# themes.xml
cat > "$PROJECT_ROOT/app/src/main/res/values/themes.xml" << 'EOF'
<resources>
    <style name="Theme.FuncApp4NAL2" parent="Theme.MaterialComponents.DayNight.DarkActionBar">
        <item name="colorPrimary">@color/primary</item>
        <item name="colorPrimaryVariant">@color/purple_700</item>
        <item name="colorOnPrimary">@color/white</item>
        <item name="colorSecondary">@color/teal_200</item>
        <item name="colorSecondaryVariant">@color/teal_700</item>
        <item name="colorOnSecondary">@color/black</item>
        <item name="android:statusBarColor">@color/primary</item>
    </style>
</resources>
EOF

# backup_rules.xml
cat > "$PROJECT_ROOT/app/src/main/res/xml/backup_rules.xml" << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<full-backup-content>
    <exclude domain="sharedpref" path="." />
</full-backup-content>
EOF

# data_extraction_rules.xml
cat > "$PROJECT_ROOT/app/src/main/res/xml/data_extraction_rules.xml" << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<data-extraction-rules>
    <cloud-backup>
        <exclude domain="sharedpref" path="." />
    </cloud-backup>
</data-extraction-rules>
EOF

# 创建.gitignore
echo "📝 创建.gitignore..."
cat > "$PROJECT_ROOT/.gitignore" << 'EOF'
*.iml
.gradle
/local.properties
/.idea/
.DS_Store
/build
/captures
.externalNativeBuild
.cxx
local.properties
*.apk
*.ap_
*.aab
EOF

cat > "$PROJECT_ROOT/app/.gitignore" << 'EOF'
/build
EOF

echo ""
echo "✅ 项目结构创建完成！"
echo ""
echo "📋 下一步操作："
echo "1. 使用Android Studio打开项目: $PROJECT_ROOT"
echo "2. 等待Gradle同步完成"
echo "3. 连接Android设备或启动模拟器"
echo "4. 点击运行按钮"
echo ""
echo "📚 更多信息请查看: $PROJECT_ROOT/README.md"
echo ""
echo "🎉 完成！"
