package com.funcapp4nal2.server

import android.content.Context
import android.util.Log
import com.funcapp4nal2.nal2.Nal2Manager
import com.funcapp4nal2.utils.GlobalVariables
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
                val wifiAddresses = mutableListOf<String>()
                val otherAddresses = mutableListOf<String>()
                
                while (interfaces.hasMoreElements()) {
                    val networkInterface = interfaces.nextElement()
                    val interfaceName = networkInterface.name.lowercase()
                    val addresses = networkInterface.inetAddresses
                    
                    while (addresses.hasMoreElements()) {
                        val address = addresses.nextElement()
                        // 只处理 IPv4 地址，排除回环地址
                        if (!address.isLoopbackAddress && address.hostAddress?.contains(':') == false) {
                            val ipAddress = address.hostAddress ?: continue
                            
                            // 优先选择 WiFi 接口的地址
                            if (interfaceName.contains("wlan") || interfaceName.contains("wifi")) {
                                wifiAddresses.add(ipAddress)
                            } else {
                                otherAddresses.add(ipAddress)
                            }
                        }
                    }
                }
                
                // 优先返回 WiFi 地址
                if (wifiAddresses.isNotEmpty()) {
                    return wifiAddresses.first()
                }
                
                // 其次返回其他网络接口地址
                if (otherAddresses.isNotEmpty()) {
                    return otherAddresses.first()
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
        
        // 处理 CORS 预检请求
        if (method == Method.OPTIONS) {
            return newFixedLengthResponse(Response.Status.OK, "text/plain", "OK").apply {
                addHeader("Access-Control-Allow-Origin", "*")
                addHeader("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
                addHeader("Access-Control-Allow-Headers", "Content-Type, Authorization")
                addHeader("Access-Control-Max-Age", "86400")
            }
        }
        
        return when {
            uri == "/api/nal2/process" && method == Method.POST -> handleNal2Request(session)
            uri == "/health" -> {
                val ipAddress = getLocalIpAddress()
                val healthResponse = JsonObject().apply {
                    addProperty("status", "ok")
                    addProperty("message", "Server is running")
                    addProperty("server", ipAddress)
                    addProperty("port", 8080)
                    addProperty("apiEndpoint", "http://$ipAddress:8080/api/nal2/process")
                }
                newFixedLengthResponse(Response.Status.OK, "application/json", gson.toJson(healthResponse)).apply {
                    addHeader("Access-Control-Allow-Origin", "*")
                    addHeader("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
                    addHeader("Access-Control-Allow-Headers", "Content-Type, Authorization")
                }
            }
            else -> newFixedLengthResponse(Response.Status.NOT_FOUND, "text/plain", "Not Found").apply {
                addHeader("Access-Control-Allow-Origin", "*")
            }
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
            ).apply {
                addHeader("Access-Control-Allow-Origin", "*")
                addHeader("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
                addHeader("Access-Control-Allow-Headers", "Content-Type, Authorization")
            }
            
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
            ).apply {
                addHeader("Access-Control-Allow-Origin", "*")
                addHeader("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
                addHeader("Access-Control-Allow-Headers", "Content-Type, Authorization")
            }
        }
    }
    
    private fun processNal2Function(functionName: String, params: JsonObject?): JsonObject {
        val result = JsonObject()
        
        if (params == null) {
            result.addProperty("error", "缺少输入参数")
            return result
        }
        
        try {
            when (functionName) {
                "dllVersion" -> {
                    val version = nal2Manager.getDllVersion()
                    result.addProperty("major", version[0])
                    result.addProperty("minor", version[1])
                    onLog?.invoke("SUCCESS", "3️⃣ NAL2输出: version=${version[0]}.${version[1]}")
                }
                
                "CrossOverFrequencies_NL2" -> {
                    val channels = params.get("channels").asInt
                    val ac = jsonArrayToDoubleArray(params.getAsJsonArray("AC"))
                    val bc = jsonArrayToDoubleArray(params.getAsJsonArray("BC"))
                    
                    val cfArr = DoubleArray(19)
                    val freqInCh = IntArray(19)
                    val crossResult = nal2Manager.getCrossOverFrequencies(cfArr, channels, ac, bc, freqInCh)
                    
                    // 自动保存到全局变量
                    GlobalVariables.setCFArray(crossResult.CFArray)
                    GlobalVariables.setFreqInCh(crossResult.FreqInCh)
                    
                    result.add("CFArray", doubleArrayToJsonArray(crossResult.CFArray))
                    result.add("FreqInCh", intArrayToJsonArray(crossResult.FreqInCh))
                    onLog?.invoke("SUCCESS", "3️⃣ NAL2输出: CrossOverFrequencies完成 (已保存到全局变量)")
                }
                
                "CenterFrequencies" -> {
                    val channels = params.get("channels").asInt
                    val cfArray = if (params.has("CFArray")) {
                        jsonArrayToDoubleArray(params.getAsJsonArray("CFArray"))
                    } else {
                        DoubleArray(0)
                    }
                    val centreF = nal2Manager.getCenterFrequencies(channels, cfArray)
                    result.add("centreF", intArrayToJsonArray(centreF))
                    onLog?.invoke("SUCCESS", "3️⃣ NAL2输出: CenterFrequencies完成")
                }
                
                "CompressionThreshold_NL2" -> {
                    val ct = DoubleArray(19)
                    val bandwidth = params.get("bandWidth")?.asInt ?: params.get("bandwidth")?.asInt ?: 0
                    val selection = params.get("selection")?.asInt ?: 0
                    val calcCh = jsonArrayToIntArray(params.getAsJsonArray("calcCh"))
                    
                    nal2Manager.setCompressionThreshold(
                        ct,
                        bandwidth,
                        selection,
                        params.get("WBCT")?.asInt ?: 0,
                        params.get("aidType")?.asInt ?: 0,
                        params.get("direction")?.asInt ?: 0,
                        params.get("mic")?.asInt ?: 0,
                        calcCh
                    )
                    
                    // 自动保存到全局变量
                    GlobalVariables.setCT(ct)
                    
                    result.add("CT", doubleArrayToJsonArray(ct))
                    onLog?.invoke("SUCCESS", "3️⃣ NAL2输出: CompressionThreshold完成 (已保存到全局变量)")
                }
                
                "setBWC" -> {
                    val channels = params.get("channels").asInt
                    val crossOver = jsonArrayToDoubleArray(params.getAsJsonArray("crossOver"))
                    nal2Manager.setBWC(channels, crossOver)
                    result.addProperty("success", true)
                }
                
                "SetAdultChild" -> {
                    nal2Manager.setAdultChild(params.get("adultChild").asInt, params.get("dateOfBirth").asInt)
                    result.addProperty("success", true)
                }
                
                "SetExperience" -> {
                    nal2Manager.setExperience(params.get("experience").asInt)
                    result.addProperty("success", true)
                }
                
                "SetCompSpeed" -> {
                    nal2Manager.setCompSpeed(params.get("compSpeed").asInt)
                    result.addProperty("success", true)
                }
                
                "SetTonalLanguage" -> {
                    nal2Manager.setTonalLanguage(params.get("tonal").asInt)
                    result.addProperty("success", true)
                }
                
                "SetGender" -> {
                    nal2Manager.setGender(params.get("gender").asInt)
                    result.addProperty("success", true)
                }
                
                "CompressionRatio_NL2" -> {
                    val cr = DoubleArray(19)
                    val channels = params.get("channels").asInt
                    val centreFreq = jsonArrayToIntArray(params.getAsJsonArray("centreFreq"))
                    val ac = jsonArrayToDoubleArray(params.getAsJsonArray("AC"))
                    val bc = jsonArrayToDoubleArray(params.getAsJsonArray("BC"))
                    val acOther = jsonArrayToDoubleArray(params.getAsJsonArray("ACother"))
                    
                    val crResult = nal2Manager.getCompressionRatio(
                        cr,
                        channels,
                        centreFreq,
                        ac,
                        bc,
                        params.get("direction").asInt,
                        params.get("mic").asInt,
                        params.get("limiting").asInt,
                        acOther,
                        params.get("noOfAids").asInt
                    )
                    result.add("CR", doubleArrayToJsonArray(crResult))
                    onLog?.invoke("SUCCESS", "3️⃣ NAL2输出: CompressionRatio完成")
                }
                
                "getMPO_NL2" -> {
                    val mpo = DoubleArray(19)
                    val ac = jsonArrayToDoubleArray(params.getAsJsonArray("AC"))
                    val bc = jsonArrayToDoubleArray(params.getAsJsonArray("BC"))
                    
                    val mpoResult = nal2Manager.getMPO(
                        mpo,
                        params.get("type").asInt,
                        ac,
                        bc,
                        params.get("channels").asInt,
                        params.get("limiting").asInt
                    )
                    result.add("MPO", doubleArrayToJsonArray(mpoResult))
                    onLog?.invoke("SUCCESS", "3️⃣ NAL2输出: getMPO完成")
                }
                
                "RealEarInsertionGain_NL2" -> {
                    val reig = DoubleArray(19)
                    val ac = jsonArrayToDoubleArray(params.getAsJsonArray("AC"))
                    val bc = jsonArrayToDoubleArray(params.getAsJsonArray("BC"))
                    val acOther = jsonArrayToDoubleArray(params.getAsJsonArray("ACother"))
                    
                    val reigResult = nal2Manager.getRealEarInsertionGain(
                        reig,
                        ac,
                        bc,
                        params.get("L").asDouble,
                        params.get("limiting").asInt,
                        params.get("channels").asInt,
                        params.get("direction").asInt,
                        params.get("mic").asInt,
                        acOther,
                        params.get("noOfAids").asInt
                    )
                    result.add("REIG", doubleArrayToJsonArray(reigResult))
                    onLog?.invoke("SUCCESS", "3️⃣ NAL2输出: RealEarInsertionGain完成")
                }
                
                "RealEarAidedGain_NL2" -> {
                    val data = DoubleArray(19)
                    val ac = jsonArrayToDoubleArray(params.getAsJsonArray("AC"))
                    val bc = jsonArrayToDoubleArray(params.getAsJsonArray("BC"))
                    
                    val reagResult = nal2Manager.getRealEarAidedGain(
                        data,
                        ac,
                        bc,
                        params.get("L").asDouble,
                        params.get("limiting").asInt,
                        params.get("channels").asInt,
                        params.get("direction").asInt,
                        params.get("mic").asInt,
                        params.get("noOfAids").asInt
                    )
                    result.add("REAG", doubleArrayToJsonArray(reagResult))
                    onLog?.invoke("SUCCESS", "3️⃣ NAL2输出: RealEarAidedGain完成")
                }
                
                "TccCouplerGain_NL2" -> {
                    val gain = DoubleArray(19)
                    val lineType = IntArray(19)
                    val ac = jsonArrayToDoubleArray(params.getAsJsonArray("AC"))
                    val bc = jsonArrayToDoubleArray(params.getAsJsonArray("BC"))
                    val acOther = jsonArrayToDoubleArray(params.getAsJsonArray("ACother"))
                    
                    val tccResult = nal2Manager.getTccCouplerGain(
                        gain,
                        ac,
                        bc,
                        params.get("L").asDouble,
                        params.get("limiting").asInt,
                        params.get("channels").asInt,
                        params.get("direction").asInt,
                        params.get("mic").asInt,
                        params.get("target").asInt,
                        params.get("aidType").asInt,
                        acOther,
                        params.get("noOfAids").asInt,
                        params.get("tubing").asInt,
                        params.get("vent").asInt,
                        params.get("RECDmeasType").asInt,
                        lineType
                    )
                    result.add("TccGain", doubleArrayToJsonArray(tccResult.TccGain))
                    result.add("lineType", intArrayToJsonArray(tccResult.lineType))
                    onLog?.invoke("SUCCESS", "3️⃣ NAL2输出: TccCouplerGain完成")
                }
                
                "EarSimulatorGain_NL2" -> {
                    val gain = DoubleArray(19)
                    val lineType = IntArray(19)
                    val ac = jsonArrayToDoubleArray(params.getAsJsonArray("AC"))
                    val bc = jsonArrayToDoubleArray(params.getAsJsonArray("BC"))
                    val acOther = jsonArrayToDoubleArray(params.getAsJsonArray("ACother"))
                    
                    val esgResult = nal2Manager.getEarSimulatorGain(
                        gain,
                        ac,
                        bc,
                        params.get("L").asDouble,
                        params.get("direction").asInt,
                        params.get("mic").asInt,
                        params.get("limiting").asInt,
                        params.get("channels").asInt,
                        params.get("target").asInt,
                        params.get("aidType").asInt,
                        acOther,
                        params.get("noOfAids").asInt,
                        params.get("tubing").asInt,
                        params.get("vent").asInt,
                        params.get("RECDmeasType").asInt,
                        lineType
                    )
                    result.add("ESG", doubleArrayToJsonArray(esgResult.ESG))
                    result.add("lineType", intArrayToJsonArray(esgResult.lineType))
                    onLog?.invoke("SUCCESS", "3️⃣ NAL2输出: EarSimulatorGain完成")
                }
                
                // RECD 相关函数
                "GetRECDh_indiv_NL2" -> {
                    val recdh = nal2Manager.getRECDhIndiv(
                        params.get("RECDmeasType").asInt,
                        params.get("dateOfBirth").asInt,
                        params.get("aidType").asInt,
                        params.get("tubing").asInt,
                        params.get("coupler").asInt,
                        params.get("fittingDepth").asInt
                    )
                    result.add("RECDh", doubleArrayToJsonArray(recdh))
                    onLog?.invoke("SUCCESS", "3️⃣ NAL2输出: GetRECDh_indiv完成")
                }
                
                "GetRECDh_indiv9_NL2" -> {
                    val recdh = nal2Manager.getRECDhIndiv9(
                        params.get("RECDmeasType").asInt,
                        params.get("dateOfBirth").asInt,
                        params.get("aidType").asInt,
                        params.get("tubing").asInt,
                        params.get("coupler").asInt,
                        params.get("fittingDepth").asInt
                    )
                    result.add("RECDh", doubleArrayToJsonArray(recdh))
                    onLog?.invoke("SUCCESS", "3️⃣ NAL2输出: GetRECDh_indiv9完成")
                }
                
                "GetRECDt_indiv_NL2" -> {
                    val recdt = nal2Manager.getRECDtIndiv(
                        params.get("RECDmeasType").asInt,
                        params.get("dateOfBirth").asInt,
                        params.get("aidType").asInt,
                        params.get("tubing").asInt,
                        params.get("vent").asInt,
                        params.get("earpiece").asInt,
                        params.get("coupler").asInt,
                        params.get("fittingDepth").asInt
                    )
                    result.add("RECDt", doubleArrayToJsonArray(recdt))
                    onLog?.invoke("SUCCESS", "3️⃣ NAL2输出: GetRECDt_indiv完成")
                }
                
                "GetRECDt_indiv9_NL2" -> {
                    val recdt = nal2Manager.getRECDtIndiv9(
                        params.get("RECDmeasType").asInt,
                        params.get("dateOfBirth").asInt,
                        params.get("aidType").asInt,
                        params.get("tubing").asInt,
                        params.get("vent").asInt,
                        params.get("earpiece").asInt,
                        params.get("coupler").asInt,
                        params.get("fittingDepth").asInt
                    )
                    result.add("RECDt", doubleArrayToJsonArray(recdt))
                    onLog?.invoke("SUCCESS", "3️⃣ NAL2输出: GetRECDt_indiv9完成")
                }
                
                "SetRECDh_indiv_NL2" -> {
                    nal2Manager.setRECDhIndiv(jsonArrayToDoubleArray(params.getAsJsonArray("RECDh")))
                    result.addProperty("success", true)
                }
                
                "SetRECDh_indiv9_NL2" -> {
                    nal2Manager.setRECDhIndiv9(jsonArrayToDoubleArray(params.getAsJsonArray("RECDh")))
                    result.addProperty("success", true)
                }
                
                "SetRECDt_indiv_NL2" -> {
                    nal2Manager.setRECDtIndiv(jsonArrayToDoubleArray(params.getAsJsonArray("RECDt")))
                    result.addProperty("success", true)
                }
                
                "SetRECDt_indiv9_NL2" -> {
                    nal2Manager.setRECDtIndiv9(jsonArrayToDoubleArray(params.getAsJsonArray("RECDt")))
                    result.addProperty("success", true)
                }
                
                // IO 曲线相关函数
                "RealEarInputOutputCurve_NL2" -> {
                    val ac = jsonArrayToDoubleArray(params.getAsJsonArray("AC"))
                    val bc = jsonArrayToDoubleArray(params.getAsJsonArray("BC"))
                    val acOther = jsonArrayToDoubleArray(params.getAsJsonArray("ACother"))
                    
                    val ioResult = nal2Manager.getRealEarInputOutputCurve(
                        ac,
                        bc,
                        params.get("graphFreq").asInt,
                        params.get("startLevel").asInt,
                        params.get("finishLevel").asInt,
                        params.get("limiting").asInt,
                        params.get("channels").asInt,
                        params.get("direction").asInt,
                        params.get("mic").asInt,
                        params.get("target").asInt,
                        acOther,
                        params.get("noOfAids").asInt
                    )
                    result.add("REIO", doubleArrayToJsonArray(ioResult.IO))
                    result.add("REIOunl", doubleArrayToJsonArray(ioResult.IOunl))
                    onLog?.invoke("SUCCESS", "3️⃣ NAL2输出: RealEarInputOutputCurve完成")
                }
                
                "TccInputOutputCurve_NL2" -> {
                    val ac = jsonArrayToDoubleArray(params.getAsJsonArray("AC"))
                    val bc = jsonArrayToDoubleArray(params.getAsJsonArray("BC"))
                    val acOther = jsonArrayToDoubleArray(params.getAsJsonArray("ACother"))
                    
                    val tccIOResult = nal2Manager.getTccInputOutputCurve(
                        ac,
                        bc,
                        params.get("graphFreq").asInt,
                        params.get("startLevel").asInt,
                        params.get("finishLevel").asInt,
                        params.get("limiting").asInt,
                        params.get("channels").asInt,
                        params.get("direction").asInt,
                        params.get("mic").asInt,
                        params.get("target").asInt,
                        params.get("aidType").asInt,
                        acOther,
                        params.get("noOfAids").asInt,
                        params.get("tubing").asInt,
                        params.get("vent").asInt,
                        params.get("RECDmeasType").asInt
                    )
                    result.add("TccIO", doubleArrayToJsonArray(tccIOResult.TccIO))
                    result.add("TccIOunl", doubleArrayToJsonArray(tccIOResult.TccIOunl))
                    result.add("lineType", intArrayToJsonArray(tccIOResult.lineType))
                    onLog?.invoke("SUCCESS", "3️⃣ NAL2输出: TccInputOutputCurve完成")
                }
                
                "EarSimulatorInputOutputCurve_NL2" -> {
                    val ac = jsonArrayToDoubleArray(params.getAsJsonArray("AC"))
                    val bc = jsonArrayToDoubleArray(params.getAsJsonArray("BC"))
                    val acOther = jsonArrayToDoubleArray(params.getAsJsonArray("ACother"))
                    
                    val esIOResult = nal2Manager.getEarSimulatorInputOutputCurve(
                        ac,
                        bc,
                        params.get("graphFreq").asInt,
                        params.get("startLevel").asInt,
                        params.get("finishLevel").asInt,
                        params.get("limiting").asInt,
                        params.get("channels").asInt,
                        params.get("direction").asInt,
                        params.get("mic").asInt,
                        params.get("target").asInt,
                        params.get("aidType").asInt,
                        acOther,
                        params.get("noOfAids").asInt,
                        params.get("tubing").asInt,
                        params.get("vent").asInt,
                        params.get("RECDmeasType").asInt
                    )
                    result.add("ESIO", doubleArrayToJsonArray(esIOResult.ESIO))
                    result.add("ESIOunl", doubleArrayToJsonArray(esIOResult.ESIOunl))
                    result.add("lineType", intArrayToJsonArray(esIOResult.lineType))
                    onLog?.invoke("SUCCESS", "3️⃣ NAL2输出: EarSimulatorInputOutputCurve完成")
                }
                
                "Speech_o_Gram_NL2" -> {
                    val ac = jsonArrayToDoubleArray(params.getAsJsonArray("AC"))
                    val bc = jsonArrayToDoubleArray(params.getAsJsonArray("BC"))
                    val acOther = jsonArrayToDoubleArray(params.getAsJsonArray("ACother"))
                    
                    val speechResult = nal2Manager.getSpeechOGram(
                        ac,
                        bc,
                        params.get("L").asDouble,
                        params.get("limiting").asInt,
                        params.get("channels").asInt,
                        params.get("direction").asInt,
                        params.get("mic").asInt,
                        acOther,
                        params.get("noOfAids").asInt
                    )
                    result.add("Speech_rms", doubleArrayToJsonArray(speechResult.Speech_rms))
                    result.add("Speech_max", doubleArrayToJsonArray(speechResult.Speech_max))
                    result.add("Speech_min", doubleArrayToJsonArray(speechResult.Speech_min))
                    result.add("Speech_thresh", doubleArrayToJsonArray(speechResult.Speech_thresh))
                    onLog?.invoke("SUCCESS", "3️⃣ NAL2输出: Speech_o_Gram完成")
                }
                
                "AidedThreshold_NL2" -> {
                    val ac = jsonArrayToDoubleArray(params.getAsJsonArray("AC"))
                    val bc = jsonArrayToDoubleArray(params.getAsJsonArray("BC"))
                    val ct = jsonArrayToDoubleArray(params.getAsJsonArray("CT"))
                    val acOther = jsonArrayToDoubleArray(params.getAsJsonArray("ACother"))
                    
                    val at = nal2Manager.getAidedThreshold(
                        ac,
                        bc,
                        ct,
                        params.get("dbOption").asInt,
                        acOther,
                        params.get("noOfAids").asInt,
                        params.get("limiting").asInt,
                        params.get("channels").asInt,
                        params.get("direction").asInt,
                        params.get("mic").asInt
                    )
                    result.add("AT", doubleArrayToJsonArray(at))
                    onLog?.invoke("SUCCESS", "3️⃣ NAL2输出: AidedThreshold完成")
                }
                
                // REDD/REUR 相关函数
                "GetREDDindiv" -> {
                    val redd = nal2Manager.getREDDindiv(params.get("defValues").asInt)
                    result.add("REDD", doubleArrayToJsonArray(redd))
                    onLog?.invoke("SUCCESS", "3️⃣ NAL2输出: GetREDDindiv完成")
                }
                
                "GetREDDindiv9" -> {
                    val redd = nal2Manager.getREDDindiv9(params.get("defValues").asInt)
                    result.add("REDD", doubleArrayToJsonArray(redd))
                    onLog?.invoke("SUCCESS", "3️⃣ NAL2输出: GetREDDindiv9完成")
                }
                
                "GetREURindiv" -> {
                    val reur = nal2Manager.getREURindiv(
                        params.get("defValues").asInt,
                        params.get("dateOfBirth").asInt,
                        params.get("direction").asInt,
                        params.get("mic").asInt
                    )
                    result.add("REUR", doubleArrayToJsonArray(reur))
                    onLog?.invoke("SUCCESS", "3️⃣ NAL2输出: GetREURindiv完成")
                }
                
                "GetREURindiv9" -> {
                    val reur = nal2Manager.getREURindiv9(
                        params.get("defValues").asInt,
                        params.get("dateOfBirth").asInt,
                        params.get("direction").asInt,
                        params.get("mic").asInt
                    )
                    result.add("REUR", doubleArrayToJsonArray(reur))
                    onLog?.invoke("SUCCESS", "3️⃣ NAL2输出: GetREURindiv9完成")
                }
                
                "SetREDDindiv" -> {
                    nal2Manager.setREDDindiv(
                        jsonArrayToDoubleArray(params.getAsJsonArray("REDD")),
                        params.get("defValues").asInt
                    )
                    result.addProperty("success", true)
                }
                
                "SetREDDindiv9" -> {
                    nal2Manager.setREDDindiv9(
                        jsonArrayToDoubleArray(params.getAsJsonArray("REDD")),
                        params.get("defValues").asInt
                    )
                    result.addProperty("success", true)
                }
                
                "SetREURindiv" -> {
                    nal2Manager.setREURindiv(
                        jsonArrayToDoubleArray(params.getAsJsonArray("REUR")),
                        params.get("defValues").asInt,
                        params.get("dateOfBirth").asInt,
                        params.get("direction").asInt,
                        params.get("mic").asInt
                    )
                    result.addProperty("success", true)
                }
                
                "SetREURindiv9" -> {
                    nal2Manager.setREURindiv9(
                        jsonArrayToDoubleArray(params.getAsJsonArray("REUR")),
                        params.get("defValues").asInt,
                        params.get("dateOfBirth").asInt,
                        params.get("direction").asInt,
                        params.get("mic").asInt
                    )
                    result.addProperty("success", true)
                }
                
                // 其他高级函数
                "GainAt_NL2" -> {
                    val ac = jsonArrayToDoubleArray(params.getAsJsonArray("AC"))
                    val bc = jsonArrayToDoubleArray(params.getAsJsonArray("BC"))
                    val acOther = jsonArrayToDoubleArray(params.getAsJsonArray("ACother"))
                    
                    val gain = nal2Manager.getGainAt(
                        params.get("freqRequired").asInt,
                        params.get("targetType").asInt,
                        ac,
                        bc,
                        params.get("L").asDouble,
                        params.get("limiting").asInt,
                        params.get("channels").asInt,
                        params.get("direction").asInt,
                        params.get("mic").asInt,
                        acOther,
                        params.get("noOfAids").asInt,
                        params.get("bandWidth").asInt,
                        params.get("target").asInt,
                        params.get("aidType").asInt,
                        params.get("tubing").asInt,
                        params.get("vent").asInt,
                        params.get("RECDmeasType").asInt
                    )
                    result.addProperty("Gain", gain)
                    onLog?.invoke("SUCCESS", "3️⃣ NAL2输出: GainAt完成")
                }
                
                "GetMLE" -> {
                    val mle = nal2Manager.getMLE(
                        params.get("aidType").asInt,
                        params.get("direction").asInt,
                        params.get("mic").asInt
                    )
                    result.add("MLE", doubleArrayToJsonArray(mle))
                    onLog?.invoke("SUCCESS", "3️⃣ NAL2输出: GetMLE完成")
                }
                
                "ReturnValues_NL2" -> {
                    val returnValues = nal2Manager.getReturnValues()
                    result.add("MAF", doubleArrayToJsonArray(returnValues.MAF))
                    result.add("BWC", doubleArrayToJsonArray(returnValues.BWC))
                    result.add("ESCD", doubleArrayToJsonArray(returnValues.ESCD))
                    onLog?.invoke("SUCCESS", "3️⃣ NAL2输出: ReturnValues完成")
                }
                
                "GetTubing_NL2" -> {
                    val tubing = nal2Manager.getTubing(params.get("tubing").asInt)
                    result.add("Tubing", doubleArrayToJsonArray(tubing))
                    onLog?.invoke("SUCCESS", "3️⃣ NAL2输出: GetTubing完成")
                }
                
                "GetTubing9_NL2" -> {
                    val tubing = nal2Manager.getTubing9(params.get("tubing").asInt)
                    result.add("Tubing", doubleArrayToJsonArray(tubing))
                    onLog?.invoke("SUCCESS", "3️⃣ NAL2输出: GetTubing9完成")
                }
                
                "GetVentOut_NL2" -> {
                    val ventOut = nal2Manager.getVentOut(params.get("vent").asInt)
                    result.add("VentOut", doubleArrayToJsonArray(ventOut))
                    onLog?.invoke("SUCCESS", "3️⃣ NAL2输出: GetVentOut完成")
                }
                
                "GetVentOut9_NL2" -> {
                    val ventOut = nal2Manager.getVentOut9(params.get("vent").asInt)
                    result.add("VentOut", doubleArrayToJsonArray(ventOut))
                    onLog?.invoke("SUCCESS", "3️⃣ NAL2输出: GetVentOut9完成")
                }
                
                "Get_SI_NL2" -> {
                    val reag = jsonArrayToDoubleArray(params.getAsJsonArray("REAG"))
                    val limit = jsonArrayToDoubleArray(params.getAsJsonArray("Limit"))
                    val si = nal2Manager.getSI(params.get("s").asInt, reag, limit)
                    result.addProperty("SI", si)
                    onLog?.invoke("SUCCESS", "3️⃣ NAL2输出: Get_SI完成")
                }
                
                "Get_SII" -> {
                    val speechThresh = jsonArrayToDoubleArray(params.getAsJsonArray("Speech_thresh"))
                    val reag = jsonArrayToDoubleArray(params.getAsJsonArray("REAG"))
                    val reagp = jsonArrayToDoubleArray(params.getAsJsonArray("REAGp"))
                    val reagm = jsonArrayToDoubleArray(params.getAsJsonArray("REAGm"))
                    val reur = jsonArrayToDoubleArray(params.getAsJsonArray("REUR"))
                    
                    val sii = nal2Manager.getSII(
                        params.get("nCompSpeed").asInt,
                        speechThresh,
                        params.get("s").asInt,
                        reag,
                        reagp,
                        reagm,
                        reur
                    )
                    result.addProperty("SII", sii)
                    onLog?.invoke("SUCCESS", "3️⃣ NAL2输出: Get_SII完成")
                }
                
                else -> {
                    result.addProperty("error", "未实现的函数: $functionName")
                    onLog?.invoke("ERROR", "未实现的函数: $functionName")
                }
            }
        } catch (e: Exception) {
            result.addProperty("error", e.message ?: "处理失败")
            onLog?.invoke("ERROR", "NAL2处理失败: ${e.message}")
            Log.e(TAG, "处理NAL2函数失败", e)
        }
        
        return result
    }
    
    // 辅助方法：JsonArray 转 DoubleArray
    private fun jsonArrayToDoubleArray(jsonArray: com.google.gson.JsonArray): DoubleArray {
        return DoubleArray(jsonArray.size()) { jsonArray.get(it).asDouble }
    }
    
    // 辅助方法：JsonArray 转 IntArray
    private fun jsonArrayToIntArray(jsonArray: com.google.gson.JsonArray): IntArray {
        return IntArray(jsonArray.size()) { 
            try {
                jsonArray.get(it).asInt
            } catch (e: Exception) {
                jsonArray.get(it).asDouble.toInt()
            }
        }
    }
    
    // 辅助方法：DoubleArray 转 JsonArray
    private fun doubleArrayToJsonArray(array: DoubleArray): com.google.gson.JsonArray {
        val jsonArray = com.google.gson.JsonArray()
        array.forEach { jsonArray.add(it) }
        return jsonArray
    }
    
    // 辅助方法：IntArray 转 JsonArray
    private fun intArrayToJsonArray(array: IntArray): com.google.gson.JsonArray {
        val jsonArray = com.google.gson.JsonArray()
        array.forEach { jsonArray.add(it) }
        return jsonArray
    }
}
