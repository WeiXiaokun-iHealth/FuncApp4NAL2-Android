package com.ihealth.nal2.api.caller.utils

import android.util.Log

/**
 * GlobalVariables - 全局变量管理器
 * 
 * 管理SDK要求不可修改的全局变量：
 * - CFArray: CrossOverFrequencies (交叉频率数组)
 * - FreqInCh: 频率所在通道映射数组
 * - CT: CompressionThreshold (压缩阈值数组)
 * 
 * 这些变量一旦生成后不应再修改，除非明确删除
 */
object GlobalVariables {
    private const val TAG = "GlobalVariables"
    
    // 三个全局变量
    private var cfArray: DoubleArray = doubleArrayOf()
    private var freqInCh: IntArray = intArrayOf()
    private var ct: DoubleArray = doubleArrayOf()
    
    // 监听器列表
    private val listeners = mutableListOf<(GlobalVariablesState) -> Unit>()
    
    /**
     * 设置 CFArray (交叉频率数组) - 直接保存引用，地址不变
     */
    @Synchronized
    fun setCFArray(value: DoubleArray) {
        cfArray = value  // 直接保存引用，不复制
        notifyListeners()
        Log.d(TAG, "CFArray已更新: ${cfArray.contentToString()}")
    }
    
    /**
     * 设置 FreqInCh (频率通道映射数组) - 直接保存引用，地址不变
     */
    @Synchronized
    fun setFreqInCh(value: IntArray) {
        freqInCh = value  // 直接保存引用，不复制
        notifyListeners()
        Log.d(TAG, "FreqInCh已更新: ${freqInCh.contentToString()}")
    }
    
    /**
     * 设置 CT (压缩阈值数组) - 直接保存引用，地址不变
     */
    @Synchronized
    fun setCT(value: DoubleArray) {
        ct = value  // 直接保存引用，不复制
        notifyListeners()
        Log.d(TAG, "CT已更新: ${ct.contentToString()}")
    }
    
    /**
     * 获取 CFArray（返回引用，地址不变）
     */
    @Synchronized
    fun getCFArray(): DoubleArray = cfArray
    
    /**
     * 获取 FreqInCh（返回引用，地址不变）
     */
    @Synchronized
    fun getFreqInCh(): IntArray = freqInCh
    
    /**
     * 获取 CT（返回引用，地址不变）
     */
    @Synchronized
    fun getCT(): DoubleArray = ct
    
    /**
     * 删除 CFArray
     */
    @Synchronized
    fun deleteCFArray() {
        cfArray = doubleArrayOf()
        notifyListeners()
        Log.d(TAG, "CFArray已删除")
    }
    
    /**
     * 删除 FreqInCh
     */
    @Synchronized
    fun deleteFreqInCh() {
        freqInCh = intArrayOf()
        notifyListeners()
        Log.d(TAG, "FreqInCh已删除")
    }
    
    /**
     * 删除 CT
     */
    @Synchronized
    fun deleteCT() {
        ct = doubleArrayOf()
        notifyListeners()
        Log.d(TAG, "CT已删除")
    }
    
    /**
     * 获取所有全局变量的状态
     */
    @Synchronized
    fun getAllVariables(): GlobalVariablesState {
        return GlobalVariablesState(
            CFArray = cfArray.copyOf(),
            FreqInCh = freqInCh.copyOf(),
            CT = ct.copyOf()
        )
    }
    
    /**
     * 清空所有全局变量
     */
    @Synchronized
    fun clearAll() {
        cfArray = doubleArrayOf()
        freqInCh = intArrayOf()
        ct = doubleArrayOf()
        notifyListeners()
        Log.d(TAG, "所有全局变量已清空")
    }
    
    /**
     * 添加监听器
     */
    fun addListener(listener: (GlobalVariablesState) -> Unit) {
        synchronized(listeners) {
            listeners.add(listener)
        }
    }
    
    /**
     * 移除监听器
     */
    fun removeListener(listener: (GlobalVariablesState) -> Unit) {
        synchronized(listeners) {
            listeners.remove(listener)
        }
    }
    
    /**
     * 通知所有监听器
     */
    fun notifyListeners() {
        val state = getAllVariables()
        synchronized(listeners) {
            listeners.forEach { listener ->
                try {
                    listener(state)
                } catch (e: Exception) {
                    Log.e(TAG, "监听器执行错误", e)
                }
            }
        }
    }
    
    /**
     * 获取变量的统计信息
     */
    @Synchronized
    fun getStats(): GlobalVariablesStats {
        return GlobalVariablesStats(
            cfArrayLength = cfArray.size,
            cfArrayIsEmpty = cfArray.isEmpty(),
            freqInChLength = freqInCh.size,
            freqInChIsEmpty = freqInCh.isEmpty(),
            ctLength = ct.size,
            ctIsEmpty = ct.isEmpty()
        )
    }
}

/**
 * 全局变量状态数据类
 */
data class GlobalVariablesState(
    val CFArray: DoubleArray,
    val FreqInCh: IntArray,
    val CT: DoubleArray
) {
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (javaClass != other?.javaClass) return false

        other as GlobalVariablesState

        if (!CFArray.contentEquals(other.CFArray)) return false
        if (!FreqInCh.contentEquals(other.FreqInCh)) return false
        if (!CT.contentEquals(other.CT)) return false

        return true
    }

    override fun hashCode(): Int {
        var result = CFArray.contentHashCode()
        result = 31 * result + FreqInCh.contentHashCode()
        result = 31 * result + CT.contentHashCode()
        return result
    }
}

/**
 * 全局变量统计信息数据类
 */
data class GlobalVariablesStats(
    val cfArrayLength: Int,
    val cfArrayIsEmpty: Boolean,
    val freqInChLength: Int,
    val freqInChIsEmpty: Boolean,
    val ctLength: Int,
    val ctIsEmpty: Boolean
)
