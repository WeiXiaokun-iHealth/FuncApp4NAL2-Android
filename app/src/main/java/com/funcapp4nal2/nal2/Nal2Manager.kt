
package com.funcapp4nal2.nal2

import android.content.Context
import android.util.Log
import com.nal2.Nal2Manager as Nal2ManagerSDK

/**
 * NAL2管理器 - 单例模式
 * 封装NAL2 SDK的所有功能
 */
class Nal2Manager private constructor(context: Context) {

    private val nal2SDK = Nal2ManagerSDK.getInstance(context)
    
    companion object {
        private const val TAG = "Nal2Manager"
        
        @Volatile
        private var instance: Nal2Manager? = null
        
        fun getInstance(context: Context): Nal2Manager {
            return instance ?: synchronized(this) {
                instance ?: Nal2Manager(context.applicationContext).also { instance = it }
            }
        }
    }

    // ==================== 基础函数 ====================
    
    /**
     * 获取DLL版本
     * @return IntArray [major, minor]
     */
    fun getDllVersion(): IntArray {
        return nal2SDK.dllVersion
    }

    // ==================== 增益计算函数 ====================
    
    /**
     * 真耳插入增益
     */
    fun getRealEarInsertionGain(
        reig: DoubleArray,
        ac: DoubleArray,
        bc: DoubleArray,
        L: Double,
        limiting: Int,
        channels: Int,
        direction: Int,
        mic: Int,
        acOther: DoubleArray,
        noOfAids: Int
    ): DoubleArray {
        return nal2SDK.getRealEarInsertionGain(
            reig, ac, bc, L, limiting, channels, direction, mic, acOther, noOfAids
        )
    }

    /**
     * 真耳辅助增益
     */
    fun getRealEarAidedGain(
        data: DoubleArray,
        ac: DoubleArray,
        bc: DoubleArray,
        L: Double,
        limiting: Int,
        channels: Int,
        direction: Int,
        mic: Int,
        noOfAids: Int
    ): DoubleArray {
        return nal2SDK.getRealEarAidedGain(
            data, ac, bc, L, limiting, channels, direction, mic, noOfAids
        )
    }

    /**
     * TCC耦合器增益
     */
    fun getTccCouplerGain(
        gain: DoubleArray,
        ac: DoubleArray,
        bc: DoubleArray,
        L: Double,
        limiting: Int,
        channels: Int,
        direction: Int,
        mic: Int,
        target: Int,
        aidType: Int,
        acOther: DoubleArray,
        noOfAids: Int,
        tubing: Int,
        vent: Int,
        RECDmeasType: Int,
        lineType: IntArray
    ): Nal2ManagerSDK.TccCouplerGainResult {
        return nal2SDK.getTccCouplerGain(
            gain, ac, bc, L, limiting, channels, direction, mic,
            target, aidType, acOther, noOfAids, tubing, vent, RECDmeasType, lineType
        )
    }

    /**
     * 耳模拟器增益
     */
    fun getEarSimulatorGain(
        gain: DoubleArray,
        ac: DoubleArray,
        bc: DoubleArray,
        L: Double,
        direction: Int,
        mic: Int,
        limiting: Int,
        channels: Int,
        target: Int,
        aidType: Int,
        acOther: DoubleArray,
        noOfAids: Int,
        tubing: Int,
        vent: Int,
        RECDmeasType: Int,
        lineType: IntArray
    ): Nal2ManagerSDK.EarSimulatorGainResult {
        return nal2SDK.getEarSimulatorGain(
            gain, ac, bc, L, direction, mic, limiting, channels,
            target, aidType, acOther, noOfAids, tubing, vent, RECDmeasType, lineType
        )
    }

    // ==================== 频率和通道函数 ====================
    
