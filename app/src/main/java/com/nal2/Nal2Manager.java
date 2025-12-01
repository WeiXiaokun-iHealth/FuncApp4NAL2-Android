package com.nal2;

import android.content.Context;
import android.util.Log;

import au.org.nal.NativeManager;
import au.org.nal.OutputResult;

import java.lang.reflect.Field;
import java.lang.reflect.Method;

public class Nal2Manager {
    private static final String TAG = "Nal2Manager";
    private static Nal2Manager instance;
    private Context context;
    private static LogCallback logCallback;

    // 日志回调接口
    public interface LogCallback {
        void onLog(String tag, String level, String message);
    }

    // 设置日志回调
    public static void setLogCallback(LogCallback callback) {
        logCallback = callback;
    }

    // 发送日志
    private static void sendLog(String tag, String level, String message) {
        if (logCallback != null) {
            logCallback.onLog(tag, level, message);
        }
        // 同时输出到logcat
        switch (level) {
            case "DEBUG":
                Log.d(tag, message);
                break;
            case "INFO":
                Log.i(tag, message);
                break;
            case "WARN":
                Log.w(tag, message);
                break;
            case "ERROR":
                Log.e(tag, message);
                break;
            default:
                Log.v(tag, message);
                break;
        }
    }

    // 发送日志（带异常）
    private static void sendLog(String tag, String level, String message, Throwable throwable) {
        if (logCallback != null) {
            logCallback.onLog(tag, level, message + ": " + throwable.getMessage());
        }
        // 同时输出到logcat
        switch (level) {
            case "DEBUG":
                Log.d(tag, message, throwable);
                break;
            case "INFO":
                Log.i(tag, message, throwable);
                break;
            case "WARN":
                Log.w(tag, message, throwable);
                break;
            case "ERROR":
                Log.e(tag, message, throwable);
                break;
            default:
                Log.v(tag, message, throwable);
                break;
        }
    }

    private Nal2Manager(Context context) {
        this.context = context.getApplicationContext();
        NativeManager.getInstance(context);
    }

    public static synchronized Nal2Manager getInstance(Context context) {
        if (instance == null) {
            instance = new Nal2Manager(context);
        }
        return instance;
    }

    public int[] getDllVersion() {
        try {
            // NAL2 SDK可能没有直接提供dllVersion的Java封装
            // 尝试通过反射调用
            int[] version = new int[2];
            try {
                Method method = NativeManager.getInstance(context).getClass().getMethod("dllVersion", int[].class);
                method.invoke(NativeManager.getInstance(context), (Object) version);
                return version;
            } catch (NoSuchMethodException e) {
                sendLog(TAG, "WARN", "dllVersion方法不存在，返回默认版本号");
                // 如果SDK没有提供dllVersion方法，返回NAL-NL2的标准版本号
                // 根据NAL-NL2规范，当前版本通常是2.0
                return new int[] { 2, 0 };
            }
        } catch (Exception e) {
            sendLog(TAG, "ERROR", "获取DLL版本失败: " + e.getMessage());
            return new int[] { 2, 0 }; // 默认返回2.0
        }
    }

    public void setAdultChild(int adultChild, int dateOfBirth) {
        NativeManager.getInstance(context).SetAdultChild(adultChild, dateOfBirth);
    }

    public void setExperience(int experience) {
        NativeManager.getInstance(context).SetExperience(experience);
    }

    public void setCompSpeed(int compSpeed) {
        NativeManager.getInstance(context).SetCompSpeed(compSpeed);
    }

    public void setTonalLanguage(int tonal) {
        NativeManager.getInstance(context).SetTonalLanguage(tonal);
    }

    public void setGender(int gender) {
        NativeManager.getInstance(context).SetGender(gender);
    }

    // 内部类用于返回CrossOverFrequencies的结果
    public static class CrossOverFrequenciesResult {
        public double[] CFArray;
        public int[] FreqInCh;

