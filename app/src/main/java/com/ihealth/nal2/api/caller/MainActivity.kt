package com.ihealth.nal2.api.caller

import android.Manifest
import android.content.ClipData
import android.content.ClipboardManager
import android.content.ContentValues
import android.content.Context
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.provider.MediaStore
import android.view.View
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.ihealth.nal2.api.caller.server.HttpServer
import com.ihealth.nal2.api.caller.utils.GlobalVariables
import com.google.gson.GsonBuilder
import java.io.File
import java.io.FileOutputStream
import java.text.SimpleDateFormat
import java.util.*

class MainActivity : AppCompatActivity() {

    private lateinit var httpServer: HttpServer
    private val logs = mutableListOf<LogEntry>()
    private lateinit var logAdapter: LogAdapter
    
    private lateinit var tvStatus: TextView
    private lateinit var tvIpAddress: TextView
    private lateinit var tvPort: TextView
    private lateinit var tvApiUrl: TextView
    private lateinit var tvLogsTitle: TextView
    private lateinit var tvLastRequest: TextView
    private lateinit var tvLastResponse: TextView
    private lateinit var cardLastRequest: View
    private lateinit var cardLastResponse: View
    private lateinit var rvLogs: RecyclerView
    private lateinit var btnClearLogs: Button
    private lateinit var btnDownloadLogs: Button
    private lateinit var btnFullScreenLogs: Button
    private lateinit var btnCopyApi: Button
    private lateinit var btnRefresh: Button
    
    // 折叠/展开相关
    private lateinit var headerApiEndpoint: View
    private lateinit var iconApiEndpoint: TextView
    private lateinit var contentApiEndpoint: View
    private var isApiEndpointExpanded = false
    
    private lateinit var headerLastRequest: View
    private lateinit var iconLastRequest: TextView
    private var isLastRequestExpanded = false
    
    private lateinit var headerLastResponse: View
    private lateinit var iconLastResponse: TextView
    private var isLastResponseExpanded = false
    
    private val STORAGE_PERMISSION_CODE = 100
    
    // 全局变量 UI 控件
    private lateinit var tvCFArrayValue: TextView
    private lateinit var tvCFArrayInfo: TextView
    private lateinit var tvFreqInChValue: TextView
    private lateinit var tvFreqInChInfo: TextView
    private lateinit var tvCTValue: TextView
    private lateinit var tvCTInfo: TextView
    private lateinit var btnDeleteCFArray: Button
    private lateinit var btnDeleteFreqInCh: Button
    private lateinit var btnDeleteCT: Button
    private lateinit var btnRefreshGlobalVars: Button
    private lateinit var btnClearAllGlobalVars: Button
    