    /**
     * 交叉频率
     */
    fun getCrossOverFrequencies(
        cfArr: DoubleArray,
        channels: Int,
        ac: DoubleArray,
        bc: DoubleArray,
        freqInCh: IntArray
    ): Nal2ManagerSDK.CrossOverFrequenciesResult {
        return nal2SDK.getCrossOverFrequencies(cfArr, channels, ac, bc, freqInCh)
    }

    /**
     * 中心频率
     */
    fun getCenterFrequencies(channels: Int, cfArray: DoubleArray): IntArray {
        return nal2SDK.getCenterFrequencies(channels, cfArray)
    }

    /**
     * 设置带宽校正
     */
    fun setBWC(channels: Int, crossOver: DoubleArray) {
        nal2SDK.setBWC(channels, crossOver)
    }

    // ==================== 压缩参数函数 ====================
    
    /**
     * 压缩阈值
     */
    fun setCompressionThreshold(
        ct: DoubleArray,
        bandwidth: Int,
        selection: Int,
        WBCT: Int,
        aidType: Int,
        direction: Int,
        mic: Int,
        calcCh: IntArray
    ) {
        nal2SDK.setCompressionThreshold(
            ct, bandwidth, selection, WBCT, aidType, direction, mic, calcCh
        )
    }

    /**
     * 压缩比
     */
    fun getCompressionRatio(
        cr: DoubleArray,
        channels: Int,
        centreFreq: IntArray,
        ac: DoubleArray,
        bc: DoubleArray,
        direction: Int,
        mic: Int,
        limiting: Int,
        acOther: DoubleArray,
        noOfAids: Int
    ): DoubleArray {
        return nal2SDK.getCompressionRatio(
            cr, channels, centreFreq, ac, bc, direction, mic, limiting, acOther, noOfAids
        )
    }

    // ==================== MPO函数 ====================
    
    /**
     * 最大功率输出
     */
    fun getMPO(
        mpo: DoubleArray,
        type: Int,
        ac: DoubleArray,
        bc: DoubleArray,
        channels: Int,
        limiting: Int
    ): DoubleArray {
        return nal2SDK.getMPO(mpo, type, ac, bc, channels, limiting)
    }

    // ==================== 输入输出曲线函数 ====================
    
    /**
     * 真耳输入输出曲线
     */
    fun getRealEarInputOutputCurve(
        ac: DoubleArray,
        bc: DoubleArray,
        graphFreq: Int,
        startLevel: Int,
        finishLevel: Int,
        limiting: Int,
        channels: Int,
        direction: Int,
        mic: Int,
        target: Int,
        acOther: DoubleArray,
        noOfAids: Int
    ): Nal2ManagerSDK.InputOutputCurveResult {
        return nal2SDK.getRealEarInputOutputCurve(
            ac, bc, graphFreq, startLevel, finishLevel, limiting,
            channels, direction, mic, target, acOther, noOfAids
        )
    }

    /**
     * TCC输入输出曲线
     */
    fun getTccInputOutputCurve(
        ac: DoubleArray,
        bc: DoubleArray,
        graphFreq: Int,
        startLevel: Int,
        finishLevel: Int,
        limiting: Int,
        channels: Int,
        direction: Int,
        mic: Int,
        target: Int,
        aidType: Int,
        acOther: DoubleArray,
        noOfAids: Int,
        tubing: Int,
        vent: Int,
        RECDmeasType: Int
    ): Nal2ManagerSDK.TccInputOutputCurveResult {
        return nal2SDK.getTccInputOutputCurve(
            ac, bc, graphFreq, startLevel, finishLevel, limiting, channels,
            direction, mic, target, aidType, acOther, noOfAids, tubing, vent, RECDmeasType
        )
    }