        public CrossOverFrequenciesResult(double[] cfArray, int[] freqInCh) {
            this.CFArray = cfArray;
            this.FreqInCh = freqInCh;
        }
    }

    public CrossOverFrequenciesResult getCrossOverFrequencies(double[] cfArr, int channels, double[] acDouble,
            double[] bcDouble,
            int[] freqInCh) {
        try {
            OutputResult result = NativeManager.getInstance(context).CrossOverFrequencies_NL2(cfArr, channels, acDouble,
                    bcDouble, freqInCh);

            double[] cfArray = getOutputData(result, cfArr);

            StringBuilder cfLog = new StringBuilder("CFArray: [");
            for (int i = 0; i < cfArray.length; i++) {
                if (i > 0)
                    cfLog.append(", ");
                cfLog.append(cfArray[i]);
            }
            cfLog.append("]");
            sendLog(TAG, "DEBUG", cfLog.toString());

            StringBuilder freqLog = new StringBuilder("FreqInCh: [");
            for (int i = 0; i < freqInCh.length; i++) {
                if (i > 0)
                    freqLog.append(", ");
                freqLog.append(freqInCh[i]);
            }
            freqLog.append("]");
            sendLog(TAG, "DEBUG", freqLog.toString());

            return new CrossOverFrequenciesResult(cfArray, freqInCh);
        } catch (Exception e) {
            sendLog(TAG, "ERROR", "获取交叉频率失败: " + e.getMessage());
            return new CrossOverFrequenciesResult(cfArr, freqInCh);
        }
    }

    public void setBWC(int channels, double[] crossoverFrequencies) {
        NativeManager.getInstance(context).setBWC(channels, crossoverFrequencies);
    }

    public void setCompressionThreshold(double[] ct, int bandWidth, int selection, int WBCT, int haType, int direction,
            int mic, int[] calcChArray) {
        NativeManager.getInstance(context).CompressionThreshold_NL2(ct, bandWidth, selection, WBCT, haType, direction,
                mic, calcChArray);
    }

    public double[] getMPO(double[] mpo, int type, double[] acDouble, double[] bcDouble, int channels, int limiting) {
        try {
            sendLog(TAG, "DEBUG", "getMPO_NL2: type=" + type + ", channels=" + channels + ", limiting=" + limiting);
            OutputResult result = NativeManager.getInstance(context).getMPO_NL2(mpo, type, acDouble, bcDouble, channels,
                    limiting);
            return getOutputData(result, mpo);
        } catch (Exception e) {
            sendLog(TAG, "ERROR", "获取MPO失败: " + e.getMessage());
            return mpo;
        }
    }

    public double[] getRealEarAidedGain(double[] data, double[] acDouble, double[] bcDouble, double level, int limiting,
            int channels, int direction, int mic, int noOfAids) {
        try {
            OutputResult result = NativeManager.getInstance(context).RealEarAidedGain_NL2(data, acDouble, bcDouble,
                    level, limiting, channels, direction, mic, acDouble, noOfAids);
            return getOutputData(result, data);
        } catch (Exception e) {
            sendLog(TAG, "ERROR", "获取实耳增益失败: " + e.getMessage());
            return data;
        }
    }

    public double[] getRealEarInsertionGain(double[] reig, double[] ac, double[] bc, double L, int limiting,
            int channels,
            int direction, int mic, double[] acOther, int noOfAids) {
        try {
            OutputResult result = NativeManager.getInstance(context).RealEarInsertionGain_NL2(reig, ac, bc, L, limiting,
                    channels, direction, mic, acOther, noOfAids);
            return getOutputData(result, reig);
        } catch (Exception e) {
            sendLog(TAG, "ERROR", "获取实耳插入增益失败: " + e.getMessage());
            return reig;
        }
    }

