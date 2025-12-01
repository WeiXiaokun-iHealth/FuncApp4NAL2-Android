#!/bin/bash

# 自动递增 versionCode 脚本
# 用于在构建 Release 版本时自动增加版本号

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BUILD_GRADLE="app/build.gradle.kts"

# 检查文件是否存在
if [ ! -f "$BUILD_GRADLE" ]; then
    echo -e "${RED}❌ 错误: 找不到 $BUILD_GRADLE 文件${NC}"
    exit 1
fi

# 读取当前的 versionCode
CURRENT_VERSION=$(grep "versionCode = " "$BUILD_GRADLE" | sed 's/.*versionCode = \([0-9]*\).*/\1/')

if [ -z "$CURRENT_VERSION" ]; then
    echo -e "${RED}❌ 错误: 无法读取当前的 versionCode${NC}"
    exit 1
fi

# 计算新的版本号
NEW_VERSION=$((CURRENT_VERSION + 1))

echo -e "${BLUE}📦 版本号递增${NC}"
echo "  当前版本: $CURRENT_VERSION"
echo "  新版本: $NEW_VERSION"
echo ""

# 更新 build.gradle.kts 文件
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/versionCode = $CURRENT_VERSION/versionCode = $NEW_VERSION/" "$BUILD_GRADLE"
else
    # Linux
    sed -i "s/versionCode = $CURRENT_VERSION/versionCode = $NEW_VERSION/" "$BUILD_GRADLE"
fi

# 验证更新
UPDATED_VERSION=$(grep "versionCode = " "$BUILD_GRADLE" | sed 's/.*versionCode = \([0-9]*\).*/\1/')

if [ "$UPDATED_VERSION" = "$NEW_VERSION" ]; then
    echo -e "${GREEN}✅ 版本号已更新: $CURRENT_VERSION -> $NEW_VERSION${NC}"
    echo ""
else
    echo -e "${RED}❌ 错误: 版本号更新失败${NC}"
    exit 1
fi
