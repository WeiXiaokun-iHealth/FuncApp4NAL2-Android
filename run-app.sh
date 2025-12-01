#!/bin/bash

# FuncApp4NAL2 Android应用运行脚本
# 此脚本用于快速构建和运行Android应用

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"

echo -e "${BLUE}🚀 FuncApp4NAL2 Android应用运行脚本${NC}"
echo "================================================"
echo ""

# 检查是否在项目根目录
if [ ! -f "$PROJECT_ROOT/settings.gradle.kts" ]; then
    echo -e "${RED}❌ 错误: 请在项目根目录运行此脚本${NC}"
    exit 1
fi

# 检查Android设备连接
echo -e "${BLUE}📱 检查Android设备连接...${NC}"
DEVICES=$(adb devices | grep -v "List" | grep "device$" | wc -l)

if [ "$DEVICES" -eq 0 ]; then
    echo -e "${RED}❌ 未检测到Android设备或模拟器${NC}"
    echo ""
    echo "请确保："
    echo "  1. 已连接Android设备并启用USB调试"
    echo "  2. 或已启动Android模拟器"
    echo ""
    echo "检查设备连接："
    adb devices
    exit 1
elif [ "$DEVICES" -eq 1 ]; then
    DEVICE_NAME=$(adb devices | grep "device$" | awk '{print $1}')
    echo -e "${GREEN}✅ 检测到设备: $DEVICE_NAME${NC}"
else
    echo -e "${YELLOW}⚠️  检测到多个设备:${NC}"
    adb devices
    echo ""
    echo -e "${YELLOW}将使用第一个设备进行安装${NC}"
fi

echo ""

# 显示菜单
echo -e "${BLUE}请选择操作:${NC}"
echo "  1) 构建并安装Debug版本 (推荐)"
echo "  2) 构建并安装Release版本"
echo "  3) 仅构建Debug APK"
echo "  4) 仅构建Release APK"
echo "  5) 清理项目"
echo "  6) 清理并重新构建"
echo "  7) 启动应用"
echo "  8) 查看日志"
echo "  9) 卸载应用"
echo "  0) 退出"
echo ""

read -p "请输入选项 [1-9/0]: " choice

case $choice in
    1)
        echo ""
        echo -e "${BLUE}🔨 构建Debug版本...${NC}"
        ./gradlew assembleDebug
        
        echo ""
        echo -e "${BLUE}📦 安装应用到设备...${NC}"
        ./gradlew installDebug
        
        echo ""
        echo -e "${GREEN}✅ 应用安装成功！${NC}"
        echo ""
        
        read -p "是否立即启动应用? [Y/n]: " launch
        if [ "$launch" != "n" ] && [ "$launch" != "N" ]; then
            echo -e "${BLUE}🚀 启动应用...${NC}"
            adb shell am start -n com.funcapp4nal2/.MainActivity
            echo ""
            echo -e "${GREEN}✅ 应用已启动${NC}"
            echo ""
            
            read -p "是否查看实时日志? [Y/n]: " viewlog
            if [ "$viewlog" != "n" ] && [ "$viewlog" != "N" ]; then
                echo -e "${BLUE}📋 显示应用日志 (Ctrl+C 退出)...${NC}"
                echo ""
                adb logcat -s "FuncApp4NAL2:*" "Nal2Manager:*" "HttpServer:*" "AndroidRuntime:E"
            fi
        fi
        ;;
        
    2)
        echo ""
        echo -e "${BLUE}🔨 构建Release版本...${NC}"
        ./gradlew assembleRelease
        
        echo ""
        echo -e "${BLUE}📦 安装应用到设备...${NC}"
        adb install -r app/build/outputs/apk/release/app-release.apk
        
        echo ""
        echo -e "${GREEN}✅ 应用安装成功！${NC}"
        echo ""
        echo -e "${YELLOW}APK位置: app/build/outputs/apk/release/app-release.apk${NC}"
        ;;
        
    3)
        echo ""
        echo -e "${BLUE}🔨 构建Debug APK...${NC}"
        ./gradlew assembleDebug
        
        echo ""
        echo -e "${GREEN}✅ 构建完成！${NC}"
        echo -e "${YELLOW}APK位置: app/build/outputs/apk/debug/app-debug.apk${NC}"
        ;;
        
    4)
        echo ""
        echo -e "${BLUE}🔨 构建Release APK...${NC}"
        ./gradlew assembleRelease
        
        echo ""
        echo -e "${GREEN}✅ 构建完成！${NC}"
        echo -e "${YELLOW}APK位置: app/build/outputs/apk/release/app-release.apk${NC}"
        ;;
        
    5)
        echo ""
        echo -e "${BLUE}🧹 清理项目...${NC}"
        ./gradlew clean
        
        echo ""
        echo -e "${GREEN}✅ 清理完成！${NC}"
        ;;
        
    6)
        echo ""
        echo -e "${BLUE}🧹 清理项目...${NC}"
        ./gradlew clean
        
        echo ""
        echo -e "${BLUE}🔨 重新构建Debug版本...${NC}"
        ./gradlew assembleDebug
        
        echo ""
        echo -e "${BLUE}📦 安装应用到设备...${NC}"
        ./gradlew installDebug
        
        echo ""
        echo -e "${GREEN}✅ 清理并重新构建完成！${NC}"
        ;;
        
    7)
        echo ""
        echo -e "${BLUE}🚀 启动应用...${NC}"
        adb shell am start -n com.funcapp4nal2/.MainActivity
        
        echo ""
        echo -e "${GREEN}✅ 应用已启动${NC}"
        echo ""
        
        read -p "是否查看实时日志? [Y/n]: " viewlog
        if [ "$viewlog" != "n" ] && [ "$viewlog" != "N" ]; then
            echo -e "${BLUE}📋 显示应用日志 (Ctrl+C 退出)...${NC}"
            echo ""
            adb logcat -s "FuncApp4NAL2:*" "Nal2Manager:*" "HttpServer:*" "AndroidRuntime:E"
        fi
        ;;
        
    8)
        echo ""
        echo -e "${BLUE}📋 显示应用日志 (Ctrl+C 退出)...${NC}"
        echo ""
        adb logcat -s "FuncApp4NAL2:*" "Nal2Manager:*" "HttpServer:*" "AndroidRuntime:E"
        ;;
        
    9)
        echo ""
        echo -e "${BLUE}🗑️  卸载应用...${NC}"
        adb uninstall com.funcapp4nal2
        
        echo ""
        echo -e "${GREEN}✅ 应用已卸载${NC}"
        ;;
        
    0)
        echo ""
        echo -e "${BLUE}👋 退出${NC}"
        exit 0
        ;;
        
    *)
        echo ""
        echo -e "${RED}❌ 无效选项${NC}"
        exit 1
        ;;
esac

echo ""
echo "================================================"
echo -e "${GREEN}🎉 操作完成！${NC}"
echo ""