    public double[] getRECDhIndiv(int RECDmeasType, int dateOfBirth, int aidType, int tubing, int coupler,
            int fittingDepth) {
        try {
            double[] recdh = new double[9];
            // 需要添加 coupler2 参数 (第8个参数)
            OutputResult result = NativeManager.getInstance(context).GetRECDh_indiv_NL2(recdh, RECDmeasType,
                    dateOfBirth, aidType, tubing, coupler, fittingDepth, coupler);
            return getOutputData(result, recdh);
        } catch (Exception e) {
            sendLog(TAG, "ERROR", "获取RECDh_indiv失败: " + e.getMessage());
            return new double[9];
        }
    }

    public double[] getRECDhIndiv9(int RECDmeasType, int dateOfBirth, int aidType, int tubing, int coupler,
            int fittingDepth) {
        try {
            double[] recdh = new double[9];
            // 需要添加 coupler2 参数 (第8个参数)
            OutputResult result = NativeManager.getInstance(context).GetRECDh_indiv9_NL2(recdh, RECDmeasType,
                    dateOfBirth, aidType, tubing, coupler, fittingDepth, coupler);
            return getOutputData(result, recdh);
        } catch (Exception e) {
            sendLog(TAG, "ERROR", "获取RECDh_indiv9失败: " + e.getMessage());
            return new double[9];
        }
    }

    public double[] getRECDtIndiv(int RECDmeasType, int dateOfBirth, int aidType, int tubing, int vent, int earpiece,
            int coupler, int fittingDepth) {
        try {
            double[] recdt = new double[9];
            OutputResult result = NativeManager.getInstance(context).GetRECDt_indiv_NL2(recdt, RECDmeasType,
                    dateOfBirth, aidType, tubing, vent, earpiece, coupler, fittingDepth);
            return getOutputData(result, recdt);
        } catch (Exception e) {
            sendLog(TAG, "ERROR", "获取RECDt_indiv失败: " + e.getMessage());
            return new double[9];
        }
    }

    public double[] getRECDtIndiv9(int RECDmeasType, int dateOfBirth, int aidType, int tubing, int vent, int earpiece,
            int coupler, int fittingDepth) {
        try {
            double[] recdt = new double[9];
            OutputResult result = NativeManager.getInstance(context).GetRECDt_indiv9_NL2(recdt, RECDmeasType,
                    dateOfBirth, aidType, tubing, vent, earpiece, coupler, fittingDepth);
            return getOutputData(result, recdt);
        } catch (Exception e) {
            sendLog(TAG, "ERROR", "获取RECDt_indiv9失败: " + e.getMessage());
            return new double[9];
        }
    }

    public void setRECDhIndiv(double[] recdh) {
        NativeManager.getInstance(context).SetRECDh_indiv_NL2(recdh);
    }

    public void setRECDhIndiv9(double[] recdh) {
        NativeManager.getInstance(context).SetRECDh_indiv9_NL2(recdh);
    }

    public void setRECDtIndiv(double[] recdt) {
        NativeManager.getInstance(context).SetRECDt_indiv_NL2(recdt);
    }

    public void setRECDtIndiv9(double[] recdt) {
        NativeManager.getInstance(context).SetRECDt_indiv9_NL2(recdt);
    }

    // 数据6-18的方法实现

    // RealEarInputOutputCurve_NL2
    public static class InputOutputCurveResult {
        public double[] IO;
        public double[] IOunl;

        public InputOutputCurveResult(double[] io, double[] iounl) {
            this.IO = io;
            this.IOunl = iounl;
        }
    }

    public InputOutputCurveResult getRealEarInputOutputCurve(double[] ac, double[] bc, int graphFreq, int startLevel,
            int finishLevel, int limiting, int channels, int direction, int mic, int target, double[] acOther,
            int noOfAids) {
        try {
            double[] reio = new double[100];
            double[] reiounl = new double[100];
            OutputResult result = NativeManager.getInstance(context).RealEarInputOutputCurve_NL2(reio, reiounl, ac, bc,
                    graphFreq, startLevel, finishLevel, limiting, channels, direction, mic, target, acOther, noOfAids);
            return new InputOutputCurveResult(getOutputData(result, reio), reiounl);
        } catch (Exception e) {
            sendLog(TAG, "ERROR", "获取RealEarInputOutputCurve失败: " + e.getMessage());
            return new InputOutputCurveResult(new double[100], new double[100]);
        }
    }

