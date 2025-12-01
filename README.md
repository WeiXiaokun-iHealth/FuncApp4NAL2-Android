# FuncApp4NAL2 - Android Native Version

NAL2（National Acoustic Laboratories - Nonlinear 2）助听器验配算法的 Android 原生应用实现。

## 项目概述

这是 FuncApp4NAL2 的 Android 原生版本，完全使用 Kotlin/Java 开发，摆脱了 React Native 的架构限制。

### 主要功能

- ✅ NAL2 算法集成（通过 AAR 库）
- ✅ HTTP API 服务器（NanoHTTPD）
- ✅ WebSocket 支持
- ✅ 全局变量管理
- ✅ 实时日志查看
- ✅ 请求/响应监控
- ✅ 日志导出功能

## 技术栈

- **语言**: Kotlin + Java
- **最低 SDK**: Android 7.0 (API 24)
- **目标 SDK**: Android 14 (API 34)
- **HTTP 服务器**: NanoHTTPD
- **NAL2 库**: nl2-release.aar
- **架构**: MVVM + Repository 模式

## 项目结构

```
FuncApp4NAL2-Android/
├── app/
│   ├── src/
│   │   ├── main/
│   │   │   ├── java/com/funcapp4nal2/
│   │   │   │   ├── MainActivity.kt              # 主Activity
│   │   │   │   ├── ui/                          # UI层
│   │   │   │   │   ├── ServerStatusFragment.kt # 服务器状态界面
│   │   │   │   │   ├── LogViewerFragment.kt    # 日志查看器
│   │   │   │   │   └── GlobalVarsFragment.kt   # 全局变量管理
│   │   │   │   ├── server/                     # HTTP服务器
│   │   │   │   │   ├── HttpServer.kt           # HTTP服务器实现
│   │   │   │   │   └── RequestHandler.kt       # 请求处理器
│   │   │   │   ├── nal2/                       # NAL2集成
│   │   │   │   │   ├── Nal2Manager.kt          # NAL2管理器
│   │   │   │   │   └── Nal2Bridge.kt           # NAL2桥接层
│   │   │   │   ├── utils/                      # 工具类
│   │   │   │   │   ├── Logger.kt               # 日志工具
│   │   │   │   │   ├── GlobalVariables.kt      # 全局变量
│   │   │   │   │   └── NetworkUtils.kt         # 网络工具
│   │   │   │   └── viewmodel/                  # ViewModel层
│   │   │   │       └── MainViewModel.kt
│   │   │   ├── res/                            # 资源文件
│   │   │   │   ├── layout/                     # 布局文件
│   │   │   │   ├── values/                     # 值资源
│   │   │   │   └── drawable/                   # 图片资源
│   │   │   └── AndroidManifest.xml
│   │   └── test/                               # 单元测试
│   ├── build.gradle.kts                        # 应用级构建配置
│   └── libs/
│       └── nl2-release.aar                     # NAL2库
├── gradle/                                      # Gradle配置
├── build.gradle.kts                            # 项目级构建配置
├── settings.gradle.kts                         # 项目设置
└── README.md                                   # 本文件
```

## 快速开始

### 前置要求

- Android Studio Hedgehog (2023.1.1) 或更高版本
- JDK 17 或更高版本
- Android SDK (API 24-34)
- 已连接的 Android 设备或模拟器

### 构建步骤

1. **克隆项目**

```bash
cd FuncApp4NAL2-Android
```

2. **复制 NAL2 库**

```bash
# 从React Native项目复制NAL2库
cp ../FuncApp4NAL2/modules/nal2/android/libs/nl2-release.aar app/libs/
```

3. **打开项目**

- 使用 Android Studio 打开项目
- 等待 Gradle 同步完成

4. **运行应用**

- 点击运行按钮或使用快捷键 Shift+F10
- 选择目标设备

### 构建 APK

**Debug 版本**

```bash
./gradlew assembleDebug
# 输出: app/build/outputs/apk/debug/app-debug.apk
```

**Release 版本**

```bash
./gradlew assembleRelease
# 输出: app/build/outputs/apk/release/app-release.apk
```

## 功能说明

### 1. HTTP API 服务器

应用启动时自动启动 HTTP 服务器，默认端口 8080。

**API 端点**

```
POST http://<设备IP>:8080/api/nal2/process
Content-Type: application/json

{
  "sequence_num": 1,
  "function": "dllVersion",
  "input_parameters": {}
}
```

### 2. NAL2 函数支持

支持所有 46 个 NAL2 函数，包括：

- dllVersion
- RealEarInsertionGain_NL2
- CrossOverFrequencies_NL2
- CompressionThreshold_NL2
- 等等...

### 3. 全局变量管理

支持三个全局变量：

- **CFArray**: 交叉频率数组
- **FreqInCh**: 频率通道映射
- **CT**: 压缩阈值

### 4. 日志系统

- 实时日志显示
- 日志级别过滤（INFO, ERROR, SUCCESS）
- 日志导出到下载文件夹
- 全屏日志查看器

## 与 React Native 版本的对比

| 特性     | React Native 版本 | Android 原生版本 |
| -------- | ----------------- | ---------------- |
| 启动速度 | 较慢              | 快速             |
| 内存占用 | 较高              | 较低             |
| 性能     | 中等              | 优秀             |
| 包大小   | ~50MB             | ~15MB            |
| 维护难度 | 高                | 中等             |
| 调试体验 | 复杂              | 简单             |
| 热更新   | 支持              | 不支持           |

## 开发指南

### 添加新的 NAL2 函数

1. 在`Nal2Manager.kt`中添加函数实现
2. 在`Nal2Bridge.kt`中添加函数路由
3. 在`RequestHandler.kt`中处理 HTTP 请求

### 自定义 UI

所有 UI 组件都在`app/src/main/res/layout/`目录下，使用标准的 Android XML 布局。

### 修改服务器端口

在`MainActivity.kt`中修改`DEFAULT_PORT`常量。

## 测试

### 单元测试

```bash
./gradlew test
```

### UI 测试

```bash
./gradlew connectedAndroidTest
```

## 常见问题

### Q: 服务器无法启动

A: 检查端口是否被占用，尝试更换端口号。

### Q: NAL2 函数调用失败

A: 确保 nl2-release.aar 已正确放置在 app/libs/目录下。

### Q: 无法导出日志

A: 检查存储权限是否已授予。

## 版本历史

- **v1.0.0** (2025-11-28)
  - 初始版本
  - 完整的 NAL2 函数支持
  - HTTP API 服务器
  - 日志系统

## 许可证

与原 React Native 项目保持一致。

## 联系方式

如有问题，请提交 Issue 或联系开发团队。
