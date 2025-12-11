package com.ihealth.nal2.api.caller

import android.app.Application

/**
 * 自定义 Application 类
 * 用于初始化全局组件
 */
class MyApplication : Application() {

    override fun onCreate() {
        super.onCreate()
        
        // 初始化崩溃处理器
        CrashHandler.getInstance().init(this)
    }
}