    // TccInputOutputCurve_NL2
    public static class TccInputOutputCurveResult {
        public double[] TccIO;
        public double[] TccIOunl;
        public int[] lineType;

        public TccInputOutputCurveResult(double[] tccIO, double[] tccIOunl, int[] lineType) {
            this.TccIO = tccIO;
            this.TccIOunl = tccIOunl;
            this.lineType = lineType;
        }
    }

    public TccInputOutputCurveResult getTccInputOutputCurve(double[] ac, double[] bc, int graphFreq, int startLevel,
            int finishLevel, int limiting, int channels, int direction, int mic, int target, int aidType,
            double[] acOther, int noOfAids, int tubing, int vent, int RECDmeasType) {
        try {
            double[] tccIO = new double[100];
            double[] tccIOunl = new double[100];
            int[] lineType = new int[100];
            OutputResult result = NativeManager.getInstance(context).TccInputOutputCurve_NL2(tccIO, tccIOunl, ac, bc,
                    graphFreq, startLevel, finishLevel, limiting, channels, direction, mic, target, aidType, acOther,
                    noOfAids, tubing, vent, RECDmeasType, lineType);
            return new TccInputOutputCurveResult(getOutputData(result, tccIO), tccIOunl, lineType);
        } catch (Exception e) {
            sendLog(TAG, "ERROR", "获取TccInputOutputCurve失败: " + e.getMessage());
            return new TccInputOutputCurveResult(new double[100], new double[100], new int[100]);
        }
    }

    // EarSimulatorInputOutputCurve_NL2
    public static class EarSimulatorInputOutputCurveResult {
        public double[] ESIO;
        public double[] ESIOunl;
        public int[] lineType;

        public EarSimulatorInputOutputCurveResult(double[] esIO, double[] esIOunl, int[] lineType) {
            this.ESIO = esIO;
            this.ESIOunl = esIOunl;
            this.lineType = lineType;
        }
    }

    public EarSimulatorInputOutputCurveResult getEarSimulatorInputOutputCurve(double[] ac, double[] bc, int graphFreq,
            int startLevel, int finishLevel, int limiting, int channels, int direction, int mic, int target,
            int aidType, double[] acOther, int noOfAids, int tubing, int vent, int RECDmeasType) {
        try {
            double[] esIO = new double[100];
            double[] esIOunl = new double[100];
            int[] lineType = new int[100];
            OutputResult result = NativeManager.getInstance(context).EarSimulatorInputOutputCurve_NL2(esIO, esIOunl, ac,
                    bc, graphFreq, startLevel, finishLevel, limiting, channels, direction, mic, target, aidType,
                    acOther, noOfAids, tubing, vent, RECDmeasType, lineType);
            return new EarSimulatorInputOutputCurveResult(getOutputData(result, esIO), esIOunl, lineType);
        } catch (Exception e) {
            sendLog(TAG, "ERROR", "获取EarSimulatorInputOutputCurve失败: " + e.getMessage());
            return new EarSimulatorInputOutputCurveResult(new double[100], new double[100], new int[100]);
        }
    }

    // Speech_o_Gram_NL2
    public static class SpeechOGramResult {
        public double[] Speech_rms;
        public double[] Speech_max;
        public double[] Speech_min;
        public double[] Speech_thresh;

        public SpeechOGramResult(double[] rms, double[] max, double[] min, double[] thresh) {
            this.Speech_rms = rms;
            this.Speech_max = max;
            this.Speech_min = min;
            this.Speech_thresh = thresh;
        }
    }

