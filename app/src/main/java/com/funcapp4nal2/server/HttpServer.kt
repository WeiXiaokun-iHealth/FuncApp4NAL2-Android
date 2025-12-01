package com.funcapp4nal2.server

import android.content.Context
import android.util.Log
import com.funcapp4nal2.nal2.Nal2Manager
import com.google.gson.Gson
import com.google.gson.JsonObject
import fi.iki.elonen.NanoHTTPD
import java.net.NetworkInterface

class HttpServer(private val context: Context, port: Int = 8080) : NanoHTTPD(port) {
    
    private val gson = Gson()
    private val nal2Manager = Nal2Manager.getInstance(context)
    
    var onRequestReceived: ((String) -> Unit)? = null
    var onResponseSent: ((String) -> Unit)? = null
    var onLog: ((String, String) -> Unit)? = null
    
    companion object {
        private const val TAG = "HttpServer"
        
        fun getLocalIpAddress(): String {
            try {
                val interfaces = NetworkInterface.getNetworkInterfaces()
                while (interfaces.hasMoreElements()) {
                    val networkInterface = interfaces.nextElement()
                    val addresses = networkInterface.inetAddresses
                    while (addresses.hasMoreElements()) {
                        val address = addresses.nextElement()
                        if (!address.isLoopbackAddress && address.hostAddress?.contains(':') == false) {
                            return address.hostAddress ?: "未知"
                        }
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "获取IP地址失败", e)
            }
            return "未知"
        }
    }
    
    override fun serve(session: IHTTPSession): Response {
        val uri = session.uri
        val method = session.method
        
        Log.d(TAG, "收到请求: $method $uri")
        onLog?.invoke("INFO", "收到请求: $method $uri")
        
        return when {
            uri == "/api/nal2/process" && method == Method.POST -> handleNal2Request(session)
            uri == "/health" -> newFixedLengthResponse(Response.Status.OK, "text/plain", "OK")
            else -> newFixedLengthResponse(Response.Status.NOT_FOUND, "text/plain", "Not Found")
        }
    }
    
    private fun handleNal2Request(session: IHTTPSession): Response {
        return try {
            // 读取请求体
            val files = HashMap<String, String>()
            session.parseBody(files)
            val requestBody = files["postData"] ?: ""
            
            Log.d(TAG, "请求体: $requestBody")
            onRequestReceived?.invoke(requestBody)
            onLog?.invoke("INFO", "1️⃣ HTTP收到: $requestBody")
            
            // 解析 JSON
            val requestJson = gson.fromJson(requestBody, JsonObject::class.java)
            val sequenceNum = requestJson.get("sequence_num")?.asInt ?: 0
            val functionName = requestJson.get("function")?.asString ?: ""
            val inputParams = requestJson.getAsJsonObject("input_parameters")
            
            onLog?.invoke("INFO", "2️⃣ NAL2输入: function=$functionName")
            
            // 调用 NAL2 函数
            val result = processNal2Function(functionName, inputParams)
            
            // 构建响应
            val response = JsonObject().apply {
                addProperty("sequence_num", sequenceNum)
                addProperty("function", functionName)
                addProperty("return", if (result.has("error")) -1 else 0)
                add("output_parameters", result)
            }
            
            val responseBody = gson.toJson(response)
            Log.d(TAG, "响应体: $responseBody")
            onResponseSent?.invoke(responseBody)
            onLog?.invoke("SUCCESS", "4️⃣ HTTP返回: $responseBody")
            
            newFixedLengthResponse(
                Response.Status.OK,
                "application/json",
                responseBody
            )
            
        } catch (e: Exception) {
            Log.e(TAG, "处理请求失败", e)
            onLog?.invoke("ERROR", "处理失败: ${e.message}")
            
            val errorResponse = JsonObject().apply {
                addProperty("return", -1)
                add("output_parameters", JsonObject().apply {
                    addProperty("error", e.message ?: "未知错误")
                })
            }
            
            newFixedLengthResponse(
                Response.Status.INTERNAL_ERROR,
                "application/json",
                gson.toJson(errorResponse)
            )
        }
    }
    
    private fun processNal2Function(functionName: String, params: JsonObject?): JsonObject {
        val result = JsonObject()
        
        try {
            when (functionName) {
                "dllVersion" -> {
                    val version = nal2Manager.getDllVersion()
                    result.addProperty("major", version[0])
                    result.addProperty("minor", version[1])
                    onLog?.invoke("SUCCESS", "3️⃣ NAL2输出: version=${version[0]}.${version[1]}")
                }
                
                // 其他函数将在后续实现
                else -> {
                    result.addProperty("error", "未实现的函数: $functionName")
                    onLog?.invoke("ERROR", "未实现的函数: $functionName")
                }
            }
        } catch (e: Exception) {
            result.addProperty("error", e.message ?: "处理失败")
            onLog?.invoke("ERROR", "NAL2处理失败: ${e.message}")
        }
        
        return result
    }
}
