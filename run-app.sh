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

# WiFi设备IP配置文件
WIFI_CONFIG_FILE="$PROJECT_ROOT/.adb_wifi_device"

echo -e "${BLUE}🚀 FuncApp4NAL2 Android应用运行脚本${NC}"
echo "================================================"
echo ""

# 检查是否在项目根目录
if [ ! -f "$PROJECT_ROOT/settings.gradle.kts" ]; then
    echo -e "${RED}❌ 错误: 请在项目根目录运行此脚本${NC}"
    exit 1
fi

# 先检查USB设备连接
echo -e "${BLUE}📱 检查Android设备连接...${NC}"
USB_DEVICES=$(adb devices | grep -v "List" | grep -v ":" | grep "device$" | wc -l)

# 如果没有USB设备，尝试WiFi连接
if [ "$USB_DEVICES" -eq 0 ]; then
    # 检查是否有保存的WiFi设备IP
    SAVED_IP=""
    if [ -f "$WIFI_CONFIG_FILE" ]; then
        SAVED_IP=$(cat "$WIFI_CONFIG_FILE" 2>/dev/null | tr -d '\n\r')
    fi
    
    # 如果有保存的IP，尝试WiFi连接
    if [ -n "$SAVED_IP" ]; then
        echo -e "${BLUE}🔌 未检测到USB设备，尝试WiFi连接到 $SAVED_IP:5555...${NC}"
        adb connect "$SAVED_IP:5555" > /dev/null 2>&1
        sleep 2
    fi
else
    echo -e "${GREEN}✅ 检测到USB设备，优先使用USB连接${NC}"
fi

# 再次检查所有设备连接
DEVICES=$(adb devices | grep -v "List" | grep "device$" | wc -l)

if [ "$DEVICES" -eq 0 ]; then
    echo -e "${YELLOW}⚠️  未检测到Android设备或模拟器${NC}"
    echo ""
    
    # 尝试通过WiFi连接
    read -p "是否尝试通过WiFi连接设备? [Y/n]: " try_wifi
    if [ "$try_wifi" != "n" ] && [ "$try_wifi" != "N" ]; then
        # 如果有保存的IP，显示为默认值
        if [ -n "$SAVED_IP" ]; then
            read -p "请输入设备IP地址 [默认: $SAVED_IP]: " device_ip
            device_ip=${device_ip:-$SAVED_IP}
        else
            read -p "请输入设备IP地址: " device_ip
        fi
        
        if [ -n "$device_ip" ]; then
            echo ""
            echo -e "${BLUE}🔌 尝试连接到 $device_ip:5555...${NC}"
            
            # 尝试连接
            adb connect "$device_ip:5555"
            
            # 等待连接建立
            sleep 2
            
            # 再次检查设备
            DEVICES=$(adb devices | grep -v "List" | grep "device$" | wc -l)
            
            if [ "$DEVICES" -eq 0 ]; then
                echo -e "${RED}❌ WiFi连接失败${NC}"
                echo ""
                echo -e "${YELLOW}📱 如何启用WiFi调试（手机重启后需要重新设置）：${NC}"
                echo ""
                echo -e "${BLUE}方法1: 通过USB首次连接（推荐）${NC}"
                echo "  1. 用USB线连接手机到电脑"
                echo "  2. 手机上启用「开发者选项」->「USB调试」"
                echo "  3. 运行命令: adb tcpip 5555"
                echo "  4. 拔掉USB线"
                echo "  5. 再次运行此脚本，输入手机IP地址"
                echo ""
                echo -e "${BLUE}方法2: 使用无线调试（Android 11+）${NC}"
                echo "  1. 手机进入「开发者选项」->「无线调试」"
                echo "  2. 启用「无线调试」"
                echo "  3. 点击「使用配对码配对设备」"
                echo "  4. 在电脑运行: adb pair <IP>:<配对端口>"
                echo "  5. 输入配对码"
                echo "  6. 然后运行: adb connect <IP>:<连接端口>"
                echo ""
                echo -e "${BLUE}方法3: 直接USB连接${NC}"
                echo "  1. 用USB线连接手机到电脑"
                echo "  2. 启用USB调试"
                echo "  3. 直接运行此脚本"
                echo ""
                echo "当前设备列表："
                adb devices
                echo ""
                
                read -p "是否通过USB连接并启用WiFi调试? [Y/n]: " enable_wifi
                if [ "$enable_wifi" != "n" ] && [ "$enable_wifi" != "N" ]; then
                    echo ""
                    echo -e "${BLUE}请用USB连接手机，然后按回车继续...${NC}"
                    read
                    
                    # 检查USB连接
                    USB_DEVICES=$(adb devices | grep -v "List" | grep "device$" | wc -l)
                    if [ "$USB_DEVICES" -gt 0 ]; then
                        echo -e "${GREEN}✅ 检测到USB设备${NC}"
                        echo -e "${BLUE}正在启用WiFi调试...${NC}"
                        adb tcpip 5555
                        sleep 2
                        echo ""
                        echo -e "${GREEN}✅ WiFi调试已启用！${NC}"
                        echo -e "${YELLOW}现在可以拔掉USB线，然后重新运行此脚本${NC}"
                        exit 0
                    else
                        echo -e "${RED}❌ 未检测到USB设备${NC}"
                        exit 1
                    fi
                else
                    exit 1
                fi
            else
                echo -e "${GREEN}✅ WiFi连接成功！${NC}"
                # 保存成功连接的IP地址
                echo "$device_ip" > "$WIFI_CONFIG_FILE"
                echo -e "${BLUE}💾 已保存设备IP地址，下次将自动连接${NC}"
            fi
        else
            echo -e "${RED}❌ 未输入IP地址${NC}"
            exit 1
        fi
    else
        echo ""
        echo "请确保："
        echo "  1. 已连接Android设备并启用USB调试"
        echo "  2. 或已启动Android模拟器"
        echo ""
        echo "检查设备连接："
        adb devices
        exit 1
    fi