    public SpeechOGramResult getSpeechOGram(double[] ac, double[] bc, double L, int limiting, int channels,
            int direction, int mic, double[] acOther, int noOfAids) {
        try {
            double[] speechRms = new double[19];
            double[] speechMax = new double[19];
            double[] speechMin = new double[19];
            double[] speechThresh = new double[19];
            OutputResult result = NativeManager.getInstance(context).Speech_o_Gram_NL2(speechRms, speechMax, speechMin,
                    speechThresh, ac, bc, L, limiting, channels, direction, mic, acOther, noOfAids);
            return new SpeechOGramResult(getOutputData(result, speechRms), speechMax, speechMin, speechThresh);
        } catch (Exception e) {
            sendLog(TAG, "ERROR", "获取SpeechOGram失败: " + e.getMessage());
            return new SpeechOGramResult(new double[19], new double[19], new double[19], new double[19]);
        }
    }

    // AidedThreshold_NL2
    public double[] getAidedThreshold(double[] ac, double[] bc, double[] ct, int dbOption, double[] acOther,
            int noOfAids, int limiting, int channels, int direction, int mic) {
        try {
            double[] at = new double[19];
            OutputResult result = NativeManager.getInstance(context).AidedThreshold_NL2(at, ac, bc, ct, dbOption,
                    acOther, noOfAids, limiting, channels, direction, mic);
            return getOutputData(result, at);
        } catch (Exception e) {
            sendLog(TAG, "ERROR", "获取AidedThreshold失败: " + e.getMessage());
            return new double[19];
        }
    }

    // GetREDDindiv
    public double[] getREDDindiv(int defValues) {
        try {
            double[] redd = new double[19];
            OutputResult result = NativeManager.getInstance(context).GetREDDindiv(redd, defValues);
            return getOutputData(result, redd);
        } catch (Exception e) {
            sendLog(TAG, "ERROR", "获取REDDindiv失败: " + e.getMessage());
            return new double[19];
        }
    }

    // GetREDDindiv9
    public double[] getREDDindiv9(int defValues) {
        try {
            double[] redd = new double[9];
            OutputResult result = NativeManager.getInstance(context).GetREDDindiv9(redd, defValues);
            return getOutputData(result, redd);
        } catch (Exception e) {
            sendLog(TAG, "ERROR", "获取REDDindiv9失败: " + e.getMessage());
            return new double[9];
        }
    }

    // GetREURindiv
    public double[] getREURindiv(int defValues, int dateOfBirth, int direction, int mic) {
        try {
            double[] reur = new double[19];
            OutputResult result = NativeManager.getInstance(context).GetREURindiv(reur, defValues, dateOfBirth,
                    direction, mic);
            return getOutputData(result, reur);
        } catch (Exception e) {
            sendLog(TAG, "ERROR", "获取REURindiv失败: " + e.getMessage());
            return new double[19];
        }
    }

    // GetREURindiv9
    public double[] getREURindiv9(int defValues, int dateOfBirth, int direction, int mic) {
        try {
            double[] reur = new double[9];
            OutputResult result = NativeManager.getInstance(context).GetREURindiv9(reur, defValues, dateOfBirth,
                    direction, mic);
            return getOutputData(result, reur);
        } catch (Exception e) {
            sendLog(TAG, "ERROR", "获取REURindiv9失败: " + e.getMessage());
            return new double[9];
        }
    }

    // SetREDDindiv
    public void setREDDindiv(double[] redd, int defValues) {
        NativeManager.getInstance(context).SetREDDindiv(redd, defValues);
    }

    // SetREDDindiv9
    public void setREDDindiv9(double[] redd, int defValues) {
        NativeManager.getInstance(context).SetREDDindiv9(redd, defValues);
    }

    // SetREURindiv
    public void setREURindiv(double[] reur, int defValues, int dateOfBirth, int direction, int mic) {
        NativeManager.getInstance(context).SetREURindiv(reur, defValues, dateOfBirth, direction, mic);
    }

