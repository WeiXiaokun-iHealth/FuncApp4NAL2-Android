#!/bin/bash

# 等待Gradle下载完成并自动构建的脚本

echo "⏳ 等待Gradle下载完成..."
echo ""

# 等待gradle wrapper文件出现
while [ ! -f "gradle/wrapper/gradle-wrapper.jar" ]; do
    sleep 2
done

echo "✅ Gradle wrapper已准备就绪！"
echo ""
echo "🔨 开始构建项目..."
echo ""

# 构建项目
./gradlew assembleDebug

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 构建成功！"
    echo ""
    echo "📱 APK位置: app/build/outputs/apk/debug/app-debug.apk"
    echo ""
    
    # 检查设备
    DEVICES=$(adb devices | grep -v "List" | grep "device$" | wc -l)
    
    if [ "$DEVICES" -gt 0 ]; then
        echo "📱 检测到Android设备"
        read -p "是否安装到设备? [Y/n]: " install
        
        if [ "$install" != "n" ] && [ "$install" != "N" ]; then
            echo "📦 安装应用..."
            ./gradlew installDebug
            
            if [ $? -eq 0 ]; then
                echo "✅ 安装成功！"
                
                read -p "是否启动应用? [Y/n]: " launch
                if [ "$launch" != "n" ] && [ "$launch" != "N" ]; then
                    echo "🚀 启动应用..."
                    adb shell am start -n com.funcapp4nal2/.MainActivity
                    echo "✅ 应用已启动"
                fi
            fi
        fi
    else
        echo "⚠️  未检测到Android设备"
        echo "请连接设备后运行: ./run-app.sh"
    fi
else
    echo ""
    echo "❌ 构建失败"
    echo "请检查错误信息"
fi