    /**
     * 耳模拟器输入输出曲线
     */
    fun getEarSimulatorInputOutputCurve(
        ac: DoubleArray,
        bc: DoubleArray,
        graphFreq: Int,
        startLevel: Int,
        finishLevel: Int,
        limiting: Int,
        channels: Int,
        direction: Int,
        mic: Int,
        target: Int,
        aidType: Int,
        acOther: DoubleArray,
        noOfAids: Int,
        tubing: Int,
        vent: Int,
        RECDmeasType: Int
    ): Nal2ManagerSDK.EarSimulatorInputOutputCurveResult {
        return nal2SDK.getEarSimulatorInputOutputCurve(
            ac, bc, graphFreq, startLevel, finishLevel, limiting, channels,
            direction, mic, target, aidType, acOther, noOfAids, tubing, vent, RECDmeasType
        )
    }

    // ==================== 语音图和辅助阈值 ====================
    
    /**
     * 语音图
     */
    fun getSpeechOGram(
        ac: DoubleArray,
        bc: DoubleArray,
        L: Double,
        limiting: Int,
        channels: Int,
        direction: Int,
        mic: Int,
        acOther: DoubleArray,
        noOfAids: Int
    ): Nal2ManagerSDK.SpeechOGramResult {
        return nal2SDK.getSpeechOGram(
            ac, bc, L, limiting, channels, direction, mic, acOther, noOfAids
        )
    }

    /**
     * 辅助阈值
     */
    fun getAidedThreshold(
        ac: DoubleArray,
        bc: DoubleArray,
        ct: DoubleArray,
        dbOption: Int,
        acOther: DoubleArray,
        noOfAids: Int,
        limiting: Int,
        channels: Int,
        direction: Int,
        mic: Int
    ): DoubleArray {
        return nal2SDK.getAidedThreshold(
            ac, bc, ct, dbOption, acOther, noOfAids, limiting, channels, direction, mic
        )
    }

    // ==================== REDD和REUR函数 ====================
    
    fun getREDDindiv(defValues: Int): DoubleArray {
        return nal2SDK.getREDDindiv(defValues)
    }

    fun getREDDindiv9(defValues: Int): DoubleArray {
        return nal2SDK.getREDDindiv9(defValues)
    }

    fun getREURindiv(defValues: Int, dateOfBirth: Int, direction: Int, mic: Int): DoubleArray {
        return nal2SDK.getREURindiv(defValues, dateOfBirth, direction, mic)
    }

    fun getREURindiv9(defValues: Int, dateOfBirth: Int, direction: Int, mic: Int): DoubleArray {
        return nal2SDK.getREURindiv9(defValues, dateOfBirth, direction, mic)
    }

    fun setREDDindiv(redd: DoubleArray, defValues: Int) {
        nal2SDK.setREDDindiv(redd, defValues)
    }

    fun setREDDindiv9(redd: DoubleArray, defValues: Int) {
        nal2SDK.setREDDindiv9(redd, defValues)
    }

    fun setREURindiv(reur: DoubleArray, defValues: Int, dateOfBirth: Int, direction: Int, mic: Int) {
        nal2SDK.setREURindiv(reur, defValues, dateOfBirth, direction, mic)
    }

    fun setREURindiv9(reur: DoubleArray, defValues: Int, dateOfBirth: Int, direction: Int, mic: Int) {
        nal2SDK.setREURindiv9(reur, defValues, dateOfBirth, direction, mic)
    }

    // ==================== RECD函数 ====================
    
    fun getRECDhIndiv(
        RECDmeasType: Int,
        dateOfBirth: Int,
        aidType: Int,
        tubing: Int,
        coupler: Int,
        fittingDepth: Int
    ): DoubleArray {
        return nal2SDK.getRECDhIndiv(RECDmeasType, dateOfBirth, aidType, tubing, coupler, fittingDepth)
    }

    fun getRECDhIndiv9(
        RECDmeasType: Int,
        dateOfBirth: Int,
        aidType: Int,
        tubing: Int,
        coupler: Int,
        fittingDepth: Int
    ): DoubleArray {
        return nal2SDK.getRECDhIndiv9(RECDmeasType, dateOfBirth, aidType, tubing, coupler, fittingDepth)
    }