    // SetREURindiv9
    public void setREURindiv9(double[] reur, int defValues, int dateOfBirth, int direction, int mic) {
        NativeManager.getInstance(context).SetREURindiv9(reur, defValues, dateOfBirth, direction, mic);
    }

    public int[] getCenterFrequencies(int channels, double[] cfArray) {
        try {
            int[] centerF = new int[channels];
            // 调用SDK的CenterFrequencies函数
            NativeManager.getInstance(context).CenterFrequencies(centerF, cfArray, channels);
            return centerF;
        } catch (Exception e) {
            String errorMsg = "获取中心频率失败: " + e.getMessage();
            sendLog(TAG, "ERROR", errorMsg);
            e.printStackTrace();
            return new int[channels];
        }
    }

    public double[] getCompressionRatio(double[] cr, int channels, int[] centreFreq, double[] ac, double[] bc,
            int direction, int mic, int limiting, double[] acOther, int noOfAids) {
        try {
            // 详细的参数校验
            if (centreFreq == null || centreFreq.length != channels) {
                sendLog(TAG, "ERROR", "Invalid centreFreq array: expected " + channels + " elements, got " +
                        (centreFreq == null ? "null" : centreFreq.length));
                throw new IllegalArgumentException("centreFreq array size must equal channels (" + channels + ")");
            }

            if (ac == null || ac.length != 9) {
                sendLog(TAG, "ERROR", "Invalid AC array: expected 9 elements, got " +
                        (ac == null ? "null" : ac.length));
                throw new IllegalArgumentException("AC array must have 9 elements (standard frequencies)");
            }

            if (bc == null || bc.length != 9) {
                sendLog(TAG, "ERROR", "Invalid BC array: expected 9 elements, got " +
                        (bc == null ? "null" : bc.length));
                throw new IllegalArgumentException("BC array must have 9 elements (standard frequencies)");
            }

            if (acOther == null || acOther.length != 9) {
                sendLog(TAG, "ERROR", "Invalid ACother array: expected 9 elements, got " +
                        (acOther == null ? "null" : acOther.length));
                throw new IllegalArgumentException("ACother array must have 9 elements (standard frequencies)");
            }

            // 打印调试信息
            sendLog(TAG, "DEBUG", "CompressionRatio_NL2: channels=" + channels +
                    ", centreFreq length=" + centreFreq.length +
                    ", AC length=" + ac.length +
                    ", BC length=" + bc.length +
                    ", ACother length=" + acOther.length +
                    ", CR length=" + cr.length);

            // centreFreq本身就是int[]数组，直接传递
            OutputResult result = NativeManager.getInstance(context).CompressionRatio_NL2(cr, channels, centreFreq,
                    ac, bc, direction, mic, limiting, acOther, noOfAids);
            return getOutputData(result, cr);
        } catch (IllegalArgumentException e) {
            sendLog(TAG, "ERROR", "参数验证失败: " + e.getMessage(), e);
            throw e; // 重新抛出，让上层处理
        } catch (Exception e) {
            sendLog(TAG, "ERROR", "获取压缩比失败: " + e.getMessage());
            e.printStackTrace(); // 打印完整堆栈
            return cr;
        }
    }

    // 内部类用于返回TccCouplerGain的结果
    public static class TccCouplerGainResult {
        public double[] TccGain;
        public int[] lineType;

        public TccCouplerGainResult(double[] tccGain, int[] lineType) {
            this.TccGain = tccGain;
            this.lineType = lineType;
        }
    }