elif [ "$DEVICES" -eq 1 ]; then
    DEVICE_NAME=$(adb devices | grep "device$" | awk '{print $1}')
    if [[ "$DEVICE_NAME" == *":"* ]]; then
        echo -e "${GREEN}✅ 检测到WiFi设备: $DEVICE_NAME${NC}"
    else
        echo -e "${GREEN}✅ 检测到USB设备: $DEVICE_NAME${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  检测到多个设备:${NC}"
    adb devices
    echo ""
    
    # 检查是否有USB设备
    USB_COUNT=$(adb devices | grep -v "List" | grep -v ":" | grep "device$" | wc -l)
    if [ "$USB_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✅ 优先使用USB设备进行安装${NC}"
        # 断开WiFi连接，只保留USB
        WIFI_DEVICES=$(adb devices | grep -v "List" | grep ":" | grep "device$" | awk '{print $1}')
        for wifi_dev in $WIFI_DEVICES; do
            echo -e "${BLUE}断开WiFi设备: $wifi_dev${NC}"
            adb disconnect "$wifi_dev" > /dev/null 2>&1
        done
        
        # 等待断开完成
        sleep 1
        
        # 获取USB设备ID
        DEVICE_NAME=$(adb devices | grep -v "List" | grep -v ":" | grep "device$" | head -1 | awk '{print $1}')
        echo -e "${GREEN}使用设备: $DEVICE_NAME${NC}"
    else
        echo -e "${YELLOW}将使用第一个设备进行安装${NC}"
        DEVICE_NAME=$(adb devices | grep "device$" | head -1 | awk '{print $1}')
    fi
fi

# 保存选中的设备ID供后续使用
SELECTED_DEVICE=""
if [ "$DEVICES" -eq 1 ]; then
    SELECTED_DEVICE=$(adb devices | grep "device$" | awk '{print $1}')
elif [ "$DEVICES" -gt 1 ]; then
    SELECTED_DEVICE="$DEVICE_NAME"
fi

echo ""

# 显示菜单
echo -e "${BLUE}请选择操作:${NC}"
echo "  1) 构建并安装Debug版本 (推荐)"
echo "  2) 快速构建安装 (./gradlew assembleDebug && installDebug)"
echo "  3) 构建并安装Release版本"
echo "  4) 仅构建Debug APK"
echo "  5) 仅构建Release APK"
echo "  6) 清理项目"
echo "  7) 清理并重新构建"
echo "  8) 启动应用"
echo "  9) 查看日志"
echo "  10) 卸载应用"
echo "  0) 退出"
echo ""

read -p "请输入选项 [0-10]: " choice

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
        
        echo -e "${BLUE}🚀 启动应用...${NC}"
        if [ -n "$SELECTED_DEVICE" ]; then
            adb -s "$SELECTED_DEVICE" shell am start -n com.ihealth.nal2.api.caller/.MainActivity
        else
            adb shell am start -n com.ihealth.nal2.api.caller/.MainActivity
        fi
        echo ""
        echo -e "${GREEN}✅ 应用已启动${NC}"
        echo ""
        
        echo -e "${BLUE}📋 显示应用日志 (Ctrl+C 退出)...${NC}"
        echo ""
        if [ -n "$SELECTED_DEVICE" ]; then
            adb -s "$SELECTED_DEVICE" logcat -s "FuncApp4NAL2:*" "Nal2Manager:*" "HttpServer:*" "AndroidRuntime:E"
        else
            adb logcat -s "FuncApp4NAL2:*" "Nal2Manager:*" "HttpServer:*" "AndroidRuntime:E"
        fi
        ;;
        
    2)
        echo ""
        echo -e "${BLUE}🚀 快速构建安装 (您常用的命令)${NC}"
        ./gradlew assembleDebug && ./gradlew installDebug
        
        echo ""
        echo -e "${GREEN}✅ 构建和安装完成！${NC}"
        ;;
        
    3)
        echo ""
        echo -e "${BLUE}📦 递增版本号...${NC}"
        ./increment-version.sh
        
        echo -e "${BLUE}🔨 构建Release版本...${NC}"
        ./gradlew assembleRelease
        
        echo ""
        echo -e "${BLUE}📦 安装应用到设备...${NC}"
        if [ -n "$SELECTED_DEVICE" ]; then
            adb -s "$SELECTED_DEVICE" install -r app/build/outputs/apk/release/app-release.apk
        else
            adb install -r app/build/outputs/apk/release/app-release.apk
        fi
        
        echo ""
        echo -e "${GREEN}✅ 应用安装成功！${NC}"
        echo ""
        echo -e "${YELLOW}APK位置: app/build/outputs/apk/release/app-release.apk${NC}"
        
        # 自动打开 APK 所在文件夹
        echo ""
        echo -e "${BLUE}📂 打开 APK 文件夹...${NC}"
        open app/build/outputs/apk/release
        ;;
        
    4)
        echo ""
        echo -e "${BLUE}🔨 构建Debug APK...${NC}"
        ./gradlew assembleDebug
        
        echo ""
        echo -e "${GREEN}✅ 构建完成！${NC}"
        echo -e "${YELLOW}APK位置: app/build/outputs/apk/debug/app-debug.apk${NC}"
        ;;
        
    5)
        echo ""
        echo -e "${BLUE}📦 递增版本号...${NC}"
        ./increment-version.sh
        
        echo -e "${BLUE}🔨 构建Release APK...${NC}"
        ./gradlew assembleRelease
        
        echo ""
        echo -e "${GREEN}✅ 构建完成！${NC}"
        echo -e "${YELLOW}APK位置: app/build/outputs/apk/release/app-release.apk${NC}"
        
        # 自动打开 APK 所在文件夹
        echo ""
        echo -e "${BLUE}📂 打开 APK 文件夹...${NC}"
        open app/build/outputs/apk/release
        ;;
        
    6)
        echo ""
        echo -e "${BLUE}🧹 清理项目...${NC}"
        ./gradlew clean
        
        echo ""
        echo -e "${GREEN}✅ 清理完成！${NC}"
        ;;
        
    7)
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
        
    8)
        echo ""
        echo -e "${BLUE}🚀 启动应用...${NC}"
        if [ -n "$SELECTED_DEVICE" ]; then
            adb -s "$SELECTED_DEVICE" shell am start -n com.ihealth.nal2.api.caller/.MainActivity
        else
            adb shell am start -n com.ihealth.nal2.api.caller/.MainActivity
        fi
        
        echo ""
        echo -e "${GREEN}✅ 应用已启动${NC}"
        echo ""
        
        read -p "是否查看实时日志? [Y/n]: " viewlog
        if [ "$viewlog" != "n" ] && [ "$viewlog" != "N" ]; then
            echo -e "${BLUE}📋 显示应用日志 (Ctrl+C 退出)...${NC}"
            echo ""
            if [ -n "$SELECTED_DEVICE" ]; then
                adb -s "$SELECTED_DEVICE" logcat -s "FuncApp4NAL2:*" "Nal2Manager:*" "HttpServer:*" "AndroidRuntime:E"
            else
                adb logcat -s "FuncApp4NAL2:*" "Nal2Manager:*" "HttpServer:*" "AndroidRuntime:E"
            fi
        fi
        ;;
        
    9)
        echo ""
        echo -e "${BLUE}📋 显示应用日志 (Ctrl+C 退出)...${NC}"
        echo ""
        if [ -n "$SELECTED_DEVICE" ]; then
            adb -s "$SELECTED_DEVICE" logcat -s "FuncApp4NAL2:*" "Nal2Manager:*" "HttpServer:*" "AndroidRuntime:E"
        else
            adb logcat -s "FuncApp4NAL2:*" "Nal2Manager:*" "HttpServer:*" "AndroidRuntime:E"
        fi
        ;;
        
    10)
        echo ""
        echo -e "${BLUE}🗑️  卸载应用...${NC}"
        if [ -n "$SELECTED_DEVICE" ]; then
            adb -s "$SELECTED_DEVICE" uninstall com.ihealth.nal2.api.caller
        else
            adb uninstall com.ihealth.nal2.api.caller
        fi
        
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
