package com.funcapp4nal2

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.funcapp4nal2.server.HttpServer
import com.google.gson.GsonBuilder
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
    private lateinit var btnCopyApi: Button
    private lateinit var btnRefresh: Button
    
    private val gson = GsonBuilder().setPrettyPrinting().create()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        initViews()
        setupRecyclerView()
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
        btnCopyApi = findViewById(R.id.btnCopyApi)
        btnRefresh = findViewById(R.id.btnRefresh)
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
        }
    }

    private fun setupListeners() {
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
            val ipAddress = HttpServer.getLocalIpAddress()
            tvIpAddress.text = ipAddress
            tvApiUrl.text = "http://$ipAddress:8080/api/nal2/process"
            addLog("INFO", "服务器状态已刷新")
            Toast.makeText(this, "已刷新", Toast.LENGTH_SHORT).show()
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