    public TccCouplerGainResult getTccCouplerGain(double[] gain, double[] ac, double[] bc, double L,
            int limiting,
            int channels, int direction, int mic, int target, int aidType, double[] acOther, int noOfAids, int tubing,
            int vent, int RECDmeasType, int[] lineType) {
        try {
            // lineType是输出参数，SDK会填充它
            OutputResult result = NativeManager.getInstance(context).TccCouplerGain_NL2(gain, ac, bc, L,
                    limiting, channels, direction, mic, target, aidType, acOther, noOfAids, tubing, vent, RECDmeasType,
                    lineType);
            double[] tccGain = getOutputData(result, gain);
            return new TccCouplerGainResult(tccGain, lineType);
        } catch (Exception e) {
            sendLog(TAG, "ERROR", "获取TCC增益失败: " + e.getMessage());
            return new TccCouplerGainResult(gain, lineType);
        }
    }

    // 内部类用于返回EarSimulatorGain的结果
    public static class EarSimulatorGainResult {
        public double[] ESG;
        public int[] lineType;

        public EarSimulatorGainResult(double[] esg, int[] lineType) {
            this.ESG = esg;
            this.lineType = lineType;
        }
    }

    public EarSimulatorGainResult getEarSimulatorGain(double[] gain, double[] ac, double[] bc, double L,
            int direction, int mic, int limiting, int channels, int target, int aidType, double[] acOther,
            int noOfAids, int tubing, int vent, int RECDmeasType, int[] lineType) {
        try {
            // aidType 需要转换为 int[] 数组
            int[] aidTypeArray = new int[] { aidType };
            OutputResult result = NativeManager.getInstance(context).EarSimulatorGain_NL2(gain, ac, bc, L,
                    direction, mic, limiting, channels, target, aidType, acOther, noOfAids, tubing, vent,
                    RECDmeasType, aidTypeArray);
            double[] esg = getOutputData(result, gain);
            // lineType通过aidTypeArray返回，这里简单填充
            for (int i = 0; i < lineType.length && i < aidTypeArray.length; i++) {
                lineType[i] = aidTypeArray[i];
            }
            return new EarSimulatorGainResult(esg, lineType);
        } catch (Exception e) {
            sendLog(TAG, "ERROR", "获取EarSimulator增益失败: " + e.getMessage());
            return new EarSimulatorGainResult(gain, lineType);
        }
    }

    // 通过反射获取OutputResult中的数据
    private double[] getOutputData(OutputResult result, double[] defaultValue) {
        try {
            // 尝试使用getOutput1方法
            try {
                Method method = result.getClass().getMethod("getOutput1");
                return (double[]) method.invoke(result);
            } catch (Exception e) {
                sendLog(TAG, "ERROR", "获取output1方法失败，尝试直接访问字段: " + e.getMessage());
                // 尝试直接访问output1字段
                Field field = result.getClass().getDeclaredField("output1");
                field.setAccessible(true);
                return (double[]) field.get(result);
            }
        } catch (Exception e) {
            sendLog(TAG, "ERROR", "获取OutputResult数据失败: " + e.getMessage());
            return defaultValue;
        }
    }

    // 数据25-33的新增方法实现

    // GainAt_NL2 - 直接返回double值
    public double getGainAt(int freqRequired, int targetType, double[] ac, double[] bc, double L, int limiting,
            int channels, int direction, int mic, double[] acOther, int noOfAids, int bandWidth, int target,
            int aidType, int tubing, int vent, int RECDmeasType) {
        try {
            // GainAt_NL2直接返回double值
            return NativeManager.getInstance(context).GainAt_NL2(freqRequired, targetType, ac, bc,
                    L, limiting, channels, direction, mic, acOther, noOfAids, bandWidth, target, aidType, tubing, vent,
                    RECDmeasType);
        } catch (Exception e) {
            sendLog(TAG, "ERROR", "获取GainAt失败: " + e.getMessage());
            return 0.0;
        }
    }

    // GetMLE
    public double[] getMLE(int aidType, int direction, int mic) {
        try {
            double[] mle = new double[19];
            OutputResult result = NativeManager.getInstance(context).GetMLE(mle, aidType, direction, mic);
            return getOutputData(result, mle);
        } catch (Exception e) {
            sendLog(TAG, "ERROR", "获取MLE失败: " + e.getMessage());
            return new double[19];
        }
    }