    private val gson = GsonBuilder().setPrettyPrinting().create()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        initViews()
        setupRecyclerView()
        loadLogsFromFile()  // 加载之前保存的日志
        startHttpServer()
        setupListeners()
    }

    private fun initViews() {
        tvStatus = findViewById(R.id.tvStatus)
        tvIpAddress = findViewById(R.id.tvIpAddress)
        tvPort = findViewById(R.id.tvPort)
        tvApiUrl = findViewById(R.id.tvApiUrl)
        tvLogsTitle = findViewById(R.id.tvLogsTitle)
        tvLastRequest = findViewById(R.id.tvLastRequest)
        tvLastResponse = findViewById(R.id.tvLastResponse)
        cardLastRequest = findViewById(R.id.cardLastRequest)
        cardLastResponse = findViewById(R.id.cardLastResponse)
        rvLogs = findViewById(R.id.rvLogs)
        btnClearLogs = findViewById(R.id.btnClearLogs)
        btnDownloadLogs = findViewById(R.id.btnDownloadLogs)
        btnFullScreenLogs = findViewById(R.id.btnFullScreenLogs)
        btnCopyApi = findViewById(R.id.btnCopyApi)
        btnRefresh = findViewById(R.id.btnRefresh)
        
        // 设置 TextView 可滚动
        tvLastRequest.movementMethod = android.text.method.ScrollingMovementMethod()
        tvLastResponse.movementMethod = android.text.method.ScrollingMovementMethod()
        
        // 处理触摸事件，防止滚动冲突
        tvLastRequest.setOnTouchListener { v, event ->
            v.parent.requestDisallowInterceptTouchEvent(true)
            when (event.action and android.view.MotionEvent.ACTION_MASK) {
                android.view.MotionEvent.ACTION_UP -> {
                    v.parent.requestDisallowInterceptTouchEvent(false)
                }
            }
            false
        }
        
        tvLastResponse.setOnTouchListener { v, event ->
            v.parent.requestDisallowInterceptTouchEvent(true)
            when (event.action and android.view.MotionEvent.ACTION_MASK) {
                android.view.MotionEvent.ACTION_UP -> {
                    v.parent.requestDisallowInterceptTouchEvent(false)
                }
            }
            false
        }
        
        // 全局变量控件
        tvCFArrayValue = findViewById(R.id.tvCFArrayValue)
        tvCFArrayInfo = findViewById(R.id.tvCFArrayInfo)
        tvFreqInChValue = findViewById(R.id.tvFreqInChValue)
        tvFreqInChInfo = findViewById(R.id.tvFreqInChInfo)
        tvCTValue = findViewById(R.id.tvCTValue)
        tvCTInfo = findViewById(R.id.tvCTInfo)
        btnDeleteCFArray = findViewById(R.id.btnDeleteCFArray)
        btnDeleteFreqInCh = findViewById(R.id.btnDeleteFreqInCh)
        btnDeleteCT = findViewById(R.id.btnDeleteCT)
        btnRefreshGlobalVars = findViewById(R.id.btnRefreshGlobalVars)
        btnClearAllGlobalVars = findViewById(R.id.btnClearAllGlobalVars)
        
        // 折叠/展开控件
        headerApiEndpoint = findViewById(R.id.headerApiEndpoint)
        iconApiEndpoint = findViewById(R.id.iconApiEndpoint)
        contentApiEndpoint = findViewById(R.id.contentApiEndpoint)
        
        headerLastRequest = findViewById(R.id.headerLastRequest)
        iconLastRequest = findViewById(R.id.iconLastRequest)
        
        headerLastResponse = findViewById(R.id.headerLastResponse)
        iconLastResponse = findViewById(R.id.iconLastResponse)
        
        // 设置初始折叠状态
        contentApiEndpoint.visibility = View.GONE
        
        // 初始化全局变量显示
        updateGlobalVariablesUI()
        
        // 添加全局变量监听器
        GlobalVariables.addListener { state ->
            runOnUiThread {
                updateGlobalVariablesUI()
            }
        }
    }

    private fun setupRecyclerView() {
        logAdapter = LogAdapter(logs)
        rvLogs.apply {
            layoutManager = LinearLayoutManager(this@MainActivity)
            adapter = logAdapter
        }
    }

    private fun startHttpServer() {
        try {
            addLog("INFO", "正在启动HTTP服务器...")
            
            // 先尝试停止可能存在的旧服务器实例
            try {
                if (::httpServer.isInitialized) {
                    httpServer.stop()
                    Thread.sleep(500) // 等待端口释放
                }
            } catch (e: Exception) {
                // 忽略停止错误
            }
            
            httpServer = HttpServer(this, 8080)
            
            // 设置回调
            httpServer.onRequestReceived = { request ->
                runOnUiThread {
                    cardLastRequest.visibility = View.VISIBLE
                    tvLastRequest.text = formatJson(request)
                }
            }
            
            httpServer.onResponseSent = { response ->
                runOnUiThread {
                    cardLastResponse.visibility = View.VISIBLE
                    tvLastResponse.text = formatJson(response)
                }
            }
            
            httpServer.onLog = { type, message ->
                runOnUiThread {
                    addLog(type, message)
                }
            }
            
            httpServer.start()
            
            val ipAddress = HttpServer.getLocalIpAddress()
            val port = 8080
            
            tvStatus.text = "服务器运行中"
            tvIpAddress.text = ipAddress
            tvPort.text = port.toString()
            tvApiUrl.text = "http://$ipAddress:$port/api/nal2/process"
            
            addLog("SUCCESS", "服务器启动成功 - $ipAddress:$port")
            
        } catch (e: Exception) {
            addLog("ERROR", "服务器启动失败: ${e.message}")
            tvStatus.text = "服务器启动失败"
            tvIpAddress.text = "启动失败"
            tvApiUrl.text = "服务器未运行"
        }
    }

    private fun updateGlobalVariablesUI() {
        val state = GlobalVariables.getAllVariables()
        
        // CFArray
        if (state.CFArray.isEmpty()) {
            tvCFArrayValue.text = "空 []"
            tvCFArrayInfo.text = "长度: 0"
            btnDeleteCFArray.isEnabled = false
            btnDeleteCFArray.alpha = 0.5f
        } else {
            tvCFArrayValue.text = "[${state.CFArray.joinToString(", ") { "%.2f".format(it) }}]"
            tvCFArrayInfo.text = "长度: ${state.CFArray.size}"
            btnDeleteCFArray.isEnabled = true
            btnDeleteCFArray.alpha = 1.0f
        }
        
        // FreqInCh
        if (state.FreqInCh.isEmpty()) {
            tvFreqInChValue.text = "空 []"
            tvFreqInChInfo.text = "长度: 0"
            btnDeleteFreqInCh.isEnabled = false
            btnDeleteFreqInCh.alpha = 0.5f
        } else {
            tvFreqInChValue.text = "[${state.FreqInCh.joinToString(", ")}]"
            tvFreqInChInfo.text = "长度: ${state.FreqInCh.size}"
            btnDeleteFreqInCh.isEnabled = true
            btnDeleteFreqInCh.alpha = 1.0f
        }
        
        // CT
        if (state.CT.isEmpty()) {
            tvCTValue.text = "空 []"
            tvCTInfo.text = "长度: 0"
            btnDeleteCT.isEnabled = false
            btnDeleteCT.alpha = 0.5f
        } else {
            tvCTValue.text = "[${state.CT.joinToString(", ") { "%.2f".format(it) }}]"
            tvCTInfo.text = "长度: ${state.CT.size}"
            btnDeleteCT.isEnabled = true
            btnDeleteCT.alpha = 1.0f
        }
        
        // 清空全部按钮
        val hasAnyData = state.CFArray.isNotEmpty() || state.FreqInCh.isNotEmpty() || state.CT.isNotEmpty()
        btnClearAllGlobalVars.isEnabled = hasAnyData
        btnClearAllGlobalVars.alpha = if (hasAnyData) 1.0f else 0.5f
    }
    
    private fun setupListeners() {
        // 全局变量刷新按钮
        btnRefreshGlobalVars.setOnClickListener {
            val nal2Manager = com.nal2.Nal2Manager.getInstance(this)
            var refreshed = false
            
            // 刷新 CrossOverFrequencies
            if (nal2Manager.hasCrossOverResult()) {
                addLog("INFO", "🔄 从 OutputResult 刷新 CrossOverFrequencies...")
                val refreshResult = nal2Manager.refreshCrossOverFrequencies()
                if (refreshResult != null) {
                    GlobalVariables.setCFArray(refreshResult.CFArray)
                    GlobalVariables.setFreqInCh(refreshResult.FreqInCh)
                    addLog("SUCCESS", "✅ CFArray 和 FreqInCh 已刷新")
                    addLog("DEBUG", "  CFArray: ${refreshResult.CFArray.take(5).joinToString(", ")}${if (refreshResult.CFArray.size > 5) " ..." else ""}")
                    addLog("DEBUG", "  FreqInCh: ${refreshResult.FreqInCh.take(5).joinToString(", ")}${if (refreshResult.FreqInCh.size > 5) " ..." else ""}")
                    refreshed = true
                }
            }
            
            // 刷新 CompressionThreshold
            if (nal2Manager.hasCompressionThresholdResult()) {
                addLog("INFO", "🔄 从 OutputResult 刷新 CompressionThreshold...")
                val refreshCT = nal2Manager.refreshCompressionThreshold()
                if (refreshCT != null) {
                    GlobalVariables.setCT(refreshCT)
                    addLog("SUCCESS", "✅ CT 已刷新")
                    addLog("DEBUG", "  CT: ${refreshCT.take(5).joinToString(", ")}${if (refreshCT.size > 5) " ..." else ""}")
                    refreshed = true
                }
            }
            
            if (refreshed) {
                Toast.makeText(this, "✅ 全局变量已刷新", Toast.LENGTH_SHORT).show()
            } else {
                addLog("WARN", "⚠️ 没有保存的 OutputResult")
                addLog("INFO", "💡 提示：请先通过 API 调用 CrossOverFrequencies_NL2 或 CompressionThreshold_NL2")
                Toast.makeText(this, "⚠️ 请先调用相关 API 函数", Toast.LENGTH_LONG).show()
            }
        }
        
        // 全局变量删除按钮
        btnDeleteCFArray.setOnClickListener {
            AlertDialog.Builder(this)
                .setTitle("确认删除")
                .setMessage("确定要删除 CFArray 吗？")
                .setPositiveButton("删除") { _, _ ->
                    GlobalVariables.deleteCFArray()
                    Toast.makeText(this, "CFArray 已删除", Toast.LENGTH_SHORT).show()
                    addLog("INFO", "CFArray 已删除")
                }
                .setNegativeButton("取消", null)
                .show()
        }
        
        btnDeleteFreqInCh.setOnClickListener {
            AlertDialog.Builder(this)
                .setTitle("确认删除")
                .setMessage("确定要删除 FreqInCh 吗？")
                .setPositiveButton("删除") { _, _ ->
                    GlobalVariables.deleteFreqInCh()
                    Toast.makeText(this, "FreqInCh 已删除", Toast.LENGTH_SHORT).show()
                    addLog("INFO", "FreqInCh 已删除")
                }
                .setNegativeButton("取消", null)
                .show()
        }
        
        btnDeleteCT.setOnClickListener {
            AlertDialog.Builder(this)
                .setTitle("确认删除")
                .setMessage("确定要删除 CT 吗？")
                .setPositiveButton("删除") { _, _ ->
                    GlobalVariables.deleteCT()
                    Toast.makeText(this, "CT 已删除", Toast.LENGTH_SHORT).show()
                    addLog("INFO", "CT 已删除")
                }
                .setNegativeButton("取消", null)
                .show()
        }
        
        btnClearAllGlobalVars.setOnClickListener {
            AlertDialog.Builder(this)
                .setTitle("确认清空")
                .setMessage("确定要清空所有全局变量吗？")
                .setPositiveButton("清空") { _, _ ->
                    GlobalVariables.clearAll()
                    Toast.makeText(this, "所有全局变量已清空", Toast.LENGTH_SHORT).show()
                    addLog("INFO", "所有全局变量已清空")
                }
                .setNegativeButton("取消", null)
                .show()
        }
        
        btnClearLogs.setOnClickListener {
            if (logs.isEmpty()) {
                Toast.makeText(this, "没有日志可清除", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            
            AlertDialog.Builder(this)
                .setTitle("确认清除")
                .setMessage("确定要清除所有日志吗？")
                .setPositiveButton("清除") { _, _ ->
                    logAdapter.clearLogs()
                    updateLogsTitle()
                    // 清除保存的日志文件
                    try {
                        val file = File(filesDir, "app_logs.txt")
                        if (file.exists()) {
                            file.delete()
                        }
                    } catch (e: Exception) {
                        e.printStackTrace()
                    }
                    Toast.makeText(this, "日志已清除", Toast.LENGTH_SHORT).show()
                }
                .setNegativeButton("取消", null)
                .show()
        }
        
        btnCopyApi.setOnClickListener {
            val apiUrl = tvApiUrl.text.toString()
            val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
            val clip = ClipData.newPlainText("API URL", apiUrl)
            clipboard.setPrimaryClip(clip)
            Toast.makeText(this, "API地址已复制", Toast.LENGTH_SHORT).show()
            addLog("INFO", "API地址已复制到剪贴板")
        }
        
        btnRefresh.setOnClickListener {
            // 刷新服务器状态
            val ipAddress = HttpServer.getLocalIpAddress()
            tvIpAddress.text = ipAddress
            tvApiUrl.text = "http://$ipAddress:8080/api/nal2/process"
            
            // 刷新 CrossOverFrequencies 全局变量
            val nal2Manager = com.nal2.Nal2Manager.getInstance(this)
            if (nal2Manager.hasCrossOverResult()) {
                addLog("INFO", "🔄 刷新 CrossOverFrequencies 全局变量...")
                val refreshResult = nal2Manager.refreshCrossOverFrequencies()
                if (refreshResult != null) {
                    // 更新全局变量
                    GlobalVariables.setCFArray(refreshResult.CFArray)
                    GlobalVariables.setFreqInCh(refreshResult.FreqInCh)
                    addLog("SUCCESS", "✅ CrossOverFrequencies 全局变量已刷新")
                    addLog("DEBUG", "  CFArray: ${refreshResult.CFArray.take(5).joinToString(", ")}${if (refreshResult.CFArray.size > 5) "..." else ""}")
                    addLog("DEBUG", "  FreqInCh: ${refreshResult.FreqInCh.take(5).joinToString(", ")}${if (refreshResult.FreqInCh.size > 5) "..." else ""}")
                    Toast.makeText(this, "✅ 已刷新（包含 CrossOverFrequencies）", Toast.LENGTH_SHORT).show()
                } else {
                    addLog("WARN", "⚠️ 刷新 CrossOverFrequencies 失败")
                    Toast.makeText(this, "已刷新服务器状态", Toast.LENGTH_SHORT).show()
                }
            } else {
                addLog("INFO", "服务器状态已刷新")
                Toast.makeText(this, "已刷新", Toast.LENGTH_SHORT).show()
            }
        }
        
        // 全屏查看日志
        btnFullScreenLogs.setOnClickListener {
            showFullScreenLogs()
        }
        
        // 下载日志
        btnDownloadLogs.setOnClickListener {
            if (logs.isEmpty()) {
                Toast.makeText(this, "没有日志可下载", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            downloadLogs()
        }
        
        // API 端点折叠/展开
        headerApiEndpoint.setOnClickListener {
            toggleSection(contentApiEndpoint, iconApiEndpoint, isApiEndpointExpanded)
            isApiEndpointExpanded = !isApiEndpointExpanded
        }
        
        // 最近请求折叠/展开
        headerLastRequest.setOnClickListener {
            toggleSection(tvLastRequest, iconLastRequest, isLastRequestExpanded)
            isLastRequestExpanded = !isLastRequestExpanded
        }
        
        // 最近响应折叠/展开
        headerLastResponse.setOnClickListener {
            toggleSection(tvLastResponse, iconLastResponse, isLastResponseExpanded)
            isLastResponseExpanded = !isLastResponseExpanded
        }
    }
    
    private fun toggleSection(content: View, icon: TextView, isExpanded: Boolean) {
        if (isExpanded) {
            // 折叠
            content.visibility = View.GONE
            icon.text = "▶"
        } else {
            // 展开
            content.visibility = View.VISIBLE
            icon.text = "▼"
        }
    }
    
    private fun showFullScreenLogs() {
        if (logs.isEmpty()) {
            Toast.makeText(this, "暂无日志", Toast.LENGTH_SHORT).show()
            return
        }
        
        val logsText = logs.joinToString("\n") { log ->
            "[${log.timestamp}] [${log.type}] ${log.message}"
        }
        
        val dialogView = layoutInflater.inflate(android.R.layout.simple_list_item_1, null)
        val textView = TextView(this).apply {
            text = logsText
            textSize = 11f
            setTextColor(ContextCompat.getColor(context, android.R.color.black))
            setTypeface(null, android.graphics.Typeface.NORMAL)
            typeface = android.graphics.Typeface.MONOSPACE
            setPadding(40, 40, 40, 40)
        }
        
        val scrollView = android.widget.ScrollView(this).apply {
            addView(textView)
        }
        
        AlertDialog.Builder(this)
            .setTitle("📋 全部日志 (${logs.size})")
            .setView(scrollView)
            .setPositiveButton("关闭", null)
            .setNeutralButton("复制全部") { _, _ ->
                val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                val clip = ClipData.newPlainText("Logs", logsText)
                clipboard.setPrimaryClip(clip)
                Toast.makeText(this, "日志已复制到剪贴板", Toast.LENGTH_SHORT).show()
            }
            .show()
    }
    
    private fun downloadLogs() {
        try {
            val timestamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(Date())
            val fileName = "NAL2_Logs_$timestamp.txt"
            
            val logsText = logs.joinToString("\n") { log ->
                "[${log.timestamp}] [${log.type}] ${log.message}"
            }
            
            // Android 10+ (API 29+) 使用 MediaStore API
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                val contentValues = ContentValues().apply {
                    put(MediaStore.MediaColumns.DISPLAY_NAME, fileName)
                    put(MediaStore.MediaColumns.MIME_TYPE, "text/plain")
                    put(MediaStore.MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS)
                }
                
                val resolver = contentResolver
                val uri: Uri? = resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, contentValues)
                
                if (uri != null) {
                    resolver.openOutputStream(uri)?.use { outputStream ->
                        outputStream.write(logsText.toByteArray())
                    }
                    Toast.makeText(this, "日志已保存到 Downloads/$fileName", Toast.LENGTH_LONG).show()
                    addLog("SUCCESS", "日志已下载到 Downloads: $fileName")
                } else {
                    throw Exception("无法创建文件")
                }
            } else {
                // Android 9 及以下需要权限
                if (ContextCompat.checkSelfPermission(this, Manifest.permission.WRITE_EXTERNAL_STORAGE)
                    != PackageManager.PERMISSION_GRANTED) {
                    ActivityCompat.requestPermissions(
                        this,
                        arrayOf(Manifest.permission.WRITE_EXTERNAL_STORAGE),
                        STORAGE_PERMISSION_CODE
                    )
                    return
                }
                
                val downloadsDir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS)
                if (!downloadsDir.exists()) {
                    downloadsDir.mkdirs()
                }
                val file = File(downloadsDir, fileName)
                file.writeText(logsText)
                
                Toast.makeText(this, "日志已保存到 Downloads/$fileName", Toast.LENGTH_LONG).show()
                addLog("SUCCESS", "日志已下载到 Downloads: $fileName")
            }
        } catch (e: Exception) {
            Toast.makeText(this, "下载失败: ${e.message}", Toast.LENGTH_LONG).show()
            addLog("ERROR", "日志下载失败: ${e.message}")
            e.printStackTrace()
        }
    }
    
    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == STORAGE_PERMISSION_CODE) {
            if (grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                downloadLogs()
            } else {
                Toast.makeText(this, "需要存储权限才能下载日志", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun addLog(type: String, message: String) {
        val timestamp = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())
            .format(Date())
        
        val logEntry = LogEntry(
            id = System.currentTimeMillis(),
            timestamp = timestamp,
            type = type,
            message = message
        )
        
        logAdapter.addLog(logEntry)
        updateLogsTitle()
        
        // 自动滚动到顶部
        if (logs.isNotEmpty()) {
            rvLogs.smoothScrollToPosition(0)
        }
        
        // 保存日志到文件
        saveLogsToFile()
    }
    
    private fun saveLogsToFile() {
        try {
            val logsText = logs.joinToString("\n") { log ->
                "${log.timestamp}|${log.type}|${log.message}"
            }
            val file = File(filesDir, "app_logs.txt")
            file.writeText(logsText)
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }
    
    private fun loadLogsFromFile() {
        try {
            val file = File(filesDir, "app_logs.txt")
            if (file.exists()) {
                val logsText = file.readText()
                if (logsText.isNotEmpty()) {
                    val loadedLogs = logsText.split("\n").mapNotNull { line ->
                        val parts = line.split("|")
                        if (parts.size == 3) {
                            LogEntry(
                                id = System.currentTimeMillis() + logs.size,
                                timestamp = parts[0],
                                type = parts[1],
                                message = parts[2]
                            )
                        } else null
                    }
                    logs.addAll(loadedLogs)
                    logAdapter.notifyDataSetChanged()
                    updateLogsTitle()
                    
                    // 检查是否有崩溃日志
                    checkForCrashLogs()
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }
    
    private fun checkForCrashLogs() {
        try {
            val crashFiles = filesDir.listFiles { file ->
                file.name.startsWith("crash_") && file.name.endsWith(".txt")
            }
            
            if (crashFiles != null && crashFiles.isNotEmpty()) {
                // 按修改时间排序，最新的在前
                val sortedCrashFiles = crashFiles.sortedByDescending { it.lastModified() }
                val latestCrashFile = sortedCrashFiles.first()
                
                // 显示崩溃提示
                runOnUiThread {
                    AlertDialog.Builder(this)
                        .setTitle("⚠️ 检测到应用崩溃")
                        .setMessage("检测到 ${crashFiles.size} 个崩溃日志文件。\n最新崩溃时间: ${SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault()).format(Date(latestCrashFile.lastModified()))}\n\n是否查看详细崩溃信息？")
                        .setPositiveButton("查看") { _, _ ->
                            showCrashLogDetails(latestCrashFile)
                        }
                        .setNegativeButton("稍后", null)
                        .setNeutralButton("清除崩溃日志") { _, _ ->
                            deleteCrashLogs()
                        }
                        .show()
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }
    
    private fun showCrashLogDetails(crashFile: File) {
        try {
            val crashContent = crashFile.readText()
            
            val textView = TextView(this).apply {
                text = crashContent
                textSize = 10f
                setTextColor(ContextCompat.getColor(context, android.R.color.black))
                typeface = android.graphics.Typeface.MONOSPACE
                setPadding(40, 40, 40, 40)
            }
            
            val scrollView = android.widget.ScrollView(this).apply {
                addView(textView)
            }
            
            AlertDialog.Builder(this)
                .setTitle("💥 崩溃详情")
                .setView(scrollView)
                .setPositiveButton("关闭", null)
                .setNeutralButton("复制") { _, _ ->
                    val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                    val clip = ClipData.newPlainText("Crash Log", crashContent)
                    clipboard.setPrimaryClip(clip)
                    Toast.makeText(this, "崩溃日志已复制到剪贴板", Toast.LENGTH_SHORT).show()
                }
                .setNegativeButton("删除此日志") { _, _ ->
                    crashFile.delete()
                    Toast.makeText(this, "崩溃日志已删除", Toast.LENGTH_SHORT).show()
                }
                .show()
        } catch (e: Exception) {
            Toast.makeText(this, "读取崩溃日志失败: ${e.message}", Toast.LENGTH_SHORT).show()
        }
    }
    
    private fun deleteCrashLogs() {
        try {
            val crashFiles = filesDir.listFiles { file ->
                file.name.startsWith("crash_") && file.name.endsWith(".txt")
            }
            
            var deletedCount = 0
            crashFiles?.forEach { file ->
                if (file.delete()) {
                    deletedCount++
                }
            }
            
            Toast.makeText(this, "已删除 $deletedCount 个崩溃日志", Toast.LENGTH_SHORT).show()
        } catch (e: Exception) {
            Toast.makeText(this, "删除崩溃日志失败: ${e.message}", Toast.LENGTH_SHORT).show()
        }
    }

    private fun updateLogsTitle() {
        tvLogsTitle.text = "📋 应用日志 (${logs.size})"
    }

    private fun formatJson(jsonString: String): String {
        return try {
            val jsonObject = gson.fromJson(jsonString, Any::class.java)
            gson.toJson(jsonObject)
        } catch (e: Exception) {
            jsonString
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        try {
            httpServer.stop()
            addLog("INFO", "服务器已停止")
        } catch (e: Exception) {
            // Ignore
        }
    }
}