    fun getRECDtIndiv(
        RECDmeasType: Int,
        dateOfBirth: Int,
        aidType: Int,
        tubing: Int,
        vent: Int,
        earpiece: Int,
        coupler: Int,
        fittingDepth: Int
    ): DoubleArray {
        return nal2SDK.getRECDtIndiv(
            RECDmeasType, dateOfBirth, aidType, tubing, vent, earpiece, coupler, fittingDepth
        )
    }

    fun getRECDtIndiv9(
        RECDmeasType: Int,
        dateOfBirth: Int,
        aidType: Int,
        tubing: Int,
        vent: Int,
        earpiece: Int,
        coupler: Int,
        fittingDepth: Int
    ): DoubleArray {
        return nal2SDK.getRECDtIndiv9(
            RECDmeasType, dateOfBirth, aidType, tubing, vent, earpiece, coupler, fittingDepth
        )
    }

    fun setRECDhIndiv(recdh: DoubleArray) {
        nal2SDK.setRECDhIndiv(recdh)
    }

    fun setRECDhIndiv9(recdh: DoubleArray) {
        nal2SDK.setRECDhIndiv9(recdh)
    }

    fun setRECDtIndiv(recdt: DoubleArray) {
        nal2SDK.setRECDtIndiv(recdt)
    }

    fun setRECDtIndiv9(recdt: DoubleArray) {
        nal2SDK.setRECDtIndiv9(recdt)
    }

    // ==================== 配置函数 ====================
    
    fun setAdultChild(adultChild: Int, dateOfBirth: Int) {
        nal2SDK.setAdultChild(adultChild, dateOfBirth)
    }

    fun setExperience(experience: Int) {
        nal2SDK.setExperience(experience)
    }

    fun setCompSpeed(compSpeed: Int) {
        nal2SDK.setCompSpeed(compSpeed)
    }

    fun setTonalLanguage(tonal: Int) {
        nal2SDK.setTonalLanguage(tonal)
    }

    fun setGender(gender: Int) {
        nal2SDK.setGender(gender)
    }

    // ==================== 其他函数 ====================
    
    fun getGainAt(
        freqRequired: Int,
        targetType: Int,
        ac: DoubleArray,
        bc: DoubleArray,
        L: Double,
        limiting: Int,
        channels: Int,
        direction: Int,
        mic: Int,
        acOther: DoubleArray,
        noOfAids: Int,
        bandWidth: Int,
        target: Int,
        aidType: Int,
        tubing: Int,
        vent: Int,
        RECDmeasType: Int
    ): Double {
        return nal2SDK.getGainAt(
            freqRequired, targetType, ac, bc, L, limiting, channels, direction,
            mic, acOther, noOfAids, bandWidth, target, aidType, tubing, vent, RECDmeasType
        )
    }

    fun getMLE(aidType: Int, direction: Int, mic: Int): DoubleArray {
        return nal2SDK.getMLE(aidType, direction, mic)
    }

    fun getReturnValues(): Nal2ManagerSDK.ReturnValuesResult {
        return nal2SDK.returnValues
    }

    fun getTubing(tubing: Int): DoubleArray {
        return nal2SDK.getTubing(tubing)
    }

    fun getTubing9(tubing: Int): DoubleArray {
        return nal2SDK.getTubing9(tubing)
    }

    fun getVentOut(vent: Int): DoubleArray {
        return nal2SDK.getVentOut(vent)
    }

    fun getVentOut9(vent: Int): DoubleArray {
        return nal2SDK.getVentOut9(vent)
    }

    fun getSI(s: Int, reag: DoubleArray, limit: DoubleArray): Double {
        return nal2SDK.getSI(s, reag, limit)
    }

    fun getSII(
        nCompSpeed: Int,
        speechThresh: DoubleArray,
        s: Int,
        reag: DoubleArray,
        reagp: DoubleArray,
        reagm: DoubleArray,
        reur: DoubleArray
    ): Double {
        return nal2SDK.getSII(nCompSpeed, speechThresh, s, reag, reagp, reagm, reur)
    }
}
