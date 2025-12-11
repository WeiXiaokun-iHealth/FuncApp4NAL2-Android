package com.ihealth.nal2.api.caller

import android.content.Context
import java.io.File
import java.io.PrintWriter
import java.io.StringWriter
import java.text.SimpleDateFormat
import java.util.*

/**
 * 全局异常捕获处理器
 * 用于捕获应用崩溃信息并保存到日志文件
 */
class CrashHandler private constructor() : Thread.UncaughtExceptionHandler {

    private var mContext: Context? = null
    private var mDefaultHandler: Thread.UncaughtExceptionHandler? = null

    companion object {
        @Volatile
        private var instance: CrashHandler? = null

        fun getInstance(): CrashHandler {
            return instance ?: synchronized(this) {
                instance ?: CrashHandler().also { instance = it }
            }
        }
    }

    /**
     * 初始化崩溃处理器
     */
    fun init(context: Context) {
        mContext = context.applicationContext
        mDefaultHandler = Thread.getDefaultUncaughtExceptionHandler()
        Thread.setDefaultUncaughtExceptionHandler(this)
    }

    override fun uncaughtException(thread: Thread, ex: Throwable) {
        try {
            // 保存崩溃信息到日志文件
            saveCrashInfoToFile(ex)
        } catch (e: Exception) {
            e.printStackTrace()
        }

        // 调用系统默认的异常处理器
        mDefaultHandler?.uncaughtException(thread, ex)
    }

    /**
     * 保存崩溃信息到文件
     */
    private fun saveCrashInfoToFile(ex: Throwable) {
        val context = mContext ?: return

        try {
            val timestamp = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault()).format(Date())
            val crashInfo = buildCrashInfo(timestamp, ex)

            // 追加到现有日志文件
            val logFile = File(context.filesDir, "app_logs.txt")
            val existingLogs = if (logFile.exists()) logFile.readText() else ""
            
            val crashLogEntry = "$timestamp|ERROR|💥 应用崩溃\n$timestamp|ERROR|$crashInfo"
            
            val updatedLogs = if (existingLogs.isNotEmpty()) {
                "$existingLogs\n$crashLogEntry"
            } else {
                crashLogEntry
            }
            
            logFile.writeText(updatedLogs)

            // 同时保存单独的崩溃日志文件
            val crashFileName = "crash_${SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(Date())}.txt"
            val crashFile = File(context.filesDir, crashFileName)
            crashFile.writeText(buildDetailedCrashInfo(timestamp, ex))

        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    /**
     * 构建简洁的崩溃信息（用于主日志）
     */
    private fun buildCrashInfo(timestamp: String, ex: Throwable): String {
        val sb = StringBuilder()
        sb.append("异常类型: ${ex.javaClass.name}\n")
        sb.append("$timestamp|ERROR|异常消息: ${ex.message ?: "无消息"}\n")
        
        // 获取堆栈跟踪的前5行
        val stackTrace = ex.stackTrace
        val maxLines = minOf(5, stackTrace.size)
        for (i in 0 until maxLines) {
            sb.append("$timestamp|ERROR|  at ${stackTrace[i]}\n")
        }
        if (stackTrace.size > maxLines) {
            sb.append("$timestamp|ERROR|  ... ${stackTrace.size - maxLines} more")
        }
        
        return sb.toString().trimEnd()
    }

    /**
     * 构建详细的崩溃信息（用于单独的崩溃日志文件）
     */
    private fun buildDetailedCrashInfo(timestamp: String, ex: Throwable): String {
        val sb = StringBuilder()
        sb.append("=".repeat(60)).append("\n")
        sb.append("应用崩溃报告\n")
        sb.append("=".repeat(60)).append("\n\n")
        
        sb.append("时间: $timestamp\n")
        sb.append("异常类型: ${ex.javaClass.name}\n")
        sb.append("异常消息: ${ex.message ?: "无消息"}\n\n")
        
        sb.append("完整堆栈跟踪:\n")
        sb.append("-".repeat(60)).append("\n")
        
        val sw = StringWriter()
        val pw = PrintWriter(sw)
        ex.printStackTrace(pw)
        sb.append(sw.toString())
        
        // 如果有原因异常，也打印出来
        var cause = ex.cause
        while (cause != null) {
            sb.append("\n").append("=".repeat(60)).append("\n")
            sb.append("原因异常:\n")
            sb.append("-".repeat(60)).append("\n")
            val causeSw = StringWriter()
            val causePw = PrintWriter(causeSw)
            cause.printStackTrace(causePw)
            sb.append(causeSw.toString())
            cause = cause.cause
        }
        
        sb.append("\n").append("=".repeat(60)).append("\n")
        
        return sb.toString()
    }
}