    // ReturnValues_NL2
    public static class ReturnValuesResult {
        public double[] MAF;
        public double[] BWC;
        public double[] ESCD;

        public ReturnValuesResult(double[] maf, double[] bwc, double[] escd) {
            this.MAF = maf;
            this.BWC = bwc;
            this.ESCD = escd;
        }
    }

    public ReturnValuesResult getReturnValues() {
        try {
            double[] maf = new double[19];
            double[] bwc = new double[19];
            double[] escd = new double[19];
            OutputResult result = NativeManager.getInstance(context).ReturnValues_NL2(maf, bwc, escd);
            return new ReturnValuesResult(getOutputData(result, maf), bwc, escd);
        } catch (Exception e) {
            sendLog(TAG, "ERROR", "获取ReturnValues失败: " + e.getMessage());
            return new ReturnValuesResult(new double[19], new double[19], new double[19]);
        }
    }

    // GetTubing_NL2
    public double[] getTubing(int tubing) {
        try {
            double[] tubingArray = new double[19];
            OutputResult result = NativeManager.getInstance(context).GetTubing_NL2(tubingArray, tubing);
            return getOutputData(result, tubingArray);
        } catch (Exception e) {
            sendLog(TAG, "ERROR", "获取Tubing失败: " + e.getMessage());
            return new double[19];
        }
    }

    // GetTubing9_NL2
    public double[] getTubing9(int tubing) {
        try {
            double[] tubingArray = new double[9];
            OutputResult result = NativeManager.getInstance(context).GetTubing9_NL2(tubingArray, tubing);
            return getOutputData(result, tubingArray);
        } catch (Exception e) {
            sendLog(TAG, "ERROR", "获取Tubing9失败: " + e.getMessage());
            return new double[9];
        }
    }

    // GetVentOut_NL2
    public double[] getVentOut(int vent) {
        try {
            double[] ventOut = new double[19];
            OutputResult result = NativeManager.getInstance(context).GetVentOut_NL2(ventOut, vent);
            return getOutputData(result, ventOut);
        } catch (Exception e) {
            sendLog(TAG, "ERROR", "获取VentOut失败: " + e.getMessage());
            return new double[19];
        }
    }

    // GetVentOut9_NL2
    public double[] getVentOut9(int vent) {
        try {
            double[] ventOut = new double[9];
            OutputResult result = NativeManager.getInstance(context).GetVentOut9_NL2(ventOut, vent);
            return getOutputData(result, ventOut);
        } catch (Exception e) {
            sendLog(TAG, "ERROR", "获取VentOut9失败: " + e.getMessage());
            return new double[9];
        }
    }

    // Get_SI_NL2 - 直接返回double值
    public double getSI(int s, double[] REAG, double[] Limit) {
        try {
            // Get_SI_NL2直接返回double值，参数顺序: s, REAG, Limit
            return NativeManager.getInstance(context).Get_SI_NL2(s, REAG, Limit);
        } catch (Exception e) {
            sendLog(TAG, "ERROR", "获取SI失败: " + e.getMessage());
            return 0.0;
        }
    }

    // Get_SII - 直接返回double值
    public double getSII(int nCompSpeed, double[] Speech_thresh, int s, double[] REAG, double[] REAGp, double[] REAGm,
            double[] REUR) {
        try {
            // Get_SII直接返回double值，参数顺序: nCompSpeed, Speech_thresh, s, REAG, REAGp, REAGm,
            // REUR
            return NativeManager.getInstance(context).Get_SII(nCompSpeed, Speech_thresh, s, REAG, REAGp, REAGm, REUR);
        } catch (Exception e) {
            sendLog(TAG, "ERROR", "获取SII失败: " + e.getMessage());
            return 0.0;
        }
    }
}
