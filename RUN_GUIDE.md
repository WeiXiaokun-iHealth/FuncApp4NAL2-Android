# FuncApp4NAL2 Android 运行指南

## 📋 前提条件

1. **Android Studio** (推荐 Arctic Fox 或更高版本)
2. **JDK 11** 或更高版本
3. **Android SDK** (API Level 24 或更高)
4. **Android 设备或模拟器**

## 🚀 快速开始

### 方法一：使用 Android Studio（推荐）

1. **打开项目**

   ```bash
   # 在Android Studio中选择 File -> Open
   # 选择项目目录: /Users/weixiaokun/HearingProject/FuncApp4NAL2-Android
   ```

2. **同步 Gradle**

   - Android Studio 会自动提示同步 Gradle
   - 或手动点击 `File -> Sync Project with Gradle Files`
   - 等待依赖下载完成

3. **连接设备**

   - 连接 Android 设备并启用 USB 调试
   - 或启动 Android 模拟器

4. **运行应用**
   - 点击工具栏的绿色运行按钮 ▶️
   - 或使用快捷键 `Shift + F10` (Windows/Linux) / `Control + R` (Mac)

### 方法二：使用命令行

1. **检查设备连接**

   ```bash
   adb devices
   ```

   应该看到已连接的设备列表

2. **使用运行脚本**
   ```bash
   cd /Users/weixiaokun/HearingProject/FuncApp4NAL2-Android
   ./run-app.sh
   ```
3. **选择操作**
   - 选项 1: 构建并安装 Debug 版本（推荐用于开发）
   - 选项 2: 构建并安装 Release 版本
   - 选项 7: 启动已安装的应用
   - 选项 8: 查看实时日志

### 方法三：手动 Gradle 命令

1. **构建 Debug APK**

   ```bash
   ./gradlew assembleDebug
   ```

2. **安装到设备**

   ```bash
   ./gradlew installDebug
   ```

3. **启动应用**

   ```bash
   adb shell am start -n com.funcapp4nal2/.MainActivity
   ```

4. **查看日志**
   ```bash
   adb logcat -s "FuncApp4NAL2:*" "Nal2Manager:*" "AndroidRuntime:E"
   ```

## 📱 应用功能

当前版本是一个基础的 NAL2 测试应用，包含：

- ✅ NAL2 库初始化
- ✅ DLL 版本显示
- ✅ 基础 UI 界面

### 预期输出

应用启动后应该显示：

```
FuncApp4NAL2 Android

✅ NAL2初始化成功！

DLL版本: 1.0

应用已准备就绪
```

## 🔧 故障排除

### 问题 1: Gradle 同步失败

**解决方案：**

```bash
# 清理Gradle缓存
./gradlew clean

# 重新下载依赖
./gradlew build --refresh-dependencies
```

### 问题 2: 找不到设备

**解决方案：**

```bash
# 检查ADB连接
adb devices

# 重启ADB服务
adb kill-server
adb start-server
```

### 问题 3: 应用崩溃

**解决方案：**

```bash
# 查看详细日志
adb logcat | grep -E "FuncApp4NAL2|AndroidRuntime"

# 或使用过滤后的日志
adb logcat -s "FuncApp4NAL2:*" "Nal2Manager:*" "AndroidRuntime:E"
```

### 问题 4: NAL2 库加载失败

**检查：**

1. 确认 `app/libs/nl2-release.aar` 文件存在
2. 确认 `app/src/main/java/com/nal2/Nal2Manager.java` 文件存在
3. 检查 `app/build.gradle.kts` 中的依赖配置

## 📂 项目结构

```
FuncApp4NAL2-Android/
├── app/
│   ├── src/
│   │   └── main/
│   │       ├── java/
│   │       │   ├── com/funcapp4nal2/
│   │       │   │   └── MainActivity.kt      # 主Activity
│   │       │   └── com/nal2/
│   │       │       └── Nal2Manager.java     # NAL2管理器
│   │       └── AndroidManifest.xml
│   ├── libs/
│   │   └── nl2-release.aar                  # NAL2库
│   └── build.gradle.kts
├── build.gradle.kts
├── settings.gradle.kts
├── run-app.sh                               # 运行脚本
└── README.md
```

## 🎯 下一步开发

当前项目是基础框架，后续可以添加：

1. **HTTP 服务器** - 提供 NAL2 API 接口
2. **WebSocket 支持** - 实时通信
3. **完整的 NAL2 API** - 所有 NAL2 功能
4. **UI 界面** - 用户友好的界面
5. **数据持久化** - 保存配置和结果

## 📞 技术支持

如遇到问题，请检查：

1. Android Studio 的 Build 输出
2. Logcat 日志
3. Gradle 控制台输出

## 📝 版本信息

- **项目版本**: 1.0.0
- **最低 Android 版本**: API 24 (Android 7.0)
- **目标 Android 版本**: API 34 (Android 14)
- **Kotlin 版本**: 1.9.0
- **Gradle 版本**: 8.2
