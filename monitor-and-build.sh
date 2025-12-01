#!/bin/bash

# 监控Gradle下载并自动构建的脚本

echo "📊 监控Gradle下载进度..."
echo ""

GRADLE_ZIP="gradle.zip"
TARGET_SIZE=128000000  # 约122MB，用字节表示

# 显示当前进度
show_progress() {
    if [ -f "$GRADLE_ZIP" ]; then
        CURRENT_SIZE=$(stat -f%z "$GRADLE_ZIP" 2>/dev/null || stat -c%s "$GRADLE_ZIP" 2>/dev/null)
        CURRENT_MB=$((CURRENT_SIZE / 1024 / 1024))
        PERCENT=$((CURRENT_SIZE * 100 / TARGET_SIZE))
        
        # 创建进度条
        FILLED=$((PERCENT / 2))
        EMPTY=$((50 - FILLED))
        BAR=$(printf "%${FILLED}s" | tr ' ' '█')
        SPACE=$(printf "%${EMPTY}s" | tr ' ' '░')
        
        echo -ne "\r进度: [${BAR}${SPACE}] ${PERCENT}% (${CURRENT_MB}MB/122MB)"
    fi
}

# 检查下载进程
check_download() {
    ps aux | grep "curl.*gradle.*zip" | grep -v grep > /dev/null
    return $?
}

# 监控循环
while check_download; do
    show_progress
    sleep 2
done

echo ""
echo ""

# 检查文件是否完整下载
if [ -f "$GRADLE_ZIP" ]; then
    FILE_SIZE=$(stat -f%z "$GRADLE_ZIP" 2>/dev/null || stat -c%s "$GRADLE_ZIP" 2>/dev/null)
    FILE_MB=$((FILE_SIZE / 1024 / 1024))
    
    if [ $FILE_SIZE -gt 100000000 ]; then
        echo "✅ Gradle下载完成！(${FILE_MB}MB)"
        echo ""
        echo "📦 解压Gradle..."
        
        if unzip -q gradle.zip; then
            echo "✅ 解压成功"
            echo ""
            echo "🔧 设置Gradle wrapper..."
            
            if ./gradle-8.2/bin/gradle wrapper; then
                echo "✅ Gradle wrapper设置完成"
                echo ""
                
                # 清理
                rm -rf gradle-8.2 gradle.zip
                echo "🧹 清理临时文件完成"
                echo ""
                
                # 开始构建
                echo "🔨 开始构建项目..."
                echo ""
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
                        echo ""
                        echo "使用以下命令安装和运行："
                        echo "  ./run-app.sh"
                    else
                        echo "⚠️  未检测到Android设备"
                        echo "请连接设备后运行: ./run-app.sh"
                    fi
                else
                    echo ""
                    echo "❌ 构建失败，请检查错误信息"
                fi
            else
                echo "❌ Gradle wrapper设置失败"
            fi
        else
            echo "❌ 解压失败"
        fi
    else
        echo "⚠️  下载可能未完成 (${FILE_MB}MB)"
        echo "请重新运行下载命令"
    fi
else
    echo "❌ 未找到gradle.zip文件"
fi
