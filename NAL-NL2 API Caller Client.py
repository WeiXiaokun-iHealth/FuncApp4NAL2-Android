import json
import os
import socket
import threading
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional

import requests
from requests.exceptions import RequestException

from PySide6 import QtCore, QtGui, QtWidgets

APP_NAME = "NAL-NL2 API Caller Client"
APP_VERSION = "Ver2025.12.08-2"

#Ver2025.12.04-4 增加“输入/输出曲线”标签页; "主页"标签页step1-8初始化按钮追加调用20号函数;
#Ver2025.12.04-5 “输入/输出曲线”标签页增加了绘制增益曲线的功能，方便直观对比
#Ver2025.12.05-1 “输入/输出曲线”标签页 图像区Y轴范围向下扩大到-30dB
#Ver2025.12.05-2 所有页面切入后先读取config文件，防止不同步。关闭软件时不写config文件，防止写入旧数据。“增益/响应曲线”标签页修复为0的数据点不绘图的bug
#Ver2025.12.08-1 "主页"右侧两个"设置RECD(9) REDD(9) REUR(9)"拆分为独立按钮；删除不用的方法
#Ver2025.12.08-2 "主页"、"函数测试"两个tab独立成为一级类，方便每个页面单独调整
#Ver2025.12.09-1 “增益/响应曲线”tab布局微调，右侧下面四个按钮上移到与“清除曲线”按钮同一行


DEFAULT_CONFIG_FILE = "nal_nl2_config.json"
DEFAULT_TEMPLATES_FILE = "function_templates.json"

FREQS_19 = [125,160,200,250,315,400,500,630,800,1000,1250,1600,2000,2500,3150,4000,5000,6300,8000]
FREQS_9 = [250,500,1000,1500,2000,3000,4000,6000,8000]

DEFAULT_TEMPLATES = {
    "templates": [
        {"label": "1 - dllVersion", "function": "dllVersion", "params": []},

        {"label": "2 - RealEarInsertionGain_NL2", "function": "RealEarInsertionGain_NL2",
         "params": ["AC", "BC", "L", "limiting", "channels", "direction", "mic", "ACother", "noOfAids"]},

        {"label": "3 - RealEarAidedGain_NL2", "function": "RealEarAidedGain_NL2",
         "params": ["AC", "BC", "L", "limiting", "channels", "direction", "mic", "ACother", "noOfAids"]},

        {"label": "4 - TccCouplerGain_NL2", "function": "TccCouplerGain_NL2",
         "params": ["AC", "BC", "L", "limiting", "channels", "direction", "mic", "target", "aidType", "ACother", "noOfAids", "tubing", "vent", "RECDmeasType"]},

        {"label": "5 - EarSimulatorGain_NL2", "function": "EarSimulatorGain_NL2",
         "params": ["AC", "BC", "L", "direction", "mic", "limiting", "channels", "target", "aidType", "ACother", "noOfAids", "tubing", "vent", "RECDmeasType"]}, #5 "tubing","RECDmeasType" NOT USED

        {"label": "6 - RealEarInputOutputCurve_NL2", "function": "RealEarInputOutputCurve_NL2",
         "params": ["AC", "BC", "graphFreq", "startLevel", "finishLevel", "limiting", "channels", "direction", "mic", "target", "ACother", "noOfAids"]},

        {"label": "7 - TccInputOutputCurve_NL2", "function": "TccInputOutputCurve_NL2",
         "params": ["AC", "BC", "graphFreq", "startLevel", "finishLevel", "limiting", "channels", "direction", "mic", "target", "aidType", "ACother", "noOfAids", "tubing", "vent", "RECDmeasType"]}, #7 "tubing","RECDmeasType" NOT USED

        {"label": "8 - EarSimulatorInputOutputCurve_NL2", "function": "EarSimulatorInputOutputCurve_NL2",
         "params": ["AC", "BC", "graphFreq", "startLevel", "finishLevel", "limiting", "channels", "direction", "mic", "target", "aidType", "ACother", "noOfAids", "tubing", "vent", "RECDmeasType"]}, #8 "tubing","RECDmeasType" NOT USED

        {"label": "9 - Speech_o_Gram_NL2", "function": "Speech_o_Gram_NL2",
         "params": ["AC", "BC", "L", "limiting", "channels", "direction", "mic", "ACother", "noOfAids"]},

        {"label": "10 - AidedThreshold_NL2", "function": "AidedThreshold_NL2",
         "params": ["AC", "BC", "CT", "dbOption", "ACother", "noOfAids", "limiting", "channels", "direction", "mic"]},

        {"label": "11 - GetREDDindiv", "function": "GetREDDindiv", "params": ["REDD_defValues"]},
        {"label": "12 - GetREDDindiv9", "function": "GetREDDindiv9", "params": ["REDD_defValues"]},
        {"label": "13 - GetREURindiv", "function": "GetREURindiv", "params": ["REUR_defValues", "dateOfBirth", "direction", "mic"]},
        {"label": "14 - GetREURindiv9", "function": "GetREURindiv9", "params": ["REUR_defValues", "dateOfBirth", "direction", "mic"]},
        {"label": "15 - SetREDDindiv", "function": "SetREDDindiv", "params": ["REDD", "REDD_defValues"]},
        {"label": "16 - SetREDDindiv9", "function": "SetREDDindiv9", "params": ["REDD9", "REDD_defValues"]},
        {"label": "17 - SetREURindiv", "function": "SetREURindiv", "params": ["REUR", "REUR_defValues", "dateOfBirth", "direction", "mic"]},
        {"label": "18 - SetREURindiv9", "function": "SetREURindiv9", "params": ["REUR9", "REUR_defValues", "dateOfBirth", "direction", "mic"]},
        {"label": "19 - CrossOverFrequencies_NL2", "function": "CrossOverFrequencies_NL2", "params": ["channels", "AC", "BC"]}, #19 "BC" NOT USED, 需要把BC填充为AC的值，以符合Step1-9文档的要求
        {"label": "20 - CenterFrequencies", "function": "CenterFrequencies", "params": ["CFArray", "channels"]},

        {"label": "21 - CompressionThreshold_NL2", "function": "CompressionThreshold_NL2",
         "params": ["bandWidth", "selection", "WBCT", "aidType", "direction", "mic", "calcCh"]},

        {"label": "22 - CompressionRatio_NL2", "function": "CompressionRatio_NL2",
         "params": ["channels", "centreFreq", "AC", "BC", "direction", "mic", "limiting", "ACother", "noOfAids"]},

        {"label": "23 - setBWC", "function": "setBWC", "params": ["channels", "crossOver"]},
        {"label": "24 - getMPO_NL2 (RESR/SSPL)", "function": "getMPO_NL2", "params": ["type", "AC", "BC", "channels", "limiting"]},

        {"label": "25 - GainAt_NL2", "function": "GainAt_NL2",
         "params": ["freqRequired", "targetType", "AC", "BC", "L", "limiting", "channels", "direction", "mic",
                    "ACother", "noOfAids", "bandWidth", "target", "aidType", "tubing", "vent", "RECDmeasType"]},

        {"label": "26 - GetMLE", "function": "GetMLE",  "params": ["aidType", "direction", "mic"]},
        {"label": "27 - ReturnValues_NL2", "function": "ReturnValues_NL2", "params": []},
        {"label": "28 - GetTubing_NL2", "function": "GetTubing_NL2", "params": ["tubing"]},
        {"label": "29 - GetTubing9_NL2", "function": "GetTubing9_NL2", "params": ["tubing"]},
        {"label": "30 - GetVentOut_NL2", "function": "GetVentOut_NL2", "params": ["vent"]},
        {"label": "31 - GetVentOut9_NL2", "function": "GetVentOut9_NL2", "params": ["vent"]},
        {"label": "32 - Get_SI_NL2", "function": "Get_SI_NL2", "params": ["s", "REAG", "MPO"]}, # MPO的位置在原文档里是 Limit,猜测就是MPO

        {"label": "33 - Get_SII", "function": "Get_SII",
         "params": ["compSpeed", "Speech_thresh", "s", "REAG", "REAGp", "REAGm", "REUR"]}, # compSpeed 的位置在文档里是 nCompSpeed ,猜测是同一个数据

        {"label": "34 - SetAdultChild", "function": "SetAdultChild", "params": ["adultChild", "dateOfBirth"]},
        {"label": "35 - SetExperience", "function": "SetExperience", "params": ["experience"]},
        {"label": "36 - SetCompSpeed", "function": "SetCompSpeed", "params": ["compSpeed"]},
        {"label": "37 - SetTonalLanguage", "function": "SetTonalLanguage", "params": ["tonal"]},
        {"label": "38 - SetGender", "function": "SetGender", "params": ["gender"]},

        {"label": "39 - GetRECDh_indiv_NL2", "function": "GetRECDh_indiv_NL2",
         "params": ["RECDmeasType", "dateOfBirth", "aidType", "tubing", "vent", "coupler", "fittingDepth"]}, #39 "aidType" NOT USED

        {"label": "40 - GetRECDh_indiv9_NL2", "function": "GetRECDh_indiv9_NL2",
         "params": ["RECDmeasType", "dateOfBirth", "aidType", "tubing", "vent", "coupler", "fittingDepth"]},

        {"label": "41 - GetRECDt_indiv_NL2", "function": "GetRECDt_indiv_NL2",
         "params": ["RECDmeasType", "dateOfBirth", "aidType", "tubing", "vent", "earpiece", "coupler", "fittingDepth"]}, #41 "aidType" NOT USED

        {"label": "42 - GetRECDt_indiv9_NL2", "function": "GetRECDt_indiv9_NL2",
         "params": ["RECDmeasType", "dateOfBirth", "aidType", "tubing", "vent", "earpiece", "coupler", "fittingDepth"]},

        {"label": "43 - SetRECDh_indiv_NL2", "function": "SetRECDh_indiv_NL2", "params": ["RECDh"]},
        {"label": "44 - SetRECDh_indiv9_NL2", "function": "SetRECDh_indiv9_NL2", "params": ["RECDh9"]},
        {"label": "45 - SetRECDt_indiv_NL2", "function": "SetRECDt_indiv_NL2", "params": ["RECDt"]},
        {"label": "46 - SetRECDt_indiv9_NL2", "function": "SetRECDt_indiv9_NL2", "params": ["RECDt9"]}
    ]
}

def ensure_templates_file(path: str):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_TEMPLATES, f, ensure_ascii=False, indent=2)

@dataclass
class AppConfig:
# Server
    server_ip: str = "192.168.0.100"
    server_port: int = 8080
    server_path: str = "/api/nal2/process"

# ======================================================================================================================
# 在配置页面出现的参数
# ======================================================================================================================
# 用户数据
    adultChild: int = 0          # 0=成人;1=儿童;2=按dateOfBirth计算 (34i)
    dateOfBirth: int = 19810101  # yyyymmdd (34i 13i 14i 17i 18i 39i 40i 41i 42i)
    experience: int = 0          # 0=有经验;1=新用户 (35i)
    compSpeed: int = 1           # 0=慢;1=快;2=双速 (36i 33i)
    tonal: int = 0               # 0=非声调;1=声调 (37i)
    gender: int = 1              # 0=未知;1=男;2=女 (38i)
    
# 用户听阈（9 点：250,500,1k,1.5k,2k,3k,4k,6k,8k Hz）
    AC:      List[float] = field(default_factory=lambda: [45, 40, 40, 999, 65, 999, 70, 70, 55])   # (2i 3i 4i 5i 6i 7i 8i 9i 10i 19i 22i 24i 25i)
    BC:      List[float] = field(default_factory=lambda: [45, 40, 40, 999, 65, 999, 70, 999, 999]) # (2i 3i 4i 5i 6i 7i 8i 9i 10i 19i 22i 24i 25i) 实际上19号函数文档里标注NOT USED，用AC值代替
    ACother: List[float] = field(default_factory=lambda: [45, 45, 45, 999, 65, 999, 70, 65, 55])   # (2i 3i 4i 5i 6i 7i 8i 9i 10i 22i 25i)


# ==============================
# 常用参数（多数 API 共享）
# ==============================
    channels: int = 18           # 1..18 (2i 3i 4i 5i 6i 7i 8i 10i 19i 20i 22i 23i 24i 25i)
    bandWidth: int = 0           # 0=宽带;1=窄带 (21i 25i)
    selection: int = 1           # 计算CT时使用的增益目标。0=REIG;1=REAG;2=2cc;3=EarSimulator (21i)
    WBCT: int = 52               # 宽带压缩阈         (21i)
    aidType: int = 3             # 0=CIC;1=ITC;2=ITE;3=BTE (4i 5i 7i 8i 21i 25i 26i 39i 40i 41i 42i) 实际上39、41号函数文档里标注NOT USED
    direction: int = 0           # 0=0°;1=45°            (2i 3i 4i 5i 6i 7i 8i 9i 10i 13i 14i 17i 18i 21i 22i 25i 26i)
    mic: int = 1                 # 0=自由场;1=头表面(MRP) (2i 3i 4i 5i 6i 7i 8i 9i 10i 13i 14i 17i 18i 21i 22i 25i 26i)
    limiting: int = 0            # 0=关;1=宽带;2=多通道 (2i 3i 4i 5i 6i 7i 8i 9i 10i 22i 24i 25i)
    noOfAids: int = 1            # 0=单耳;1=双耳           (2i 3i 4i 5i 6i 7i 8i 9i 10i 22i 25i)
    calcCh: List[int] = field(default_factory=lambda: [1] * 19)  # CompressionThreshold 重算标志 (21i)


# ==============================
# 装配/耦合相关（RECD/管路/通气孔等）
# ==============================
    tubing: int = 3              # 0=Libby4;1=Libby3;2=#13;3=细管;4=RITC;5=None (4i 5i 7i 8i 25i 28i 29i 39i 40i 41i 42i)  实际上5、7、8号函数文档里标注NOT USED
    vent: int = 0                # 0=紧;1=封闭;2=封闭穹顶;3=1mm;4=2mm;5=3mm;6=开放穹顶 (4i 5i 7i 8i 25i 30i 31i 39i 40i 41i 42i)
    coupler: int = 0             # 0=HA1;1=HA2 (39i 40i 41i 42i)
    fittingDepth: int = 0        # 0=标准;1=深;2=浅 (39i 40i 41i 42i)
    earpiece: int = 0            # 0=泡棉;1=自制耳模 (41i 42i)
    RECDmeasType: int = 0        # 0=预测;1=实测 (4i 5i 7i 8i 25i 39i 40i 41i 42i) 实际上4、5、7、8号函数文档里标注NOT USED
    REDD_defValues: int = 0      # Get/Set REDD: 0=预测;1=客户数据 (11i 12i 15i 16i)
    REUR_defValues: int = 0      # Get/Set REUR: 0=预测;1=客户数据 (13i 14i 17i 18i)

# ==============================
# 获取增益或曲线用
# ==============================
    L: int = 65                  # 宽带输入电平(dB)          (2i 3i 4i 5i 6i 7i 8i 9i 25i)
    target: int = 1              # 目标：0=REIG;1=REAG (4i 5i 6i 7i 8i 25i)
    targetType: int = 1          # GainAt_NL2使用的增益目标: 0=REIG;1=REAG;2=2cc;3=EarSim (25i)
    freqRequired: int = 9        # 单频点计算索引 0..18 (25i)
    type: int = 1                # getMPO_NL2 用：0=RESR;1=SSPL (24i)
    
    graphFreq: int = 9           # IO 曲线用：0..18 (6i 7i 8i)
    startLevel: int = 40         # IO 曲线起始 dB (6i 7i 8i)
    finishLevel: int = 90        # IO 曲线结束 dB (6i 7i 8i)
    s: int = 2                   # SI/SII 语音级别索引 (32i 33i)
    dbOption: int = 0            # AidedThreshold: 0=dB HL;1=dB SPL (10i)

# ==============================
# 频带/分频计算（19 或可变）
# ==============================
    CFArray: List[float] = field(default_factory=lambda: [0.0] * 19)   # CrossOverFrequencies 输出；实际用长=channels-1 (19o 20i)
    crossOver: List[float] = field(default_factory=lambda: [0.0] * 19) # setBWC 输入 (23i)
    FreqInCh: List[int] = field(default_factory=lambda: [0] * 19)      # 频点所属通道 (19o)
    centerF: List[int] = field(default_factory=lambda: [0] * 19)       # CenterFrequencies 输出 (20o)
    centreFreq: List[int] = field(default_factory=lambda: [0] * 19)    # CompressionRatio 输入名 (22i)

# ==============================
# 阈值/压缩（21,22）
# ==============================
    CT: List[float] = field(default_factory=lambda: [0.0] * 19)        # CompressionThreshold_NL2 输出 / AidedThreshold 输入 (21o 10i)
    CR: List[float] = field(default_factory=lambda: [0.0] * 19)        # CompressionRatio_NL2 输出 (22o)

# ==============================
# RECD 系列（39-46）
# ==============================
    RECDh:  List[float] = field(default_factory=lambda: [0.0] * 19)   # GetRECDh_indiv_NL2 / SetRECDh_indiv_NL2 (39o 43i)
    RECDh9: List[float] = field(default_factory=lambda: [0.0] * 9)    # GetRECDh_indiv9_NL2 / SetRECDh_indiv9_NL2 (40o 44i)
    RECDt:  List[float] = field(default_factory=lambda: [0.0] * 19)   # GetRECDt_indiv_NL2 / SetRECDt_indiv_NL2 (41o 45i)
    RECDt9: List[float] = field(default_factory=lambda: [0.0] * 9)    # GetRECDt_indiv9_NL2 / SetRECDt_indiv9_NL2 (42o 46i)

# ==============================
# REUR / REDD（11-18）
# ==============================
    REDD: List[float] = field(default_factory=lambda: [0.0] * 19)      # GetREDDindiv / SetREDDindiv (11o 15i)
    REDD9: List[float] = field(default_factory=lambda: [0.0] * 9)      # GetREDDindiv9 / SetREDDindiv9 (12o 16i)
    REUR: List[float] = field(default_factory=lambda: [0.0] * 19)      # GetREURindiv / SetREURindiv / Get_SII (13o 17i 33i)
    REUR9: List[float] = field(default_factory=lambda: [0.0] * 9)      # GetREURindiv9 / SetREURindiv9 (14o 18i)

# ==============================
# 实耳/耦合/耳模拟 增益与曲线（2-8,24-25）
# ==============================
    REIG: List[float] = field(default_factory=lambda: [0.0] * 19)      # RealEarInsertionGain_NL2 (2o)
    REAG: List[float] = field(default_factory=lambda: [0.0] * 19)      # RealEarAidedGain_NL2 / Get_SI_NL2 / Get_SII (3o 32i 33i)
    TccCG: List[float] = field(default_factory=lambda: [0.0] * 19)     # TccCouplerGain_NL2 (4o)
    ESG: List[float] = field(default_factory=lambda: [0.0] * 19)       # EarSimulatorGain_NL2 (5o)
    lineType19: List[int] = field(default_factory=lambda: [0] * 19)    # 画线类型输出 (4o 5o)

    MPO: List[float] = field(default_factory=lambda: [0.0] * 19)       # getMPO_NL2 (24o)
    gainAt_value: float = 0.0                                         # GainAt_NL2 返回值 (25o)

    REIO: List[float] = field(default_factory=lambda: [0.0] * 100)     # RealEarInputOutputCurve_NL2（限幅）(6o)
    REIOunl: List[float] = field(default_factory=lambda: [0.0] * 100)  # RealEarInputOutputCurve_NL2（无限幅）(6o)
    TccIO: List[float] = field(default_factory=lambda: [0.0] * 100)    # TccInputOutputCurve_NL2（限幅）(7o)
    TccIOunl: List[float] = field(default_factory=lambda: [0.0] * 100) # TccInputOutputCurve_NL2（无限幅）(7o)
    ESIO: List[float] = field(default_factory=lambda: [0.0] * 100)     # EarSimulatorInputOutputCurve_NL2（限幅）(8o)
    ESIOunl: List[float] = field(default_factory=lambda: [0.0] * 100)  # EarSimulatorInputOutputCurve_NL2（无限幅）(8o)
    lineType100: List[int] = field(default_factory=lambda: [0] * 100)  # 画线类型输出 (7o 8o)


# ==============================
# 语音图/指标（9,32,33）
# ==============================
    Speech_rms: List[float] = field(default_factory=lambda: [0.0] * 19)    # Speech_o_Gram_NL2 (9o)
    Speech_max: List[float] = field(default_factory=lambda: [0.0] * 19)    # Speech_o_Gram_NL2 (9o)
    Speech_min: List[float] = field(default_factory=lambda: [0.0] * 19)    # Speech_o_Gram_NL2 (9o)
    Speech_thresh: List[float] = field(default_factory=lambda: [0.0] * 19) # Speech_o_Gram_NL2 / Get_SII (9o 33i)
    Limit: List[float] = field(default_factory=lambda: [0.0] * 19)         # Get_SI_NL2 (32i)

    REAGp: List[float] = field(default_factory=lambda: [0.0] * 19)         # Get_SII (33i)
    REAGm: List[float] = field(default_factory=lambda: [0.0] * 19)         # Get_SII (33i)
    SI_value: float = 0.0                                                  # Get_SI_NL2 返回值 (32o)
    SII_value: float = 0.0                                                 # Get_SII 返回值 (33o)

# ==============================
# Aided Threshold（10）
# ==============================
    AT: List[float] = field(default_factory=lambda: [0.0] * 19)        # AidedThreshold_NL2 (10o)


# ==============================
# 参考数据与修正（26,27,28-31）
# ==============================
    MLE: List[float] = field(default_factory=lambda: [0.0] * 19)       # GetMLE (26o)
    MAF: List[float] = field(default_factory=lambda: [0.0] * 19)       # ReturnValues_NL2 (27o)
    BWC: List[float] = field(default_factory=lambda: [0.0] * 19)       # ReturnValues_NL2 (27o)
    ESCD: List[float] = field(default_factory=lambda: [0.0] * 19)      # ReturnValues_NL2 (27o)

    Tubing: List[float] = field(default_factory=lambda: [0.0] * 19)    # GetTubing_NL2 (28o)
    Tubing9: List[float] = field(default_factory=lambda: [0.0] * 9)    # GetTubing9_NL2 (29o)
    Ventout: List[float] = field(default_factory=lambda: [0.0] * 19)   # GetVentOut_NL2 (30o)
    Ventout9: List[float] = field(default_factory=lambda: [0.0] * 9)   # GetVentOut9_NL2 (31o)

# ==============================
# 版本信息（1）
# ==============================
    dll_major: int = 0                                               # dllVersion (1o)
    dll_minor: int = 0                                               # dllVersion (1o)


# —— 新增：增益/响应曲线页缓存（19点） ——
    gain50_19: List[float] = field(default_factory=lambda: [0.0] * 19)
    gain65_19: List[float] = field(default_factory=lambda: [0.0] * 19)
    gain80_19: List[float] = field(default_factory=lambda: [0.0] * 19)
    gainL_19:  List[float] = field(default_factory=lambda: [0.0] * 19)

    resp50_19: List[float] = field(default_factory=lambda: [0.0] * 19)
    resp65_19: List[float] = field(default_factory=lambda: [0.0] * 19)
    resp80_19: List[float] = field(default_factory=lambda: [0.0] * 19)
    respL_19:  List[float] = field(default_factory=lambda: [0.0] * 19)
 
# —— 新增：GainAt_NL2 的增益与响应（19点） ——
    GainAt_NL2_gain: List[float] = field(default_factory=lambda: [0.0] * 19)
    GainAt_NL2_resp: List[float] = field(default_factory=lambda: [0.0] * 19)

# ==============================
# 频点说明（注释）
# - 9点数组顺序：250, 500, 1000, 1500, 2000, 3000, 4000, 6000, 8000 Hz
# - 19点数组顺序：125, 160, 200, 250, 315, 400, 500, 630, 800, 1000,
#                 1250,1600,2000,2500,3150,4000,5000,6300,8000
# ==============================

class NALClient:
    def __init__(self):
        self.ip = ""
        self.port = 8080
        self.path = "/api/nal2/process"
        self.sequence_num = 0
        self.timeout = 3.0
        self.session = requests.Session()
        self.connected = False

    def set_server(self, ip: str, port: int, path: str):
        self.ip = ip.strip()
        self.port = int(port)
        self.path = path.strip() if path.strip() else "/"

    def url(self) -> str:
        path = self.path
        if not path.startswith("/"):
            path = "/" + path
        return f"http://{self.ip}:{self.port}{path}"

    def connect(self) -> bool:
        try:
            with socket.create_connection((self.ip, self.port), timeout=3.0):
                self.connected = True
                return True
        except OSError:
            self.connected = False
            return False

    def disconnect(self):
        self.connected = False

    def post_json(self, body: Dict[str, Any]) -> Dict[str, Any]:
        body = dict(body)
        body["sequence_num"] = self.sequence_num
        self.sequence_num += 1
        headers = {"Content-Type": "application/json"}
        resp = self.session.post(self.url(), headers=headers, data=json.dumps(body), timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

# 通用方法，在其他类中都可以调用
class CommonFunc:
    """HomePageTab 与 FunctionTestTab 共享的小工具集合"""
    @staticmethod
    def set_combo_by_value(combo: QtWidgets.QComboBox, val: int):
        idx = 0
        for i in range(combo.count()):
            if combo.itemData(i) == val:
                idx = i
                break
        combo.setCurrentIndex(idx)

    @staticmethod
    def set_combo_safely(combo: QtWidgets.QComboBox, value: int):
        combo.blockSignals(True)
        try:
            CommonFunc.set_combo_by_value(combo, value)
        finally:
            combo.blockSignals(False)

    @staticmethod
    def mk_ro_text(layout: QtWidgets.QHBoxLayout, label: str) -> QtWidgets.QPlainTextEdit:
        box = QtWidgets.QGroupBox(label)
        layout.addWidget(box)
        v = QtWidgets.QVBoxLayout(box)
        t = QtWidgets.QPlainTextEdit()
        t.setReadOnly(True)
        v.addWidget(t)
        return t

    @staticmethod
    def parse_9(edits: List[QtWidgets.QLineEdit]) -> List[int]:
        arr = []
        for e in edits:
            s = e.text().strip()
            if s == "":
                arr.append(999)
            else:
                try:
                    arr.append(int(float(s)))
                except:
                    arr.append(999)
        if len(arr) != 9:
            raise ValueError("数组长度不是 9")
        return arr

class _WheelFocusFilter(QtCore.QObject):
    # 未聚焦时：把滚轮事件转发给最近的滚动区域（而不是吞掉）
    def eventFilter(self, obj, ev):
        if ev.type() == QtCore.QEvent.Type.Wheel:
            try:
                if not obj.hasFocus():
                    sa = self._find_scroll_area(obj)
                    if sa is not None:
                        vp = sa.viewport()
                        # 位置映射到 viewport 坐标
                        pos_vp = vp.mapFromGlobal(ev.globalPosition().toPoint())
                        new_ev = QtGui.QWheelEvent(
                            QtCore.QPointF(pos_vp),
                            ev.globalPosition(),
                            ev.pixelDelta(),
                            ev.angleDelta(),
                            ev.buttons(),
                            ev.modifiers(),
                            ev.phase(),
                            ev.inverted(),
                            ev.source()
                        )
                        QtWidgets.QApplication.sendEvent(vp, new_ev)
                        return True  # 阻止子控件处理
            except Exception:
                pass
        return super().eventFilter(obj, ev)

    def _find_scroll_area(self, w):
        p = w.parent()
        while p is not None:
            if isinstance(p, QtWidgets.QAbstractScrollArea):
                return p
            p = p.parent()
        return None

class CurveChart(QtWidgets.QWidget):
    def __init__(self, kind: str, parent=None):
        super().__init__(parent)
        # kind: "gain" 或 "resp"
        self.kind = kind
        if kind == "gain":
            self.y_min, self.y_max, self.y_step = -10, 60, 10
            self.y_unit = "dB"
        else:
            self.y_min, self.y_max, self.y_step = 0, 130, 10
            self.y_unit = "dB SPL"
        self.freqs = FREQS_19[:]
        self.series: Dict[str, List[Optional[float]]] = {
            "50": [None]*19,
            "65": [None]*19,
            "80": [None]*19,
            "L":  [None]*19,
            "GA": [None]*19,
        }
        self.colors = {
            "50": QtGui.QColor(115, 76, 158),   # 紫色
            "65": QtGui.QColor(212, 90, 41),   # 橙色
            "80": QtGui.QColor(93, 170, 184),  # 蓝绿色
            "L":  QtGui.QColor(160, 160, 160), # 灰色
            "GA": QtGui.QColor(0, 0, 0),
        }
        self.setMinimumHeight(260)
        self.setAutoFillBackground(True)

    def setFrequencies(self, freqs: List[int]):
        if len(freqs) == 19:
            self.freqs = freqs[:]
            self.update()

    def setSeries(self, name: str, values: List[Optional[float]]):
        if name in self.series and len(values) == 19:
            self.series[name] = values[:]
            self.update()

    def clearAll(self):
        for k in self.series.keys():
            self.series[k] = [None]*19
        self.update()

    def paintEvent(self, e: QtGui.QPaintEvent):
        # 关键修复：显式 begin()/end()，避免活跃 QPainter 遗留
        p = QtGui.QPainter()
        if not p.begin(self):
            return
        try:
            p.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.TextAntialiasing)

            rect = self.rect()
            p.fillRect(rect, QtGui.QColor(255, 255, 255))

            left, right, top, bottom = 60, 20, 20, 46
            plot = QtCore.QRectF(rect.left()+left, rect.top()+top, rect.width()-left-right, rect.height()-top-bottom)

            # 背景网格：纵向 19 条
            vpen = QtGui.QPen(QtGui.QColor(220,220,220))
            p.setPen(vpen)
            xs = self._x_positions(plot)
            for x in xs:
                p.drawLine(QtCore.QPointF(x, plot.top()), QtCore.QPointF(x, plot.bottom()))
            # 横向网格
            hpen = QtGui.QPen(QtGui.QColor(220,220,220))
            p.setPen(hpen)
            for yv in range(self.y_min, self.y_max + 1, self.y_step):
                y = self._y_to_pixel(yv, plot)
                p.drawLine(QtCore.QPointF(plot.left(), y), QtCore.QPointF(plot.right(), y))

            # 坐标标签：Y轴
            p.setPen(QtGui.QColor(60,60,60))
            font = p.font(); font.setPointSize(9); p.setFont(font)
            for yv in range(self.y_min, self.y_max + 1, self.y_step):
                y = self._y_to_pixel(yv, plot)
                p.drawText(QtCore.QRectF(0, y-8, plot.left()-6, 16),
                           QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignVCenter, str(yv))

            # X 轴标签（中心对齐）
            for i, x in enumerate(xs):
                label = str(self.freqs[i]) + (" Hz" if i == len(xs)-1 else "")
                p.drawText(QtCore.QRectF(x-40, plot.bottom()+2, 80, 18),
                           QtCore.Qt.AlignmentFlag.AlignHCenter|QtCore.Qt.AlignmentFlag.AlignTop, label)

            # 边框
            p.setPen(QtGui.QPen(QtGui.QColor(160,160,160)))
            p.drawRect(plot)

            # 曲线
            for key in ["50","65","80","L","GA"]:
                vals = self.series.get(key, [])
                color = self.colors[key]
                self._draw_series(p, plot, xs, vals, color)

            # 图例
            legend_items = [("50dB", self.colors["50"]), ("65dB", self.colors["65"]),
                            ("80dB", self.colors["80"]), ("LdB", self.colors["L"]),
                            ("GainAt", self.colors["GA"])]
            lx, ly = plot.left()+6, plot.top()+6
            for name, col in legend_items:
                p.setPen(QtGui.QPen(col, 2)); p.drawLine(lx, ly+6, lx+16, ly+6)
                p.setPen(QtGui.QPen(QtGui.QColor(50,50,50))); p.drawText(lx+20, ly+10, name)
                ly += 16
        finally:
            p.end()

    def _x_positions(self, plot: QtCore.QRectF) -> List[float]:
        w = plot.width(); n = 19; step = w / (n - 1)
        return [plot.left() + i*step for i in range(n)]

    def _y_to_pixel(self, yval: float, plot: QtCore.QRectF) -> float:
        yval = max(self.y_min, min(self.y_max, yval))
        ratio = (yval - self.y_min) / (self.y_max - self.y_min)
        return plot.bottom() - ratio * plot.height()

    def _draw_series(self, p: QtGui.QPainter, plot: QtCore.QRectF, xs: List[float], vals: List[Optional[float]], color: QtGui.QColor):
        pts = [(xs[i], self._y_to_pixel(vals[i], plot)) for i in range(19) if vals[i] is not None]
        if len(pts) == 0:
            return
        # 画点
        p.setBrush(color); p.setPen(QtGui.QPen(color, 2))
        for x, y in pts:
            p.drawEllipse(QtCore.QPointF(x, y), 2.5, 2.5)
        if len(pts) == 1:
            return
        X = [pt[0] for pt in pts]; Y = [pt[1] for pt in pts]
        path = QtGui.QPainterPath(QtCore.QPointF(X[0], Y[0]))
        beziers = self._monotone_bezier(X, Y)
        p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        for i in range(len(pts)-1):
            c1, c2 = beziers[i]
            path.cubicTo(QtCore.QPointF(c1[0], c1[1]), QtCore.QPointF(c2[0], c2[1]),
                         QtCore.QPointF(X[i+1], Y[i+1]))
        p.drawPath(path)

    def _monotone_bezier(self, X: List[float], Y: List[float]):
        n = len(X)
        dx = [X[i+1]-X[i] for i in range(n-1)]
        dy = [Y[i+1]-Y[i] for i in range(n-1)]
        s = [dy[i]/dx[i] if dx[i] != 0 else 0.0 for i in range(n-1)]
        m = [0.0]*n; m[0] = s[0]; m[-1] = s[-1]
        for i in range(1, n-1):
            m[i] = 0.0 if s[i-1]*s[i] <= 0 else (s[i-1] + s[i]) / 2.0
        # Fritsch-Carlson 限制避免过冲
        for i in range(n-1):
            if s[i] == 0:
                m[i] = m[i+1] = 0.0
            else:
                a = m[i] / s[i]; b = m[i+1] / s[i]; h = a*a + b*b
                if h > 9.0:
                    t = 3.0 / (h**0.5); m[i] = t*a*s[i]; m[i+1] = t*b*s[i]
        # 转为 Bezier 控制点
        beziers = []
        for i in range(n-1):
            x0, y0, x1, y1 = X[i], Y[i], X[i+1], Y[i+1]
            h = x1 - x0
            c1 = (x0 + h/3.0, y0 + m[i] * h/3.0)
            c2 = (x1 - h/3.0, y1 - m[i+1] * h/3.0)
            beziers.append((c1, c2))
        return beziers

# 一、删除原 IOChartWidget 与 IO_Tab 两个顶层类后，新增以下两个类：IOPlotWidget（绘图）与 IO_tab（整页）

class IOPlotWidget(QtWidgets.QWidget):
    """输入/输出曲线页的绘图控件：
       - 坐标系 0..140（X 输入 dB，Y 输出 dB），1:1 正方形靠左；
       - 背景每 10 实线、每 5 虚线；
       - 支持 4 条曲线：IO/IOunl（按模式着色）与 G/Gunl（黑色）；
       - 左上角图例：根据模式显示名称；图例下方显示 Frequency: {FREQS_19[graphFreq]}Hz。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(True)
        self.startLevel = 40
        self.finishLevel = 90
        # 四条曲线数据（顺序：IO(限幅)、IOunl(无限幅)、G(限幅)、Gunl(无限幅)）
        self.series_io: List[float] = []
        self.series_io_unl: List[float] = []
        self.series_g: List[float] = []
        self.series_g_unl: List[float] = []
        # 模式：'RE'（RealEar）/'TCC'/'ES'（EarSim）
        self.mode = 'RE'
        # 颜色（IO/IOunl 用；G/Gunl 始终黑色）
        self.base_color = QtGui.QColor(255, 197, 185)  # 默认皮肤色
        # 频率文字（图例下方）
        self.freq_label = ""

    def setLevels(self, startLevel: int, finishLevel: int):
        self.startLevel = int(startLevel)
        self.finishLevel = int(finishLevel)
        self.update()

    def setMode(self, mode: str):
        """mode: 'RE' / 'TCC' / 'ES'"""
        self.mode = mode.upper().strip()
        self.update()

    def setFrequencyLabelByIndex(self, graph_idx: int):
        try:
            i = int(graph_idx)
            if 0 <= i < len(FREQS_19):
                self.freq_label = f"Frequency: {FREQS_19[i]}Hz"
            else:
                self.freq_label = ""
        except Exception:
            self.freq_label = ""
        self.update()

    def setSeries(self, io: List[float], io_unl: List[float], g: List[float], g_unl: List[float], base_color: QtGui.QColor):
        self.series_io = io[:] if isinstance(io, list) else []
        self.series_io_unl = io_unl[:] if isinstance(io_unl, list) else []
        self.series_g = g[:] if isinstance(g, list) else []
        self.series_g_unl = g_unl[:] if isinstance(g_unl, list) else []
        self.base_color = base_color
        self.update()

    def clearSeries(self):
        self.series_io = []
        self.series_io_unl = []
        self.series_g = []
        self.series_g_unl = []
        self.update()

    def _plot_rect(self, full: QtCore.QRect) -> QtCore.QRectF:
        # 左侧/下侧留出刻度数值空间，保持 1:1，靠左对齐
        left, top, right, bottom = 60, 16, 16, 60
        area = QtCore.QRectF(full.left()+left, full.top()+top, full.width()-left-right, full.height()-top-bottom)
        side = min(area.width(), area.height())
        return QtCore.QRectF(area.left(), area.top(), side, side)

    def _xy_to_px(self, rect: QtCore.QRectF, x_val: float, y_val: float) -> QtCore.QPointF:
        # X: 0..140；Y: -30..140
        y_min, y_max = -30.0, 140.0
        x_clamped = max(0.0, min(140.0, float(x_val)))
        y_clamped = max(y_min, min(y_max, float(y_val)))
        x = rect.left() + (x_clamped / 140.0) * rect.width()
        y = rect.top() + ((y_max - y_clamped) / (y_max - y_min)) * rect.height()
        return QtCore.QPointF(x, y)

    def paintEvent(self, e: QtGui.QPaintEvent):
        p = QtGui.QPainter()
        if not p.begin(self):
            return
        try:
            p.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.TextAntialiasing)
            rect = self.rect()
            p.fillRect(rect, QtGui.QColor(255, 255, 255))

            plot = self._plot_rect(rect)

            # 坐标范围
            y_min, y_max = -30, 140

            # 背景网格
            # 竖线（X：0..140，每 10 实线，每 5 点线）
            p.setPen(QtGui.QPen(QtGui.QColor(230,230,230), 1, QtCore.Qt.PenStyle.SolidLine))
            for k in range(0, 141, 10):
                p.drawLine(self._xy_to_px(plot, k, y_min), self._xy_to_px(plot, k, y_max))
            p.setPen(QtGui.QPen(QtGui.QColor(230,230,230), 1, QtCore.Qt.PenStyle.DotLine))
            for k in range(5, 141, 10):
                p.drawLine(self._xy_to_px(plot, k, y_min), self._xy_to_px(plot, k, y_max))

            # 横线（Y：-30..140，每 10 实线，每 5 点线）
            p.setPen(QtGui.QPen(QtGui.QColor(230,230,230), 1, QtCore.Qt.PenStyle.SolidLine))
            for yv in range(y_min, y_max + 1, 10):
                p.drawLine(self._xy_to_px(plot, 0, yv), self._xy_to_px(plot, 140, yv))
            p.setPen(QtGui.QPen(QtGui.QColor(230,230,230), 1, QtCore.Qt.PenStyle.DotLine))
            for yv in range(y_min + 5, y_max + 1, 10):
                p.drawLine(self._xy_to_px(plot, 0, yv), self._xy_to_px(plot, 140, yv))

            # y=0 的加深背景实线（深灰接近黑色）
            p.setPen(QtGui.QPen(QtGui.QColor(40,40,40), 1))
            p.drawLine(self._xy_to_px(plot, 0, 0), self._xy_to_px(plot, 140, 0))

            # 坐标数字
            p.setPen(QtGui.QColor(80,80,80)); f = p.font(); f.setPointSize(9); p.setFont(f)
            # X 轴标签（0..140）放在底部
            for k in range(0, 141, 10):
                pos = self._xy_to_px(plot, k, y_min)  # 用 y_min 仅取 x 坐标
                p.drawText(QtCore.QRectF(pos.x()-18, plot.bottom()+2, 36, 16),
                           QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignTop, str(k))
            # Y 轴标签（-30..140）
            for yv in range(y_min, y_max + 1, 10):
                pos = self._xy_to_px(plot, 0, yv)
                p.drawText(QtCore.QRectF(plot.left()-44, pos.y()-8, 40, 16),
                           QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter, str(yv))

            # 边框
            p.setPen(QtGui.QPen(QtGui.QColor(160,160,160), 1)); p.drawRect(plot)

            # 曲线绘制（保持原逻辑）
            def draw_series(vals: List[float], color: QtGui.QColor, dashed: bool):
                if not vals: return
                n = max(0, self.finishLevel - self.startLevel) + 1
                if n <= 1: return
                path = QtGui.QPainterPath()
                for i in range(n):
                    x = float(self.startLevel + i)
                    y = float(vals[i]) if i < len(vals) else 0.0
                    pt = self._xy_to_px(plot, x, y)
                    if i == 0: path.moveTo(pt)
                    else: path.lineTo(pt)
                pen = QtGui.QPen(color, 2.0, QtCore.Qt.PenStyle.DashLine if dashed else QtCore.Qt.PenStyle.SolidLine)
                p.setPen(pen); p.setBrush(QtCore.Qt.BrushStyle.NoBrush); p.drawPath(path)

            base_col = self.base_color
            black = QtGui.QColor(0, 0, 0)
            draw_series(self.series_io, base_col, dashed=False)
            draw_series(self.series_io_unl, base_col, dashed=True)
            draw_series(self.series_g, black, dashed=False)
            draw_series(self.series_g_unl, black, dashed=True)

            # 图例与频率文字（保持原逻辑）
            lx, ly = plot.left()+6, plot.top()+6
            if self.mode == 'RE':
                names = [("REIO", False, base_col), ("REIOunl", True, base_col), ("REG", False, black), ("REGunl", True, black)]
            elif self.mode == 'TCC':
                names = [("TccIO", False, base_col), ("TccIOunl", True, base_col), ("TccG", False, black), ("TccGunl", True, black)]
            else:
                names = [("ESIO", False, base_col), ("ESIOunl", True, base_col), ("ESG", False, black), ("ESGunl", True, black)]
            for name, dashed, col in names:
                pen = QtGui.QPen(col, 2.0, QtCore.Qt.PenStyle.DashLine if dashed else QtCore.Qt.PenStyle.SolidLine)
                p.setPen(pen); p.drawLine(QtCore.QPointF(lx, ly+6), QtCore.QPointF(lx+22, ly+6))
                p.setPen(QtGui.QPen(QtGui.QColor(50,50,50))); p.drawText(lx+28, ly+10, name)
                ly += 16
            if self.freq_label:
                p.setPen(QtGui.QPen(QtGui.QColor(50,50,50)))
                p.drawText(lx, ly+10, self.freq_label)

        finally:
            p.end()


class IO_tab(QtWidgets.QWidget):
    """输入/输出曲线页（三栏布局：左参数+按钮+log，中绘图，右结果）"""
    ui_call = QtCore.Signal(object)

    def __init__(self, mainwin: "MainWindow"):
        super().__init__()
        self.win = mainwin
        self._build_ui()
        self.reload_from_cfg()
        self.ui_call.connect(self._on_ui)

    def _post_ui(self, f): self.ui_call.emit(f)
    @QtCore.Slot(object)
    def _on_ui(self, f): 
        try: f()
        except Exception as e: print("IO_tab UI error:", e)

    # ---------- UI ----------
    def _build_ui(self):
        main = QtWidgets.QHBoxLayout(self); main.setContentsMargins(6,6,6,6); main.setSpacing(6)

        # 左侧（固定 420）
        left_box = QtWidgets.QWidget(); left_box.setFixedWidth(420)
        left = QtWidgets.QVBoxLayout(left_box); left.setContentsMargins(8,8,8,8); left.setSpacing(8)

        gb_param = QtWidgets.QGroupBox("参数"); grid = QtWidgets.QGridLayout(gb_param); r = 0
        # 行1：limiting / target
        grid.addWidget(QtWidgets.QLabel("limiting"), r, 0)
        self.cbo_limit = QtWidgets.QComboBox()
        for k, v in [(0,"关(off)"),(1,"宽带(wideband)"),(2,"多通道(multichannel)")]:
            self.cbo_limit.addItem(f"{k} - {v}", k)
        grid.addWidget(self.cbo_limit, r, 1)
        grid.addWidget(QtWidgets.QLabel("target"), r, 2)
        self.cbo_target = QtWidgets.QComboBox()
        for k, v in [(0,"REIG"),(1,"REAG")]:
            self.cbo_target.addItem(f"{k} - {v}", k)
        grid.addWidget(self.cbo_target, r, 3); r += 1

        # 行2：startLevel / finishLevel
        grid.addWidget(QtWidgets.QLabel("startLevel"), r, 0)
        self.ed_start = QtWidgets.QLineEdit(); self.ed_start.setFixedWidth(80); grid.addWidget(self.ed_start, r, 1)
        grid.addWidget(QtWidgets.QLabel("finishLevel"), r, 2)
        self.ed_finish = QtWidgets.QLineEdit(); self.ed_finish.setFixedWidth(80); grid.addWidget(self.ed_finish, r, 3); r += 1

        # 行3：graphFreq + spin
        grid.addWidget(QtWidgets.QLabel("graphFreq"), r, 0)
        self.cbo_graph = QtWidgets.QComboBox()
        for i, f in enumerate(FREQS_19):
            self.cbo_graph.addItem(f"{i} - {f}Hz", i)
        grid.addWidget(self.cbo_graph, r, 1, 1, 2)
        self.spin_graph = QtWidgets.QSpinBox(); self.spin_graph.setRange(0, len(FREQS_19)-1); self.spin_graph.setWrapping(True)
        grid.addWidget(self.spin_graph, r, 3); r += 1
        left.addWidget(gb_param)

        # 按钮区
        row_btn = QtWidgets.QHBoxLayout()
        self.btn_reio  = QtWidgets.QPushButton("获取RealEar IO曲线")
        self.btn_tccio = QtWidgets.QPushButton("获取2cc IO曲线")
        self.btn_esio  = QtWidgets.QPushButton("获取EarSim IO曲线")
        for b in (self.btn_reio, self.btn_tccio, self.btn_esio): row_btn.addWidget(b, 1)
        left.addLayout(row_btn)

        # log 区
        gb_log = QtWidgets.QGroupBox("log"); vlg = QtWidgets.QVBoxLayout(gb_log)
        self.log = QtWidgets.QPlainTextEdit(); self.log.setReadOnly(True)
        self.log.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.NoWrap)
        vlg.addWidget(self.log, 1)
        self.btn_clear_log = QtWidgets.QPushButton("清空log"); vlg.addWidget(self.btn_clear_log)
        left.addWidget(gb_log, 1)

        main.addWidget(left_box)

        # 中间：绘图
        mid = QtWidgets.QVBoxLayout(); mid.setContentsMargins(0,0,0,0); mid.setSpacing(0)
        self.chart = IOPlotWidget()
        mid.addWidget(self.chart, 1)
        main.addLayout(mid, 1)

        # 右侧（固定 420）：结果
        right_box = QtWidgets.QWidget(); right_box.setFixedWidth(420)
        right = QtWidgets.QVBoxLayout(right_box); right.setContentsMargins(8,8,8,8); right.setSpacing(8)
        gb_res = QtWidgets.QGroupBox("结果数据"); vres = QtWidgets.QVBoxLayout(gb_res)
        self.txt_data = QtWidgets.QPlainTextEdit(); self.txt_data.setReadOnly(True)
        self.txt_data.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.NoWrap)
        vres.addWidget(self.txt_data, 1)
        self.btn_clear_plot = QtWidgets.QPushButton("清除"); vres.addWidget(self.btn_clear_plot, 0, QtCore.Qt.AlignmentFlag.AlignRight)
        right.addWidget(gb_res, 1)
        main.addWidget(right_box)

        # 事件
        self.cbo_limit.currentIndexChanged.connect(self._on_params_changed)
        self.cbo_target.currentIndexChanged.connect(self._on_params_changed)
        self.cbo_graph.currentIndexChanged.connect(self._on_graph_combo_changed)
        self.spin_graph.valueChanged.connect(self._on_graph_spin_changed)
        self.ed_start.editingFinished.connect(self._on_levels_changed)
        self.ed_finish.editingFinished.connect(self._on_levels_changed)

        self.btn_reio.clicked.connect(lambda: self._on_fetch("RE"))
        self.btn_tccio.clicked.connect(lambda: self._on_fetch("TCC"))
        self.btn_esio.clicked.connect(lambda: self._on_fetch("ES"))
        self.btn_clear_log.clicked.connect(self.log.clear)
        self.btn_clear_plot.clicked.connect(self._on_clear)

    # ---------- 参数与载入 ----------
    def reload_from_cfg(self):
        c = self.win.cfg

        # limiting / target：程序化设值时阻断信号
        self.cbo_limit.blockSignals(True)
        self.cbo_limit.setCurrentIndex(max(0, min(2, int(c.limiting))))
        self.cbo_limit.blockSignals(False)

        self.cbo_target.blockSignals(True)
        self.cbo_target.setCurrentIndex(max(0, min(1, int(c.target))))
        self.cbo_target.blockSignals(False)

        # start/finish
        self.ed_start.setText(str(int(c.startLevel)))
        self.ed_finish.setText(str(int(c.finishLevel)))

        # graphFreq（已阻断）
        idx = max(0, min(len(FREQS_19)-1, int(c.graphFreq)))
        self.cbo_graph.blockSignals(True); self.cbo_graph.setCurrentIndex(idx); self.cbo_graph.blockSignals(False)
        self.spin_graph.blockSignals(True); self.spin_graph.setValue(idx); self.spin_graph.blockSignals(False)

        # 图表联动
        self.chart.setLevels(int(c.startLevel), int(c.finishLevel))
        self.chart.setFrequencyLabelByIndex(idx)

    def _on_params_changed(self):
        # 用 currentData 读取值；保存
        try:
            self.win.cfg.limiting = int(self.cbo_limit.currentData())
        except Exception:
            self.win.cfg.limiting = int(self.cbo_limit.currentIndex())
        try:
            self.win.cfg.target = int(self.cbo_target.currentData())
        except Exception:
            self.win.cfg.target = int(self.cbo_target.currentIndex())
        self.win.save_config(self.win.config_path)

    def _on_graph_combo_changed(self, _):
        idx = int(self.cbo_graph.currentData()) if self.cbo_graph.currentData() is not None else int(self.cbo_graph.currentIndex())
        self.spin_graph.blockSignals(True); self.spin_graph.setValue(idx); self.spin_graph.blockSignals(False)
        self.win.cfg.graphFreq = idx; self.win.save_config(self.win.config_path)
        self.chart.setFrequencyLabelByIndex(idx)

    def _on_graph_spin_changed(self, val: int):
        if 0 <= val < self.cbo_graph.count():
            self.cbo_graph.blockSignals(True); self.cbo_graph.setCurrentIndex(val); self.cbo_graph.blockSignals(False)
            self.win.cfg.graphFreq = val; self.win.save_config(self.win.config_path)
            self.chart.setFrequencyLabelByIndex(val)

    def _on_levels_changed(self):
        def _to_int(s, d): 
            try: return int(float(str(s).strip()))
            except: return d
        s = _to_int(self.ed_start.text(), self.win.cfg.startLevel)
        f = _to_int(self.ed_finish.text(), self.win.cfg.finishLevel)
        if not (0 <= s <= 140):
            QtWidgets.QMessageBox.warning(self, "提示", "startLevel 需在 0~140 之间"); return
        if not (0 <= f <= 140):
            QtWidgets.QMessageBox.warning(self, "提示", "finishLevel 需在 0~140 之间"); return
        if f < s:
            QtWidgets.QMessageBox.warning(self, "提示", "finishLevel 必须大于等于 startLevel（不做自动修改）"); return
        if (f - s) >= 100:
            QtWidgets.QMessageBox.warning(self, "提示", "finishLevel - startLevel 必须小于 100"); return
        self.win.cfg.startLevel = s; self.win.cfg.finishLevel = f; self.win.save_config(self.win.config_path)
        self.chart.setLevels(s, f)

    # ---------- 清除 ----------
    def _on_clear(self):
        self.chart.clearSeries()
        self.txt_data.clear()

    # ---------- 日志 ----------
    def _log(self, txt: str): self.log.appendPlainText(txt)
    def _sep(self): self._log("--------------------------------------------------------------------\n\n")

    # ---------- 工具 ----------
    def _parse_array(self, outp: Dict[str, Any], keys: List[str]) -> Optional[List[float]]:
        if not isinstance(outp, dict): return None
        for k in keys:
            if k in outp:
                v = outp[k]
                if isinstance(v, list): return [0.0 if x is None else float(x) for x in v]
                if isinstance(v, dict):
                    for subk in ("values","data","arr","array"):
                        if subk in v and isinstance(v[subk], list):
                            return [0.0 if x is None else float(x) for x in v[subk]]
                    for sub in v.values():
                        if isinstance(sub, list):
                            return [0.0 if x is None else float(x) for x in sub]
        return None

    # ---------- 获取并绘制 ----------
    def _on_fetch(self, mode: str):
        if not self.win.client.connected:
            QtWidgets.QMessageBox.warning(self, "提示", "请先连接服务器"); return
        c = self.win.cfg
        sLv, fLv = int(c.startLevel), int(c.finishLevel)
        if fLv < sLv or sLv < 0 or fLv > 140 or (fLv - sLv) >= 100:
            QtWidgets.QMessageBox.warning(self, "提示", "请先修正 startLevel/finishLevel"); return

        # 函数/键/颜色/模式名
        if mode == 'RE':  # RealEar (函数6)
            fn = "RealEarInputOutputCurve_NL2"
            keys = (["REIO"], ["REIOunl"])
            base_color = QtGui.QColor(255, 197, 185)  # 皮肤色
        elif mode == 'TCC':  # 2cc (函数7)
            fn = "TccInputOutputCurve_NL2"
            keys = (["TccIO"], ["TccIOunl"])
            base_color = QtGui.QColor(120, 180, 255)  # 浅蓝
        else:  # ES (函数8)
            fn = "EarSimulatorInputOutputCurve_NL2"
            keys = (["ESIO"], ["ESIOunl"])
            base_color = QtGui.QColor(100, 180, 100)  # 草绿

        # 请求参数
        params = {"AC": c.AC, "BC": c.BC, "graphFreq": int(c.graphFreq), "startLevel": sLv, "finishLevel": fLv,
                  "limiting": c.limiting, "channels": c.channels, "direction": c.direction, "mic": c.mic,
                  "target": c.target, "ACother": c.ACother, "noOfAids": c.noOfAids}
        if mode != 'RE':
            params.update({"aidType": c.aidType, "tubing": c.tubing, "vent": c.vent, "RECDmeasType": c.RECDmeasType})

        def worker():
            req = {"function": fn, "input_parameters": params}
            prev = dict(req); prev["sequence_num"] = self.win.client.sequence_num
            self._post_ui(lambda: self._log("发送:\n" + json.dumps(prev, ensure_ascii=False, indent=2)))
            try:
                resp = self.win.client.post_json(req)
                self._post_ui(lambda: self._log("响应:\n" + json.dumps(resp, ensure_ascii=False, indent=2)))
                self._post_ui(self._sep)
            except Exception as e:
                self._post_ui(lambda: self._log(f"错误: {e}\n")); self._post_ui(self._sep); return

            outp = (resp or {}).get("output_parameters", {}) or {}
            arr_io = self._parse_array(outp, keys[0]) or []
            arr_io_unl = self._parse_array(outp, keys[1]) or []

            # 保存到 config（填充长度）
            def _fill100(x): 
                a = (x or [])[:100]
                return a + [0.0]*(100 - len(a))
            if mode == 'RE':
                self.win.cfg.REIO = _fill100(arr_io); self.win.cfg.REIOunl = _fill100(arr_io_unl)
            elif mode == 'TCC':
                self.win.cfg.TccIO = _fill100(arr_io); self.win.cfg.TccIOunl = _fill100(arr_io_unl)
            else:
                self.win.cfg.ESIO = _fill100(arr_io); self.win.cfg.ESIOunl = _fill100(arr_io_unl)
            self.win.save_config(self.win.config_path)

            # 生成 inLevel / G / Gunl
            n = min(101, max(0, fLv - sLv + 1))
            inLevel = [sLv + i for i in range(n)]
            def _diff(series):
                out = []
                for i in range(n):
                    v = float(series[i]) if i < len(series) else 0.0
                    out.append(v - float(inLevel[i]))
                return out
            g = _diff(arr_io)
            g_unl = _diff(arr_io_unl)

            # 右侧文本（5 列）
            if mode == 'RE':
                col2, col3, col4, col5 = "REIO", "REIOunl", "REG", "REGunl"
            elif mode == 'TCC':
                col2, col3, col4, col5 = "TccIO", "TccIOunl", "TccG", "TccGunl"
            else:
                col2, col3, col4, col5 = "ESIO", "ESIOunl", "ESG", "ESGunl"

            def fill_table():
                lines = [f"{'Level':>5}  {col2:>10}  {col3:>10}  {col4:>10}  {col5:>10}"]
                for i in range(n):
                    lv = inLevel[i]
                    v2 = float(arr_io[i]) if i < len(arr_io) else 0.0
                    v3 = float(arr_io_unl[i]) if i < len(arr_io_unl) else 0.0
                    v4 = float(g[i]) if i < len(g) else 0.0
                    v5 = float(g_unl[i]) if i < len(g_unl) else 0.0
                    lines.append(f"{lv:5d}  {v2:10.1f}  {v3:10.1f}  {v4:10.1f}  {v5:10.1f}")
                self.txt_data.setPlainText("\n".join(lines))

            # 应用到 UI
            def apply_ui():
                self.chart.setMode(mode)
                self.chart.setLevels(sLv, fLv)
                self.chart.setFrequencyLabelByIndex(int(self.win.cfg.graphFreq))
                self.chart.setSeries(arr_io[:n], arr_io_unl[:n], g[:n], g_unl[:n], base_color)
                fill_table()

            self._post_ui(apply_ui)

        threading.Thread(target=worker, daemon=True).start()

class GainRespTab(QtWidgets.QWidget):
    # 新增：跨线程调度到主线程的信号（比 QTimer.singleShot 更稳妥）
    ui_call = QtCore.Signal(object)

    def __init__(self, mainwin: "MainWindow"):
        super().__init__()
        self.win = mainwin
        self._build_ui()
        self._load_from_cfg()
        if hasattr(self.win, "_apply_strict_focus_behavior"):
            self.win._apply_strict_focus_behavior()
        # 连接信号 -> 槽，确保所有 UI 更新都在主线程执行
        self.ui_call.connect(self._run_on_ui)

    # 统一接口：把函数安排到主线程执行
    def _post_ui(self, func):
        self.ui_call.emit(func)

    @QtCore.Slot(object)
    def _run_on_ui(self, func):
        try:
            func()
        except Exception as e:
            print("UI apply error:", e)

    def _build_ui(self):
        main = QtWidgets.QHBoxLayout(self)

        left_box = QtWidgets.QWidget(); left_box.setFixedWidth(420)
        left = QtWidgets.QVBoxLayout(left_box); left.setContentsMargins(8,8,8,8); left.setSpacing(8)

        # 参数区
        gb_param = QtWidgets.QGroupBox("参数"); vparam = QtWidgets.QGridLayout(gb_param)
        vparam.addWidget(QtWidgets.QLabel("宽带声压级 (L)"), 0, 0)
        self.L_edit = QtWidgets.QLineEdit(str(self.win.cfg.L)); self.L_edit.setFixedWidth(120)
        vparam.addWidget(self.L_edit, 0, 1)
        vparam.addWidget(QtWidgets.QLabel("dB SPL"), 0, 2)

        vparam.addWidget(QtWidgets.QLabel("要使用的增益目标(target)"), 1, 0)
        self.target_combo = QtWidgets.QComboBox()
        self.target_combo.addItem("0 - REIG", 0); self.target_combo.addItem("1 - REAG", 1)
        self.target_combo.setCurrentIndex(self.target_combo.findData(self.win.cfg.target))
        self.target_combo.setFixedWidth(120); vparam.addWidget(self.target_combo, 1, 1)

        vparam.addWidget(QtWidgets.QLabel("MPO限制类型(limiting)"), 2, 0)
        self.limit_combo = QtWidgets.QComboBox()
        for k, v in [(0,"关(off)"),(1,"宽带(wideband)"),(2,"多通道(multichannel)")]: self.limit_combo.addItem(f"{k} - {v}", k)
        self.limit_combo.setCurrentIndex(self.limit_combo.findData(self.win.cfg.limiting))
        self.limit_combo.setFixedWidth(120); vparam.addWidget(self.limit_combo, 2, 1)

        vparam.addWidget(QtWidgets.QLabel("MPO类型(type)"), 3, 0)
        self.type_combo = QtWidgets.QComboBox()
        self.type_combo.addItem("0 - RESR", 0); self.type_combo.addItem("1 - SSPL", 1)
        self.type_combo.setCurrentIndex(self.type_combo.findData(self.win.cfg.type))
        self.type_combo.setFixedWidth(120); vparam.addWidget(self.type_combo, 3, 1)
        left.addWidget(gb_param)

        # 按钮区
        btns = QtWidgets.QGridLayout()
        r = 0
        self.btn_get_mpo = QtWidgets.QPushButton("Get MPO"); self.btn_get_cr  = QtWidgets.QPushButton("Get CompressionRetio")
        btns.addWidget(self.btn_get_mpo, r, 0); btns.addWidget(self.btn_get_cr, r, 1); r += 1
        self.btn_get_reig = QtWidgets.QPushButton("Get REIG @ L"); self.btn_get_reag = QtWidgets.QPushButton("Get REAG @ L")
        btns.addWidget(self.btn_get_reig, r, 0); btns.addWidget(self.btn_get_reag, r, 1); r += 1
        self.btn_get_2cc  = QtWidgets.QPushButton("Get 2cc @ L");  self.btn_get_ears = QtWidgets.QPushButton("Get EarSim @ L")
        btns.addWidget(self.btn_get_2cc, r, 0); btns.addWidget(self.btn_get_ears, r, 1)
        left.addLayout(btns)
        
        # 分隔线 + targetType + 获取 GainAt_NL2（批量）
        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        sep.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        left.addWidget(sep)

        row_gainat = QtWidgets.QHBoxLayout()
        row_gainat.addWidget(QtWidgets.QLabel("targetType"))
        self.targetType_combo = QtWidgets.QComboBox()
        for k, v in [(0,"REIG"), (1,"REAG"), (2,"2cc"), (3,"EarSim")]:
            self.targetType_combo.addItem(f"{k} - {v}", k)
        self.targetType_combo.setCurrentIndex(self.targetType_combo.findData(self.win.cfg.targetType))
        row_gainat.addWidget(self.targetType_combo)

        self.btn_gainat = QtWidgets.QPushButton("Get GainAt_NL2(19Freqs)@L")
        row_gainat.addWidget(self.btn_gainat)
        row_gainat.addStretch()
        left.addLayout(row_gainat)

        # 单点 GainAt：freqRequired 下拉 + 按钮 + 返回值
        row_gainat_one = QtWidgets.QHBoxLayout()
        row_gainat_one.addWidget(QtWidgets.QLabel("freqRequired"))
        self.freqRequired_combo = QtWidgets.QComboBox()
        for i, f in enumerate(FREQS_19):
            self.freqRequired_combo.addItem(f"{i} - {f}Hz", i)
        self.freqRequired_combo.setCurrentIndex(self.freqRequired_combo.findData(self.win.cfg.freqRequired))
        row_gainat_one.addWidget(self.freqRequired_combo)

        self.btn_gainat_single = QtWidgets.QPushButton("Get GainAt_NL2@L")
        row_gainat_one.addWidget(self.btn_gainat_single)

        row_gainat_one.addWidget(QtWidgets.QLabel("RetVal"))
        self.gainat_ret_edit = QtWidgets.QLineEdit()
        self.gainat_ret_edit.setFixedWidth(40)
        self.gainat_ret_edit.setReadOnly(True)
        row_gainat_one.addWidget(self.gainat_ret_edit)
        row_gainat_one.addStretch()
        left.addLayout(row_gainat_one)

        # 事件绑定
        self.targetType_combo.currentIndexChanged.connect(self._on_targetType_changed)
        self.freqRequired_combo.currentIndexChanged.connect(self._on_freqRequired_changed)
        self.btn_gainat.clicked.connect(self._on_gain_at)
        self.btn_gainat_single.clicked.connect(self._on_gain_at_single)

        # 日志区
        gb_log = QtWidgets.QGroupBox("日志"); vlog = QtWidgets.QVBoxLayout(gb_log)
        self.log = QtWidgets.QPlainTextEdit(); self.log.setReadOnly(True); vlog.addWidget(self.log, 1)
        self.btn_clear_log = QtWidgets.QPushButton("清空log"); vlog.addWidget(self.btn_clear_log)
        left.addWidget(gb_log, 1)

        main.addWidget(left_box)

        # 右侧：图形 + 数据
        right = QtWidgets.QVBoxLayout(); main.addLayout(right, 1)

        self.subtabs = QtWidgets.QTabWidget(); right.addWidget(self.subtabs, 2)

        # 增益 tab
        self.tab_gain = QtWidgets.QWidget(); vg = QtWidgets.QVBoxLayout(self.tab_gain)
        self.chart_gain = CurveChart("gain"); vg.addWidget(self.chart_gain, 3)
        self.gain_rows = self._build_data_rows(vg, ["1/3-Octave(Hz)","50dB Gain","65dB Gain","80dB Gain","LdB Gain","GainAt_NL2 Gain"])
        self.subtabs.addTab(self.tab_gain, "增益曲线")

        # 响应 tab
        self.tab_resp = QtWidgets.QWidget(); vr = QtWidgets.QVBoxLayout(self.tab_resp)
        self.chart_resp = CurveChart("resp"); vr.addWidget(self.chart_resp, 3)
        self.resp_rows = self._build_data_rows(vr, ["1/3-Octave(Hz)","50dB Resp","65dB Resp","80dB Resp","LdB Resp","GainAt_NL2 Resp"])
        self.subtabs.addTab(self.tab_resp, "响应曲线")

        # 四个“标准曲线”按钮 + “清除全部曲线”按钮
        row_ops = QtWidgets.QHBoxLayout()
        self.btn_std_label = QtWidgets.QLabel("获取标准曲线(Get stardard curve): ")
        row_ops.addWidget(self.btn_std_label)
        self.btn_std_reig = QtWidgets.QPushButton(" REIG ")
        self.btn_std_reag = QtWidgets.QPushButton(" REAG ")
        self.btn_std_2cc  = QtWidgets.QPushButton(" 2cc  ")
        self.btn_std_ears = QtWidgets.QPushButton("EarSim")
        for b in (self.btn_std_reig, self.btn_std_reag, self.btn_std_2cc, self.btn_std_ears):
            row_ops.addWidget(b)
        row_ops.addWidget(QtWidgets.QLabel("        |        "))
        self.btn_clear_curves = QtWidgets.QPushButton("清除全部曲线(Clear all curves)")
        row_ops.addWidget(self.btn_clear_curves)
        self.btn_clear_curves.setFixedWidth(300)
        row_ops.addStretch()#占位弹簧
        right.addLayout(row_ops)

        # 数据显示区：中心频率、MPO、CT、CR
        gb_show = QtWidgets.QGroupBox("数据显示区"); vs = QtWidgets.QVBoxLayout(gb_show)
        self.show_rows = self._build_data_rows(vs, ["1/3-Octave(Hz)","MPO","CT","CR"])
        right.addWidget(gb_show, 0)

        # 事件
        self.L_edit.editingFinished.connect(self._on_params_changed)
        self.target_combo.currentIndexChanged.connect(self._on_params_changed)
        self.limit_combo.currentIndexChanged.connect(self._on_params_changed)
        self.type_combo.currentIndexChanged.connect(self._on_params_changed)
        self.btn_clear_log.clicked.connect(self.log.clear)
        self.btn_clear_curves.clicked.connect(self._on_clear_curves)

        self.btn_get_mpo.clicked.connect(self._on_get_mpo)
        self.btn_get_cr.clicked.connect(self._on_get_cr)
        self.btn_get_reig.clicked.connect(lambda: self._on_get_gain("REIG"))
        self.btn_get_reag.clicked.connect(lambda: self._on_get_gain("REAG"))
        self.btn_get_2cc.clicked.connect(lambda: self._on_get_gain("2cc"))
        self.btn_get_ears.clicked.connect(lambda: self._on_get_gain("EarSim"))

        self.btn_std_reig.clicked.connect(lambda: self._on_std_curves("REIG"))
        self.btn_std_reag.clicked.connect(lambda: self._on_std_curves("REAG"))
        self.btn_std_2cc.clicked.connect(lambda: self._on_std_curves("2cc"))
        self.btn_std_ears.clicked.connect(lambda: self._on_std_curves("EarSim"))
    
    def _build_data_rows(self, parent_layout: QtWidgets.QVBoxLayout, titles: List[str]):
        rows = {}
        # 第一行：通道中心频率（用 QLabel）
        row = QtWidgets.QHBoxLayout()
        lab = QtWidgets.QLabel(titles[0]); lab.setFixedWidth(110)
        row.addWidget(lab)
        edits = []
        for _ in range(19):
            labv = QtWidgets.QLabel("")
            labv.setFixedWidth(40)
            labv.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            edits.append(labv)
            row.addWidget(labv)
        row.addStretch()
        parent_layout.addLayout(row)
        rows[titles[0]] = edits
    
        # 其它行（用 QLineEdit）
        for title in titles[1:]:
            row = QtWidgets.QHBoxLayout()
            lab = QtWidgets.QLabel(title); lab.setFixedWidth(110)
            row.addWidget(lab)
            edits = []
            for _ in range(19):
                e = QtWidgets.QLineEdit()
                e.setFixedWidth(40)
                e.setReadOnly(True)
                edits.append(e)
                row.addWidget(e)
            row.addStretch()
            parent_layout.addLayout(row)
            rows[title] = edits
    
        return rows

    def _log(self, msg: str):
        self.log.appendPlainText(msg)

    def _sep(self):
        self._log("--------------------------------------------------------------------\n")

    def _get_center_freqs(self) -> List[int]:
        cf = self.win.cfg.centerF
        if isinstance(cf, list) and len(cf) == 19 and any(x != 0 for x in cf):
            return [int(x) if x else FREQS_19[i] for i, x in enumerate(cf)]
        return FREQS_19[:]
    
    def _fill_row(self, edits, data, fmt="{:.1f}", int_only: bool=False):
        for i in range(19):
            v = data[i]
            if v is None:
                text = ""
            else:
                try:
                    text = str(int(float(v))) if int_only else fmt.format(float(v))
                except Exception:
                    text = ""
            w = edits[i]
            if isinstance(w, (QtWidgets.QLabel, QtWidgets.QLineEdit)):
                w.setText(text)

    def _on_params_changed(self):
        try: self.win.cfg.L = int(float(self.L_edit.text().strip() or self.win.cfg.L))
        except Exception: pass
        self.win.cfg.target = int(self.target_combo.currentData())
        self.win.cfg.limiting = int(self.limit_combo.currentData())
        self.win.cfg.type = int(self.type_combo.currentData())
        self.win.save_config(self.win.config_path)
    
    def _on_targetType_changed(self):
        try:
            self.win.cfg.targetType = int(self.targetType_combo.currentData())
        except Exception:
            self.win.cfg.targetType = 0
        self.win.save_config(self.win.config_path)
    
    def _on_freqRequired_changed(self):
        try:
            self.win.cfg.freqRequired = int(self.freqRequired_combo.currentData())
        except Exception:
            self.win.cfg.freqRequired = 0
        self.win.save_config(self.win.config_path)

    def _on_clear_curves(self):
        for title in ["50dB Gain","65dB Gain","80dB Gain","LdB Gain","GainAt_NL2 Gain"]:
            self._fill_row(self.gain_rows[title], [None]*19)
        for title in ["50dB Resp","65dB Resp","80dB Resp","LdB Resp","GainAt_NL2 Resp"]:
            self._fill_row(self.resp_rows[title], [None]*19)
        self.chart_gain.clearAll(); self.chart_resp.clearAll()
        z = [0.0]*19
        self.win.cfg.gain50_19 = z[:]; self.win.cfg.gain65_19 = z[:]; self.win.cfg.gain80_19 = z[:]; self.win.cfg.gainL_19 = z[:]; self.win.cfg.GainAt_NL2_gain = z[:]
        self.win.cfg.resp50_19 = z[:]; self.win.cfg.resp65_19 = z[:]; self.win.cfg.resp80_19 = z[:]; self.win.cfg.respL_19 = z[:]; self.win.cfg.GainAt_NL2_resp = z[:]
        self.win.save_config(self.win.config_path)

    def _extract_gainat_return(self, resp: Dict[str, Any]) -> Optional[float]:
        if not isinstance(resp, dict):
            return None
        for k in ("return", "result"):
            if k in resp:
                try:
                    return float(resp[k])
                except Exception:
                    pass
        outp = resp.get("output_parameters", {})
        if isinstance(outp, dict):
            for k in ("gainAt_value", "value", "gain"):
                if k in outp:
                    try:
                        return float(outp[k])
                    except Exception:
                        pass
        return None

    def _on_gain_at(self):
        if not self.win.client.connected:
            QtWidgets.QMessageBox.warning(self, "提示", "请先连接服务器")
            return
        c = self.win.cfg
        try:
            L_now = float(self.L_edit.text().strip() or c.L)
        except Exception:
            L_now = float(c.L)
        tgtType = int(self.targetType_combo.currentData()) if self.targetType_combo.currentData() is not None else int(c.targetType)
    
        ga_gain = (c.GainAt_NL2_gain[:] if isinstance(c.GainAt_NL2_gain, list) and len(c.GainAt_NL2_gain)==19 else [0.0]*19)
        ga_resp = (c.GainAt_NL2_resp[:] if isinstance(c.GainAt_NL2_resp, list) and len(c.GainAt_NL2_resp)==19 else [0.0]*19)
        nmax = min(18, int(c.channels))  # 0..channels
    
        def worker():
            mpo = c.MPO if isinstance(c.MPO, list) and len(c.MPO)==19 else [9999]*19
            for i in range(nmax + 1):
                params = {
                    "freqRequired": i,
                    "targetType": tgtType,
                    "AC": c.AC, "BC": c.BC, "L": int(L_now), "limiting": c.limiting, "channels": c.channels,
                    "direction": c.direction, "mic": c.mic, "ACother": c.ACother, "noOfAids": c.noOfAids,
                    "bandWidth": c.bandWidth, "target": c.target, "aidType": c.aidType,
                    "tubing": c.tubing, "vent": c.vent, "RECDmeasType": c.RECDmeasType
                }
                resp = self._send("GainAt_NL2", params)
                if not resp:
                    continue
                val = self._extract_gainat_return(resp)
                if isinstance(val, (int, float)):
                    ga_gain[i] = float(val)
                    ga_resp[i] = min(float(mpo[i]), ga_gain[i] + L_now)
    
            def apply_ui():
                self.win.cfg.GainAt_NL2_gain = ga_gain[:]
                self.win.cfg.GainAt_NL2_resp = ga_resp[:]
                self.win.save_config(self.win.config_path)
                self._fill_row(self.gain_rows["GainAt_NL2 Gain"], ga_gain)
                self._fill_row(self.resp_rows["GainAt_NL2 Resp"], ga_resp)
                self.chart_gain.setSeries("GA", [None if v==0.0 else v for v in ga_gain])
                self.chart_resp.setSeries("GA", [None if v==0.0 else v for v in ga_resp])
    
            self._post_ui(apply_ui)
    
        threading.Thread(target=worker, daemon=True).start()

    def _on_gain_at_single(self):
        if not self.win.client.connected:
            QtWidgets.QMessageBox.warning(self, "提示", "请先连接服务器")
            return
        c = self.win.cfg
        idx = int(self.freqRequired_combo.currentData()) if self.freqRequired_combo.currentData() is not None else int(c.freqRequired)
        if idx < 0 or idx > 18:
            idx = 0
        try:
            L_now = float(self.L_edit.text().strip() or c.L)
        except Exception:
            L_now = float(c.L)
        tgtType = int(self.targetType_combo.currentData()) if self.targetType_combo.currentData() is not None else int(c.targetType)
    
        params = {
            "freqRequired": idx,
            "targetType": tgtType,
            "AC": c.AC, "BC": c.BC, "L": int(L_now), "limiting": c.limiting, "channels": c.channels,
            "direction": c.direction, "mic": c.mic, "ACother": c.ACother, "noOfAids": c.noOfAids,
            "bandWidth": c.bandWidth, "target": c.target, "aidType": c.aidType,
            "tubing": c.tubing, "vent": c.vent, "RECDmeasType": c.RECDmeasType
        }
    
        def worker():
            resp = self._send("GainAt_NL2", params)
            if not resp:
                return
            val = self._extract_gainat_return(resp)
            if not isinstance(val, (int, float)):
                return
            val = float(val)
    
            ga_gain = (c.GainAt_NL2_gain[:] if isinstance(c.GainAt_NL2_gain, list) and len(c.GainAt_NL2_gain)==19 else [0.0]*19)
            ga_resp = (c.GainAt_NL2_resp[:] if isinstance(c.GainAt_NL2_resp, list) and len(c.GainAt_NL2_resp)==19 else [0.0]*19)
            ga_gain[idx] = val
            mpo = c.MPO if isinstance(c.MPO, list) and len(c.MPO)==19 else [9999]*19
            ga_resp[idx] = min(float(mpo[idx]), val + L_now)
    
            def apply_ui():
                self.win.cfg.GainAt_NL2_gain = ga_gain[:]
                self.win.cfg.GainAt_NL2_resp = ga_resp[:]
                self.win.save_config(self.win.config_path)
                self._fill_row(self.gain_rows["GainAt_NL2 Gain"], ga_gain)
                self._fill_row(self.resp_rows["GainAt_NL2 Resp"], ga_resp)
                self.chart_gain.setSeries("GA", [None if v==0.0 else v for v in ga_gain])
                self.chart_resp.setSeries("GA", [None if v==0.0 else v for v in ga_resp])
                self.gainat_ret_edit.setText(f"{val:.2f}")
    
            self._post_ui(apply_ui)
    
        threading.Thread(target=worker, daemon=True).start()

    # —— 网络封装：后台线程用；日志改由主线程写 ——
    def _send(self, function: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.win.client.connected:
            return None
        req = {"function": function, "input_parameters": params}
        prev = dict(req); prev["sequence_num"] = self.win.client.sequence_num
        self._post_ui(lambda: self._log("发送(Send):\n" + json.dumps(prev, ensure_ascii=False, indent=2)))
        try:
            resp = self.win.client.post_json(req)
            self._post_ui(lambda: self._log("响应(Response):\n" + json.dumps(resp, ensure_ascii=False, indent=2)))
            self._post_ui(self._sep)
            return resp
        except Exception as e:
            self._post_ui(lambda: self._log(f"错误: {e}"))
            self._post_ui(self._sep)
            return None

    def _parse_array(self, outp: Dict[str, Any], keys: List[str]) -> Optional[List[float]]:
        for k in keys:
            if k in outp:
                v = outp[k]
                if isinstance(v, list):
                    return [float(x) if x is not None else 0.0 for x in v]
                if isinstance(v, dict):
                    for subk in ("values", "data", "arr", "array"):
                        if subk in v and isinstance(v[subk], list):
                            return [float(x) if x is not None else 0.0 for x in v[subk]]
                    for sub in v.values():
                        if isinstance(sub, list):
                            return [float(x) if x is not None else 0.0 for x in sub]
        if "output_parameters" in outp and isinstance(outp["output_parameters"], dict):
            return self._parse_array(outp["output_parameters"], keys)
        return None

    def _on_get_mpo(self):
        if not self.win.client.connected:
            QtWidgets.QMessageBox.warning(self, "提示", "请先连接服务器")
            return
        c = self.win.cfg
        params = {"type": c.type, "AC": c.AC, "BC": c.BC, "channels": c.channels, "limiting": c.limiting}
        def worker():
            resp = self._send("getMPO_NL2", params)
            if not resp: return
            outp = resp.get("output_parameters", {})
            arr = self._parse_array(outp, ["MPO"])
            if arr and len(arr) >= 19:
                def apply_ui():
                    self.win.cfg.MPO = arr[:19]
                    self._fill_row(self.show_rows["MPO"], self.win.cfg.MPO)
                    self.win.save_config(self.win.config_path)
                self._post_ui(apply_ui)
        threading.Thread(target=worker, daemon=True).start()

    def _on_get_cr(self):
        if not self.win.client.connected:
            QtWidgets.QMessageBox.warning(self, "提示", "请先连接服务器")
            return
        c = self.win.cfg
        cf = c.centerF if any(x != 0 for x in c.centerF) else FREQS_19[:]
        params = {"channels": c.channels, "centreFreq": cf, "AC": c.AC, "BC": c.BC,
                  "direction": c.direction, "mic": c.mic, "limiting": c.limiting,
                  "ACother": c.ACother, "noOfAids": c.noOfAids}
        def worker():
            resp = self._send("CompressionRatio_NL2", params)
            if not resp: return
            outp = resp.get("output_parameters", {})
            arr = self._parse_array(outp, ["CR"])
            if arr and len(arr) >= 19:
                def apply_ui():
                    self.win.cfg.CR = arr[:19]
                    self._fill_row(self.show_rows["CR"], self.win.cfg.CR)
                    self.win.save_config(self.win.config_path)
                self._post_ui(apply_ui)
        threading.Thread(target=worker, daemon=True).start()

    def _on_get_gain(self, mode: str):
        if not self.win.client.connected:
            QtWidgets.QMessageBox.warning(self, "提示", "请先连接服务器")
            return
        c = self.win.cfg
        try: L_cur = int(float(self.L_edit.text().strip() or c.L))
        except Exception: L_cur = c.L
        if mode == "REIG":
            fn = "RealEarInsertionGain_NL2"
            params = {"AC": c.AC, "BC": c.BC, "L": L_cur, "limiting": c.limiting, "channels": c.channels,
                      "direction": c.direction, "mic": c.mic, "ACother": c.ACother, "noOfAids": c.noOfAids}
            keys = ["REIG","gain","REIG19"]
        elif mode == "REAG":
            fn = "RealEarAidedGain_NL2"
            params = {"AC": c.AC, "BC": c.BC, "L": L_cur, "limiting": c.limiting, "channels": c.channels,
                      "direction": c.direction, "mic": c.mic, "ACother": c.ACother, "noOfAids": c.noOfAids}
            keys = ["REAG","gain","REAG19"]
        elif mode == "2cc":
            fn = "TccCouplerGain_NL2"
            params = {"AC": c.AC, "BC": c.BC, "L": L_cur, "limiting": c.limiting, "channels": c.channels,
                      "direction": c.direction, "mic": c.mic, "target": c.target, "aidType": c.aidType,
                      "ACother": c.ACother, "noOfAids": c.noOfAids, "tubing": c.tubing, "vent": c.vent, "RECDmeasType": c.RECDmeasType}
            keys = ["TccCG", "TccCG19", "gain", "gain19"]
        else:  # EarSim
            fn = "EarSimulatorGain_NL2"
            params = {"AC": c.AC, "BC": c.BC, "L": L_cur, "direction": c.direction, "mic": c.mic,
                      "limiting": c.limiting, "channels": c.channels, "target": c.target, "aidType": c.aidType,
                      "ACother": c.ACother, "noOfAids": c.noOfAids, "tubing": c.tubing, "vent": c.vent, "RECDmeasType": c.RECDmeasType}
            keys = ["ESG", "ESG19", "gain", "gain19"]

        def worker():
            resp = self._send(fn, params)
            if not resp: return
            outp = resp.get("output_parameters", {})
            arr = self._parse_array(outp, keys)
            if not arr: return
            arr = arr[:19]
            def apply_ui():
                self._fill_row(self.gain_rows["LdB Gain"], arr)
                self.chart_gain.setSeries("L", [arr[i] for i in range(19)])
                self.win.cfg.gainL_19 = arr[:]
                mpo = self.win.cfg.MPO if isinstance(self.win.cfg.MPO, list) and len(self.win.cfg.MPO) == 19 else [9999]*19
                resp_vals = [min(mpo[i], float(arr[i]) + float(L_cur)) for i in range(19)]
                self._fill_row(self.resp_rows["LdB Resp"], resp_vals)
                self.chart_resp.setSeries("L", [resp_vals[i] for i in range(19)])
                self.win.cfg.respL_19 = resp_vals[:]
                self.win.save_config(self.win.config_path)
            self._post_ui(apply_ui)
        threading.Thread(target=worker, daemon=True).start()

    def _on_std_curves(self, mode: str):
        if not self.win.client.connected:
            QtWidgets.QMessageBox.warning(self, "提示", "请先连接服务器")
            return
        c = self.win.cfg
        if mode == "REIG":
            fn = "RealEarInsertionGain_NL2"; keys=["REIG","gain","REIG19"]
            def params(Lv): return {"AC": c.AC, "BC": c.BC, "L": Lv, "limiting": c.limiting, "channels": c.channels,
                                    "direction": c.direction, "mic": c.mic, "ACother": c.ACother, "noOfAids": c.noOfAids}
        elif mode == "REAG":
            fn = "RealEarAidedGain_NL2"; keys=["REAG","gain","REAG19"]
            def params(Lv): return {"AC": c.AC, "BC": c.BC, "L": Lv, "limiting": c.limiting, "channels": c.channels,
                                    "direction": c.direction, "mic": c.mic, "ACother": c.ACother, "noOfAids": c.noOfAids}
        elif mode == "2cc":
            fn = "TccCouplerGain_NL2"; keys=["TccCG", "TccCG19", "gain", "gain19"]
            def params(Lv): return {"AC": c.AC, "BC": c.BC, "L": Lv, "limiting": c.limiting, "channels": c.channels,
                                    "direction": c.direction, "mic": c.mic, "target": c.target, "aidType": c.aidType,
                                    "ACother": c.ACother, "noOfAids": c.noOfAids, "tubing": c.tubing, "vent": c.vent, "RECDmeasType": c.RECDmeasType}
        else:
            fn = "EarSimulatorGain_NL2"; keys=["ESG", "ESG19", "gain", "gain19"]
            def params(Lv): return {"AC": c.AC, "BC": c.BC, "L": Lv, "direction": c.direction, "mic": c.mic,
                                    "limiting": c.limiting, "channels": c.channels, "target": c.target, "aidType": c.aidType,
                                    "ACother": c.ACother, "noOfAids": c.noOfAids, "tubing": c.tubing, "vent": c.vent, "RECDmeasType": c.RECDmeasType}

        def worker():
            results = {}
            for Lv, tag in [(50,"50"),(65,"65"),(80,"80")]:
                resp = self._send(fn, params(Lv))
                if not resp: return
                outp = resp.get("output_parameters", {})
                arr = self._parse_array(outp, keys)
                if not arr: return
                results[tag] = arr[:19]

            def apply_ui():
                self._fill_row(self.gain_rows["50dB Gain"], results["50"])
                self._fill_row(self.gain_rows["65dB Gain"], results["65"])
                self._fill_row(self.gain_rows["80dB Gain"], results["80"])
                self.chart_gain.setSeries("50", results["50"])
                self.chart_gain.setSeries("65", results["65"])
                self.chart_gain.setSeries("80", results["80"])
                self.win.cfg.gain50_19 = results["50"][:]
                self.win.cfg.gain65_19 = results["65"][:]
                self.win.cfg.gain80_19 = results["80"][:]

                mpo = self.win.cfg.MPO if isinstance(self.win.cfg.MPO, list) and len(self.win.cfg.MPO) == 19 else [9999]*19
                r50 = [min(mpo[i], results["50"][i] + 50.0) for i in range(19)]
                r65 = [min(mpo[i], results["65"][i] + 65.0) for i in range(19)]
                r80 = [min(mpo[i], results["80"][i] + 80.0) for i in range(19)]
                self._fill_row(self.resp_rows["50dB Resp"], r50)
                self._fill_row(self.resp_rows["65dB Resp"], r65)
                self._fill_row(self.resp_rows["80dB Resp"], r80)
                self.chart_resp.setSeries("50", r50)
                self.chart_resp.setSeries("65", r65)
                self.chart_resp.setSeries("80", r80)
                self.win.cfg.resp50_19 = r50[:]
                self.win.cfg.resp65_19 = r65[:]
                self.win.cfg.resp80_19 = r80[:]
                self.win.save_config(self.win.config_path)

            self._post_ui(apply_ui)
        threading.Thread(target=worker, daemon=True).start()

    def reload_from_cfg(self):
        self._load_from_cfg()

    def _series_from_cfg(self, arr: List[float]) -> List[Optional[float]]:
        # 生成用于绘图的 19 点序列：整条全为 0 -> 返回 [None]*19；否则返回实际数值（包含 0）
        vals: List[float] = []
        for i in range(19):
            try:
                v = float(arr[i])
            except Exception:
                v = 0.0
            vals.append(v)
        if len(vals) != 19 or all(v == 0.0 for v in vals):
            return [None] * 19
        return vals  # 保留 0 值

    def _load_from_cfg(self):
        # 中心频率
        cfs = self._get_center_freqs()
        self.chart_gain.setFrequencies(cfs); self.chart_resp.setFrequencies(cfs)
        self._fill_row(self.gain_rows["1/3-Octave(Hz)"], cfs, int_only=True)
        self._fill_row(self.resp_rows["1/3-Octave(Hz)"], cfs, int_only=True)
        self._fill_row(self.show_rows["1/3-Octave(Hz)"], cfs, int_only=True)

        cfg = self.win.cfg

        # 增益四条
        gain50 = self._series_from_cfg(getattr(cfg, "gain50_19", [0.0]*19))
        gain65 = self._series_from_cfg(getattr(cfg, "gain65_19", [0.0]*19))
        gain80 = self._series_from_cfg(getattr(cfg, "gain80_19", [0.0]*19))
        gainL  = self._series_from_cfg(getattr(cfg, "gainL_19",  [0.0]*19))
        self.chart_gain.setSeries("50", gain50); self._fill_row(self.gain_rows["50dB Gain"], gain50)
        self.chart_gain.setSeries("65", gain65); self._fill_row(self.gain_rows["65dB Gain"], gain65)
        self.chart_gain.setSeries("80", gain80); self._fill_row(self.gain_rows["80dB Gain"], gain80)
        self.chart_gain.setSeries("L",  gainL ); self._fill_row(self.gain_rows["LdB Gain"],  gainL )

        # 响应四条
        resp50 = self._series_from_cfg(getattr(cfg, "resp50_19", [0.0]*19))
        resp65 = self._series_from_cfg(getattr(cfg, "resp65_19", [0.0]*19))
        resp80 = self._series_from_cfg(getattr(cfg, "resp80_19", [0.0]*19))
        respL  = self._series_from_cfg(getattr(cfg, "respL_19",  [0.0]*19))
        self.chart_resp.setSeries("50", resp50); self._fill_row(self.resp_rows["50dB Resp"], resp50)
        self.chart_resp.setSeries("65", resp65); self._fill_row(self.resp_rows["65dB Resp"], resp65)
        self.chart_resp.setSeries("80", resp80); self._fill_row(self.resp_rows["80dB Resp"], resp80)
        self.chart_resp.setSeries("L",  respL ); self._fill_row(self.resp_rows["LdB Resp"],  respL )

        # 显示区
        self._fill_row(self.show_rows["MPO"], cfg.MPO)
        self._fill_row(self.show_rows["CT"],  cfg.CT)
        self._fill_row(self.show_rows["CR"],  cfg.CR)

        # GainAt_NL2 两条（增益/响应）
        ga_gain = getattr(cfg, "GainAt_NL2_gain", [0.0]*19)
        ga_resp = getattr(cfg, "GainAt_NL2_resp", [0.0]*19)
        self._fill_row(self.gain_rows["GainAt_NL2 Gain"], ga_gain)
        self._fill_row(self.resp_rows["GainAt_NL2 Resp"], ga_resp)
        self.chart_gain.setSeries("GA", self._series_from_cfg(ga_gain))
        self.chart_resp.setSeries("GA", self._series_from_cfg(ga_resp))




class HomePageTab(QtWidgets.QWidget):
    """主页 Tab：原 MainWindow._build_main_tab 及其相关事件/方法迁移到此"""
    def __init__(self, mainwin: "MainWindow"):
        super().__init__()
        self.win = mainwin
        self._build_ui()
        # 连接 MainWindow 发出的通用信号到本页槽
        self.win.logReady.connect(self._on_log_ready)
        self.win.seqUpdated.connect(self._on_seq_updated)
        self.win.rrrViewUpdate.connect(self.update_rrr_entries_from_cfg)
        # 初次载入
        self.load_server_from_config()
        self.update_rrr_entries_from_cfg()
        if hasattr(self, "update_ref_entries_from_cfg"):
            self.update_ref_entries_from_cfg()

    # ---------- UI ----------
    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # 顶部连接条
        self._build_top_connect_bar(layout)

        # 中间左右
        hsplit = QtWidgets.QHBoxLayout()
        layout.addLayout(hsplit, 1)

        # 左侧可滚动区
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        left_container = QtWidgets.QWidget()
        scroll.setWidget(left_container)
        hsplit.addWidget(scroll, 2)

        left = QtWidgets.QVBoxLayout(left_container)

        # 工具：下拉创建（带统一宽度与列对齐）
        def mk_combo(parent_layout: QtWidgets.QGridLayout, row: int, col: int,
                     label: str, options: List[tuple], cur_value: int) -> QtWidgets.QComboBox:
            lab = QtWidgets.QLabel(label)
            lab.setFixedWidth(self.win.LABEL_W)
            cb = QtWidgets.QComboBox()
            cb.setFixedWidth(self.win.COMBO_W)
            for k, v in options:
                cb.addItem(f"{k} - {v}", k)
            # set current
            idx = 0
            for i in range(cb.count()):
                if cb.itemData(i) == cur_value:
                    idx = i
                    break
            cb.setCurrentIndex(idx)
            parent_layout.addWidget(lab, row, col*2, QtCore.Qt.AlignmentFlag.AlignLeft)
            parent_layout.addWidget(cb, row, col*2+1, QtCore.Qt.AlignmentFlag.AlignLeft)
            return cb

        # 用户设置（3列2行）
        gb_user = QtWidgets.QGroupBox("用户设置(User settings)")
        left.addWidget(gb_user)
        grid_user = QtWidgets.QGridLayout(gb_user)

        # 行1：成人/儿童(adultChild) | 出生日期(YYYYMMDD) | 性别(gender)
        self.adultChild_combo = mk_combo(grid_user, 0, 0, "成人/儿童(adultChild)",
                                         [(0,"成人(adult)"),(1,"儿童(child)"),(2,"按出生日期计算(calculate from date of birth)")],
                                         self.win.cfg.adultChild)
        lab_dob = QtWidgets.QLabel("出生日期(YYYYMMDD)")
        lab_dob.setFixedWidth(self.win.LABEL_W)
        self.dob_edit = QtWidgets.QLineEdit(str(self.win.cfg.dateOfBirth))
        self.dob_edit.setFixedWidth(self.win.COMBO_W)
        grid_user.addWidget(lab_dob, 0, 1*2, QtCore.Qt.AlignmentFlag.AlignLeft)
        grid_user.addWidget(self.dob_edit, 0, 1*2+1, QtCore.Qt.AlignmentFlag.AlignLeft)

        self.gender_combo = mk_combo(grid_user, 0, 2, "性别(gender)",
                                     [(0,"未知(unknown)"),(1,"男(male)"),(2,"女(female)")],
                                     self.win.cfg.gender)

        # 行2：语言类型(tonal) | 经验(experience) | 压缩速度(compSpeed)
        self.tonal_combo = mk_combo(grid_user, 1, 0, "语言类型(tonal)",
                                    [(0,"非声调(non-tonal)"),(1,"声调(tonal)")],
                                    self.win.cfg.tonal)
        self.experience_combo = mk_combo(grid_user, 1, 1, "经验(experience)",
                                         [(0,"有经验(experienced)"),(1,"新用户(new user)")],
                                         self.win.cfg.experience)
        self.compSpeed_combo = mk_combo(grid_user, 1, 2, "压缩速度(compSpeed)",
                                        [(0,"慢(slow)"),(1,"快(fast)"),(2,"双速(dual)")],
                                        self.win.cfg.compSpeed)

        grid_user.setColumnStretch(6, 1)

        # 听阈
        gb_thr = QtWidgets.QGroupBox("听阈(dB HL) :      250      500      1000      1500      2000     3000     4000     6000     8000 Hz (999 表示未测)")
        left.addWidget(gb_thr)
        v_thr = QtWidgets.QVBoxLayout(gb_thr)
        self.AC_edits = self._mk_array_row(v_thr, "AC[9]:", self.win.cfg.AC)
        self.BC_edits = self._mk_array_row(v_thr, "BC[9]:", self.win.cfg.BC)
        self.ACother_edits = self._mk_array_row(v_thr, "ACother[9]:", self.win.cfg.ACother)

        # 助听器/测量相关（每行3个）
        gb_ha = QtWidgets.QGroupBox("助听器/测量相关(Hearing aids/Measure)")
        left.addWidget(gb_ha)
        grid_ha = QtWidgets.QGridLayout(gb_ha)

        # 行1：channels | bandWidth | selection
        self.channels_combo = mk_combo(grid_ha, 0, 0, "通道数(channels)", [(i,str(i)) for i in range(1,19)], self.win.cfg.channels)
        self.bandWidth_combo = mk_combo(grid_ha, 0, 1, "噪声带宽(bandWidth)", [(0,"宽带(broadband)"),(1,"窄带(narrowband)")], self.win.cfg.bandWidth)
        self.selection_combo_cfg = mk_combo(grid_ha, 0, 2, "CT的增益类型(selection)", [(0,"REIG"),(1,"REAG"),(2,"2cc"),(3,"EarSimulator")], self.win.cfg.selection)

        # 行2：WBCT | aidType | direction
        lab_wbct = QtWidgets.QLabel("宽带压缩阈值(WBCT)")
        lab_wbct.setFixedWidth(self.win.LABEL_W)
        self.WBCT_edit = QtWidgets.QLineEdit(str(self.win.cfg.WBCT))
        self.WBCT_edit.setFixedWidth(self.win.EDIT_W)
        grid_ha.addWidget(lab_wbct, 1, 0*2, QtCore.Qt.AlignmentFlag.AlignLeft)
        grid_ha.addWidget(self.WBCT_edit, 1, 0*2+1, QtCore.Qt.AlignmentFlag.AlignLeft)

        self.aidType_combo = mk_combo(grid_ha, 1, 1, "助听器类型(aidType)", [(0,"CIC"),(1,"ITC"),(2,"ITE"),(3,"BTE")], self.win.cfg.aidType)
        self.direction_combo = mk_combo(grid_ha, 1, 2, "声音方向(direction)", [(0,"0°"),(1,"45°")], self.win.cfg.direction)

        # 行3：mic | limiting | noOfAids
        self.mic_combo = mk_combo(grid_ha, 2, 0, "麦克风参考位置(mic)", [(0,"自由场(undisturbed field)"),(1,"头表面(head surface)")], self.win.cfg.mic)
        self.limiting_combo = mk_combo(grid_ha, 2, 1, "限制类型(limiting)", [(0,"关(off)"),(1,"宽带(wideband)"),(2,"多通道(multichannel)")], self.win.cfg.limiting)
        self.noOfAids_combo = mk_combo(grid_ha, 2, 2, "助听器数量(noOfAids)", [(0,"单侧(unilateral)"),(1,"双侧(bilateral)")], self.win.cfg.noOfAids)

        grid_ha.setColumnStretch(6, 1)

        # 管路/通气/耦合器/插入件
        gb_fit = QtWidgets.QGroupBox("管路/通气/耦合器/插入件(tubing/vent/coupler/earpiece)")
        left.addWidget(gb_fit)
        grid_fit = QtWidgets.QGridLayout(gb_fit)

        # 行1：tubing | vent | coupler
        self.tubing_combo = mk_combo(grid_fit, 0, 0, "导管(tubing)", [(0,"Libby4"),(1,"Libby3"),(2,"#13"),(3,"Thintube"),(4,"RITC"),(5,"None")], self.win.cfg.tubing)
        self.vent_combo = mk_combo(grid_fit, 0, 1, "开口(vent)", [(0,"紧(Tight)"),(1,"堵耳(Occluded)"),(2,"封闭帽(Closed Dome)"),(3,"1mm"),(4,"2mm"),(5,"3mm"),(6,"开放帽(Open Dome)")], self.win.cfg.vent)
        self.coupler_combo = mk_combo(grid_fit, 0, 2, "耦合腔(coupler)", [(0,"HA1"),(1,"HA2")], self.win.cfg.coupler)

        # 行2：fittingDepth | earpiece
        self.fittingDepth_combo = mk_combo(grid_fit, 1, 0, "验配深度(fittingDepth)", [(0,"标准(standard)"),(1,"深(deep)"),(2,"浅(shallow)")], self.win.cfg.fittingDepth)
        self.earpiece_combo = mk_combo(grid_fit, 1, 1, "耳塞(earpiece)", [(0,"泡沫耳塞(Foam Tip)"),(1,"自有耳模(Own Mold)")], self.win.cfg.earpiece)

        grid_fit.setColumnStretch(6, 1)

        # RECD/REDD/REUR类型选择
        gb_types = QtWidgets.QGroupBox("RECD/REDD/REUR类型选择(Type select)")
        left.addWidget(gb_types)
        grid_types = QtWidgets.QGridLayout(gb_types)

        self.RECDmeasType_combo = mk_combo(grid_types, 0, 0, "RECDmeasType", [(0,"预估值(Predicted)"),(1,"实测值(Measured)")], self.win.cfg.RECDmeasType)
        self.REDD_defValues_combo = mk_combo(grid_types, 0, 1, "REDD_defValues", [(0,"预估值(Predicted)"),(1,"用户数据(use client data)")], self.win.cfg.REDD_defValues)
        self.REUR_defValues_combo = mk_combo(grid_types, 0, 2, "REUR_defValues", [(0,"预估值(Predicted)"),(1,"用户数据(use client data)")], self.win.cfg.REUR_defValues)

        grid_types.setColumnStretch(6, 1)

        # RECD/REDD/REUR 读写与显示（含清除按钮）
        gb_rrr = QtWidgets.QGroupBox("RECD/REDD/REUR 读写与显示(Read/Write and display)")
        left.addWidget(gb_rrr)
        v_rrr = QtWidgets.QVBoxLayout(gb_rrr)

        # 19频率表头
        hdr = QtWidgets.QHBoxLayout()
        hdr.addWidget(QtWidgets.QLabel("1/3-Octave(Hz)"))
        for f in FREQS_19:
            lab = QtWidgets.QLabel(str(f)); lab.setFixedWidth(40)
            hdr.addWidget(lab)
        hdr.addStretch(); v_rrr.addLayout(hdr)

        def mk_row19(name: str) -> List[QtWidgets.QLineEdit]:
            row = QtWidgets.QHBoxLayout()
            title = QtWidgets.QLabel(name); title.setFixedWidth(80)
            row.addWidget(title)
            edits = []
            for _ in range(19):
                e = QtWidgets.QLineEdit(); e.setFixedWidth(40)
                edits.append(e); row.addWidget(e)
            row.addStretch(); v_rrr.addLayout(row)
            return edits

        self.RECDh_edits19 = mk_row19("RECDh")
        self.RECDt_edits19 = mk_row19("RECDt")
        self.REDD_edits19 = mk_row19("REDD")
        self.REUR_edits19 = mk_row19("REUR")

        # 9频率表头
        hdr9 = QtWidgets.QHBoxLayout()
        hdr9.addWidget(QtWidgets.QLabel("Standard(Hz)  "))
        for f in FREQS_9:
            lab = QtWidgets.QLabel(str(f)); lab.setFixedWidth(40)
            hdr9.addWidget(lab)
        hdr9.addStretch(); v_rrr.addLayout(hdr9)

        def mk_row9(name: str, with_clear_button: bool=False) -> List[QtWidgets.QLineEdit]:
            row = QtWidgets.QHBoxLayout()
            title = QtWidgets.QLabel(name); title.setFixedWidth(80)
            row.addWidget(title)
            edits: List[QtWidgets.QLineEdit] = []; EDIT_W = 40
            for _ in range(9):
                e = QtWidgets.QLineEdit(); e.setFixedWidth(EDIT_W)
                edits.append(e); row.addWidget(e)
            if with_clear_button:
                SP = row.spacing(); BTN_W = 220
                target_center = 17 * (EDIT_W + SP) + EDIT_W / 2
                right_of_9 = 9 * EDIT_W + 8 * SP
                spacer_w = int(max(0, target_center - (right_of_9 + SP) - SP - BTN_W / 2))
                spacer = QtWidgets.QWidget(); spacer.setFixedWidth(spacer_w)
                spacer.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
                row.addWidget(spacer)
                self.btn_clear_rrr_data = QtWidgets.QPushButton("Clear RECD/REDD/REUR data")
                self.btn_clear_rrr_data.setFixedWidth(BTN_W)
                self.btn_clear_rrr_data.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
                row.addWidget(self.btn_clear_rrr_data)
                self.btn_clear_rrr_data.clicked.connect(self.on_clear_rrr_data)
            row.addStretch(); v_rrr.addLayout(row)
            return edits

        self.RECDh_edits9 = mk_row9("RECDh9")
        self.RECDt_edits9 = mk_row9("RECDt9")
        self.REDD_edits9 = mk_row9("REDD9")
        self.REUR_edits9 = mk_row9("REUR9", with_clear_button=True)

        # 参考数据与修正
        gb_ref = QtWidgets.QGroupBox("参考数据与修正(Reference data and correction)")
        left.addWidget(gb_ref)
        v_ref = QtWidgets.QVBoxLayout(gb_ref)

        # 行1：通道频率(Hz) 19点
        hdr_ref19 = QtWidgets.QHBoxLayout()
        hdr_ref19.addWidget(QtWidgets.QLabel("1/3-Octave(Hz)"))
        for f in FREQS_19:
            lab = QtWidgets.QLabel(str(f)); lab.setFixedWidth(40)
            hdr_ref19.addWidget(lab)
        hdr_ref19.addStretch(); v_ref.addLayout(hdr_ref19)

        def mk_ref_row19(name: str, arr: List[float]) -> tuple[List[QtWidgets.QLineEdit], QtWidgets.QHBoxLayout]:
            row = QtWidgets.QHBoxLayout()
            title = QtWidgets.QLabel(name); title.setFixedWidth(80)
            row.addWidget(title)
            edits: List[QtWidgets.QLineEdit] = []
            for i in range(19):
                e = QtWidgets.QLineEdit(); e.setFixedWidth(40)
                try: v = float(arr[i]) if i < len(arr) else 0.0
                except: v = 0.0
                e.setText(f"{v:.1f}")
                edits.append(e); row.addWidget(e)
            tail_host = QtWidgets.QWidget()
            tail_layout = QtWidgets.QHBoxLayout(tail_host)
            tail_layout.setContentsMargins(0, 0, 0, 0); tail_layout.setSpacing(4)
            row.addWidget(tail_host)
            row.addStretch(); v_ref.addLayout(row)
            return edits, tail_layout

        self.MLE_edits19, self.MLE_tail19 = mk_ref_row19("MLE", self.win.cfg.MLE or [])
        self.MAF_edits19, self.MAF_tail19 = mk_ref_row19("MAF", self.win.cfg.MAF or [])
        self.BWC_edits19, self.BWC_tail19 = mk_ref_row19("BWC", self.win.cfg.BWC or [])
        self.ESCD_edits19, self.ESCD_tail19 = mk_ref_row19("ESCD", self.win.cfg.ESCD or [])
        self.Tubing_edits19, self.Tubing_tail19 = mk_ref_row19("Tubing", self.win.cfg.Tubing or [])
        self.Ventout_edits19, self.Ventout_tail19 = mk_ref_row19("Ventout", self.win.cfg.Ventout or [])

        self.MLE_tail19.addWidget(QtWidgets.QLabel("Microphone Location Effects data @ 1/3 octaves"))
        self.MAF_tail19.addWidget(QtWidgets.QLabel("Minimum Audible Field @ 1/3 octaves"))
        self.BWC_tail19.addWidget(QtWidgets.QLabel("Bandwidth Correction @ 1/3 octaves"))
        self.ESCD_tail19.addWidget(QtWidgets.QLabel("Ear Simulator to Coupler Difference data @ 1/3 octaves"))
        self.Tubing_tail19.addWidget(QtWidgets.QLabel("Tubing corrections @ 1/3 octaves"))
        self.Ventout_tail19.addWidget(QtWidgets.QLabel("Vent corrections @ 1/3 octaves"))

        # 9点参考
        hdr_ref9 = QtWidgets.QHBoxLayout()
        hdr_ref9.addWidget(QtWidgets.QLabel("Standard(Hz)  "))
        for f in FREQS_9:
            lab = QtWidgets.QLabel(str(f)); lab.setFixedWidth(40)
            hdr_ref9.addWidget(lab)
        hdr_ref9.addStretch(); v_ref.addLayout(hdr_ref9)

        def mk_ref_row9(name: str, arr: List[float], with_clear_button: bool=False) -> tuple[List[QtWidgets.QLineEdit], QtWidgets.QHBoxLayout]:
            row = QtWidgets.QHBoxLayout()
            title = QtWidgets.QLabel(name); title.setFixedWidth(80)
            row.addWidget(title)
            edits: List[QtWidgets.QLineEdit] = []; EDIT_W = 40
            for i in range(9):
                e = QtWidgets.QLineEdit(); e.setFixedWidth(EDIT_W)
                try: v = float(arr[i])
                except: v = 0.0
                e.setText(f"{v:.1f}")
                edits.append(e); row.addWidget(e)
            tail_host = QtWidgets.QWidget()
            tail_layout = QtWidgets.QHBoxLayout(tail_host)
            tail_layout.setContentsMargins(0, 0, 0, 0); tail_layout.setSpacing(4)
            row.addWidget(tail_host)
            if with_clear_button:
                SP = row.spacing(); BTN_W = 220
                target_center = 14 * (EDIT_W + SP) + EDIT_W
                right_of_9 = 9 * EDIT_W + 8 * SP
                spacer_w = int(max(0, target_center - (right_of_9 + SP) - SP - BTN_W / 2))
                spacer = QtWidgets.QWidget(); spacer.setFixedWidth(spacer_w)
                spacer.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
                row.addWidget(spacer)
                self.btn_clear_ref_data = QtWidgets.QPushButton("清除参考数据与修正(Clear)")
                self.btn_clear_ref_data.setFixedWidth(BTN_W)
                self.btn_clear_ref_data.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
                row.addWidget(self.btn_clear_ref_data)
                self.btn_clear_ref_data.clicked.connect(self.on_clear_ref_data)
            row.addStretch(); v_ref.addLayout(row)
            return edits, tail_layout

        self.Tubing9_edits9, self.Tubing9_tail9 = mk_ref_row9("Tubing9", self.win.cfg.Tubing9 or [])
        self.Ventout9_edits9, self.Ventout9_tail9 = mk_ref_row9("Ventout9", self.win.cfg.Ventout9 or [], with_clear_button=True)

        self.Tubing9_tail9.addWidget(QtWidgets.QLabel("Tubing corrections @ standard NAL-NL2 frequencies"))
        self.Ventout9_tail9.addWidget(QtWidgets.QLabel("Vent corrections"))

        # 右侧
        right_container = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_container)
        hsplit.addWidget(right_container, 1)

        gb_file = QtWidgets.QGroupBox("Configuration file")
        right_layout.addWidget(gb_file)
        v_file = QtWidgets.QVBoxLayout(gb_file)
        btn_load_cfg = QtWidgets.QPushButton("Load config file")
        btn_saveas_cfg = QtWidgets.QPushButton("Config file save as...")
        v_file.addWidget(btn_load_cfg)
        v_file.addWidget(btn_saveas_cfg)
        # 注意：移到 HomePageTab 内部
        self.lbl_cfg = QtWidgets.QLabel(f"Current file: {os.path.basename(self.win.config_path)}")
        v_file.addWidget(self.lbl_cfg)

        gb_apply = QtWidgets.QGroupBox("Apply to server (Step 1-8)")
        right_layout.addWidget(gb_apply)
        v_apply = QtWidgets.QVBoxLayout(gb_apply)
        btn_apply = QtWidgets.QPushButton("Step 1-8 Initialize")
        v_apply.addWidget(btn_apply)

        grid_apply = QtWidgets.QGridLayout()
        v_apply.addLayout(grid_apply)

        # 顶行：两个“获取”按钮
        self.btn_get_rrr_19 = QtWidgets.QPushButton("Get RECD/REDD/REUR")
        self.btn_get_rrr_9  = QtWidgets.QPushButton("Get RECD9/REDD9/REUR9")
        grid_apply.addWidget(self.btn_get_rrr_19, 0, 0)
        grid_apply.addWidget(self.btn_get_rrr_9,  0, 1)

        # 左列（19点）：三个“设置”按钮
        self.btn_set_recd_19 = QtWidgets.QPushButton("Set RECD")
        self.btn_set_redd_19 = QtWidgets.QPushButton("Set REDD")
        self.btn_set_reur_19 = QtWidgets.QPushButton("Set REUR")
        grid_apply.addWidget(self.btn_set_recd_19, 1, 0)
        grid_apply.addWidget(self.btn_set_redd_19, 2, 0)
        grid_apply.addWidget(self.btn_set_reur_19, 3, 0)

        # 右列（9点）：三个“设置”按钮
        self.btn_set_recd_9 = QtWidgets.QPushButton("Set RECD9")
        self.btn_set_redd_9 = QtWidgets.QPushButton("Set REDD9")
        self.btn_set_reur_9 = QtWidgets.QPushButton("Set REUR9")
        grid_apply.addWidget(self.btn_set_recd_9, 1, 1)
        grid_apply.addWidget(self.btn_set_redd_9, 2, 1)
        grid_apply.addWidget(self.btn_set_reur_9, 3, 1)

        # 获取参考数据与修正
        self.btn_fetch_ref = QtWidgets.QPushButton("获取参考数据与修正(Get reference data and correction)")
        v_apply.addWidget(self.btn_fetch_ref)

        # 日志 + 清除
        self.apply_log = QtWidgets.QTextEdit()
        self.apply_log.setReadOnly(False)
        right_layout.addWidget(self.apply_log, 1)
        btn_clear_log = QtWidgets.QPushButton("Clear log")
        right_layout.addWidget(btn_clear_log)

        # 事件绑定
        btn_load_cfg.clicked.connect(self.on_load_config)
        btn_saveas_cfg.clicked.connect(self.on_saveas_config)
        btn_apply.clicked.connect(self.on_apply_steps)
        btn_clear_log.clicked.connect(lambda: self.apply_log.clear())

        self.btn_get_rrr_19.clicked.connect(self.on_fetch_rrr_19)
        self.btn_get_rrr_9.clicked.connect(self.on_fetch_rrr_9)
        self.btn_set_recd_19.clicked.connect(self.on_set_recd_19)
        self.btn_set_redd_19.clicked.connect(self.on_set_redd_19)
        self.btn_set_reur_19.clicked.connect(self.on_set_reur_19)
        self.btn_set_recd_9.clicked.connect(self.on_set_recd_9)
        self.btn_set_redd_9.clicked.connect(self.on_set_redd_9)
        self.btn_set_reur_9.clicked.connect(self.on_set_reur_9)
        self.btn_fetch_ref.clicked.connect(self.on_fetch_ref_data)

        # 左侧控件更改 -> 自动保存
        for cb, setter in [
            (self.adultChild_combo, lambda v: setattr(self.win.cfg, "adultChild", v)),
            (self.gender_combo, lambda v: setattr(self.win.cfg, "gender", v)),
            (self.tonal_combo, lambda v: setattr(self.win.cfg, "tonal", v)),
            (self.experience_combo, lambda v: setattr(self.win.cfg, "experience", v)),
            (self.compSpeed_combo, lambda v: setattr(self.win.cfg, "compSpeed", v)),
            (self.channels_combo, lambda v: setattr(self.win.cfg, "channels", v)),
            (self.direction_combo, lambda v: setattr(self.win.cfg, "direction", v)),
            (self.bandWidth_combo, lambda v: setattr(self.win.cfg, "bandWidth", v)),
            (self.mic_combo, lambda v: setattr(self.win.cfg, "mic", v)),
            (self.selection_combo_cfg, lambda v: setattr(self.win.cfg, "selection", v)),
            (self.limiting_combo, lambda v: setattr(self.win.cfg, "limiting", v)),
            (self.noOfAids_combo, lambda v: setattr(self.win.cfg, "noOfAids", v)),
            (self.aidType_combo, lambda v: setattr(self.win.cfg, "aidType", v)),
            (self.tubing_combo, lambda v: setattr(self.win.cfg, "tubing", v)),
            (self.fittingDepth_combo, lambda v: setattr(self.win.cfg, "fittingDepth", v)),
            (self.vent_combo, lambda v: setattr(self.win.cfg, "vent", v)),
            (self.earpiece_combo, lambda v: setattr(self.win.cfg, "earpiece", v)),
            (self.coupler_combo, lambda v: setattr(self.win.cfg, "coupler", v)),
            (self.RECDmeasType_combo, lambda v: setattr(self.win.cfg, "RECDmeasType", v)),
            (self.REDD_defValues_combo, lambda v: setattr(self.win.cfg, "REDD_defValues", v)),
            (self.REUR_defValues_combo, lambda v: setattr(self.win.cfg, "REUR_defValues", v)),
        ]:
            cb.currentIndexChanged.connect(lambda _=None, c=cb, s=setter: self._on_combo_changed(c, s))

        self.dob_edit.editingFinished.connect(self.autosave_config)
        self.WBCT_edit.editingFinished.connect(self.autosave_config)
        for e in self.AC_edits + self.BC_edits + self.ACother_edits:
            e.editingFinished.connect(self.autosave_config)

    def _build_top_connect_bar(self, parent_layout: QtWidgets.QLayout):
        top = QtWidgets.QGridLayout()
        parent_layout.addLayout(top)

        self.ip_edit = QtWidgets.QLineEdit(self.win.cfg.server_ip);  self.ip_edit.setFixedWidth(self.win.TOP_IP_W)
        self.port_edit = QtWidgets.QLineEdit(str(self.win.cfg.server_port)); self.port_edit.setFixedWidth(self.win.TOP_PORT_W)
        self.path_edit = QtWidgets.QLineEdit(self.win.cfg.server_path); self.path_edit.setFixedWidth(self.win.TOP_PATH_W)

        row = 0
        lbl = QtWidgets.QLabel("Server: IP"); lbl.setFixedWidth(80)
        top.addWidget(lbl, row, 0)
        top.addWidget(self.ip_edit, row, 1)
        top.addWidget(QtWidgets.QLabel("Port"), row, 2)
        top.addWidget(self.port_edit, row, 3)
        top.addWidget(QtWidgets.QLabel("Path"), row, 4)
        top.addWidget(self.path_edit, row, 5)

        # 顶栏服务器三项的自动保存绑定
        for w in (self.ip_edit, self.port_edit, self.path_edit):
            w.editingFinished.connect(self.save_server_to_cfg)
            try:
                w.returnPressed.connect(self.save_server_to_cfg)
            except Exception:
                pass

        self.btn_connect = QtWidgets.QPushButton("连接(Connect)")
        self.btn_disconnect = QtWidgets.QPushButton("断开(Disconnect)")
        self.btn_disconnect.setEnabled(False)
        self.btn_connect.clicked.connect(self.on_connect)
        self.btn_disconnect.clicked.connect(self.on_disconnect)

        top.addWidget(self.btn_connect, row, 6)
        top.addWidget(self.btn_disconnect, row, 7)

        self.status_label = QtWidgets.QLabel("未连接(Disconnected)")
        self.status_label.setStyleSheet("color: green;")
        self.seq_label = QtWidgets.QLabel("sequence_num: 0")
        top.addWidget(self.status_label, row, 8)
        top.addWidget(self.seq_label, row, 9)

        top.setColumnStretch(10, 1)

    def _mk_array_row(self, parent_layout: QtWidgets.QVBoxLayout, label: str, values: List[float]) -> List[QtWidgets.QLineEdit]:
        roww = QtWidgets.QHBoxLayout()
        lab = QtWidgets.QLabel(label); lab.setFixedWidth(70)
        roww.addWidget(lab)
        edits: List[QtWidgets.QLineEdit] = []
        for v in values:
            e = QtWidgets.QLineEdit(str(v)); e.setFixedWidth(40)
            edits.append(e); roww.addWidget(e)
        roww.addStretch()
        parent_layout.addLayout(roww)
        return edits

    # ---------- “主页”事件/方法（原 MainWindow 同名方法迁移并替换 self 为 self.win） ----------
    def on_connect(self):
        try:
            ip = self.ip_edit.text().strip()
            port = int(self.port_edit.text().strip())
            path = self.path_edit.text().strip()
        except ValueError:
            QtWidgets.QMessageBox.critical(self, "错误(Error)", "端口号不正确(Wrong port number)")
            return
        self.win.client.set_server(ip, port, path)
        ok = self.win.client.connect()
        if ok:
            self.status_label.setText(f"已连接(Connected): {self.win.client.url()}")
            self.btn_connect.setEnabled(False); self.btn_disconnect.setEnabled(True)
            self.win.cfg.server_ip = ip; self.win.cfg.server_port = port; self.win.cfg.server_path = path if path else "/"
            self.win.save_config(self.win.config_path)
        else:
            self.status_label.setText("无法连接（请检查 IP/端口/网络）")

    def on_disconnect(self):
        self.win.client.disconnect()
        self.status_label.setText("未连接(Disconnected)")
        self.btn_connect.setEnabled(True); self.btn_disconnect.setEnabled(False)

    def save_server_to_cfg(self):
        # 同 autosave_config 的写法，单独保存三项
        try:
            self.win.cfg.server_ip = self.ip_edit.text().strip()
            try:
                self.win.cfg.server_port = int(self.port_edit.text().strip())
            except Exception:
                pass  # 端口非数字时不覆盖旧值
            p = self.path_edit.text().strip()
            self.win.cfg.server_path = p if p else "/"
            self.win.save_config(self.win.config_path)
        except Exception as e:
            print("save_server_to_cfg error:", e)

    def _on_log_ready(self, msg: str):
        # MainWindow.logReady -> 主页右侧日志
        try:
            self.apply_log.append(msg)
        except Exception:
            pass

    def _on_seq_updated(self, seq: int):
        # 更新顶部 sequence_num
        try:
            self.seq_label.setText(f"sequence_num: {seq}")
        except Exception:
            pass

    def _on_combo_changed(self, combo: QtWidgets.QComboBox, setter):
        try:
            val = int(combo.currentData())
        except Exception:
            val = 0
        setter(val)
        self.autosave_config()

    def autosave_config(self):
        try:
            # 服务器
            self.win.cfg.server_ip = self.ip_edit.text().strip()
            try: self.win.cfg.server_port = int(self.port_edit.text().strip())
            except: pass
            p = self.path_edit.text().strip()
            self.win.cfg.server_path = p if p else "/"

            # 用户信息
            self.win.cfg.adultChild = int(self.adultChild_combo.currentData())
            try: self.win.cfg.dateOfBirth = int(self.dob_edit.text().strip() or 0)
            except: pass
            self.win.cfg.experience = int(self.experience_combo.currentData())
            self.win.cfg.compSpeed = int(self.compSpeed_combo.currentData())
            self.win.cfg.tonal = int(self.tonal_combo.currentData())
            self.win.cfg.gender = int(self.gender_combo.currentData())

            # 听阈
            self.win.cfg.AC = CommonFunc.parse_9(self.AC_edits)
            self.win.cfg.BC = CommonFunc.parse_9(self.BC_edits)
            self.win.cfg.ACother = CommonFunc.parse_9(self.ACother_edits)

            # 助听器/测量
            ch = int(self.channels_combo.currentData())
            self.win.cfg.channels = 1 if ch < 1 else (18 if ch > 18 else ch)
            self.win.cfg.bandWidth = int(self.bandWidth_combo.currentData())
            self.win.cfg.selection = int(self.selection_combo_cfg.currentData())
            try: self.win.cfg.WBCT = int(self.WBCT_edit.text().strip() or self.win.cfg.WBCT)
            except: pass
            self.win.cfg.aidType = int(self.aidType_combo.currentData())
            self.win.cfg.direction = int(self.direction_combo.currentData())
            self.win.cfg.mic = int(self.mic_combo.currentData())
            self.win.cfg.limiting = int(self.limiting_combo.currentData())
            self.win.cfg.noOfAids = int(self.noOfAids_combo.currentData())

            # 装配/耦合
            self.win.cfg.tubing = int(self.tubing_combo.currentData())
            self.win.cfg.vent = int(self.vent_combo.currentData())
            self.win.cfg.coupler = int(self.coupler_combo.currentData())
            self.win.cfg.fittingDepth = int(self.fittingDepth_combo.currentData())
            self.win.cfg.earpiece = int(self.earpiece_combo.currentData())
            self.win.cfg.RECDmeasType = int(self.RECDmeasType_combo.currentData())
            self.win.cfg.REDD_defValues = int(self.REDD_defValues_combo.currentData())
            self.win.cfg.REUR_defValues = int(self.REUR_defValues_combo.currentData())

            self.win.save_config(self.win.config_path)
        except Exception as e:
            print("autosave_config error:", e)

    def on_fetch_rrr_19(self):
        if not self.win.client.connected:
            QtWidgets.QMessageBox.warning(self, "提示", "请先连接服务器")
            return
        c = self.win.cfg

        def send(function, params):
            req = {"function": function, "input_parameters": params}
            resp = self.win.client.post_json(req)
            self.win.handle_response_update_config(resp)
            self._log_send_resp(req, resp)
            return resp

        def worker():
            try:
                send("GetRECDh_indiv_NL2", {
                    "RECDmeasType": c.RECDmeasType, "dateOfBirth": c.dateOfBirth, "aidType": c.aidType,
                    "tubing": c.tubing, "vent": c.vent, "coupler": c.coupler, "fittingDepth": c.fittingDepth
                })
                send("GetRECDt_indiv_NL2", {
                    "RECDmeasType": c.RECDmeasType, "dateOfBirth": c.dateOfBirth, "aidType": c.aidType,
                    "tubing": c.tubing, "vent": c.vent, "earpiece": c.earpiece, "coupler": c.coupler, "fittingDepth": c.fittingDepth
                })
                send("GetREDDindiv", {"REDD_defValues": c.REDD_defValues})
                send("GetREURindiv", {"REUR_defValues": c.REUR_defValues, "dateOfBirth": c.dateOfBirth,
                                      "direction": c.direction, "mic": c.mic})
            except Exception as e:
                self.win.errorReady.emit(f"获取RECD/REDD/REUR失败: {e}")
        threading.Thread(target=worker, daemon=True).start()


    def on_fetch_rrr_9(self):
        if not self.win.client.connected:
            QtWidgets.QMessageBox.warning(self, "提示", "请先连接服务器")
            return
        c = self.win.cfg

        def send(function, params):
            req = {"function": function, "input_parameters": params}
            resp = self.win.client.post_json(req)
            self.win.handle_response_update_config(resp)
            self._log_send_resp(req, resp)
            return resp

        def worker():
            try:
                send("GetRECDh_indiv9_NL2", {
                    "RECDmeasType": c.RECDmeasType, "dateOfBirth": c.dateOfBirth, "aidType": c.aidType,
                    "tubing": c.tubing, "vent": c.vent, "coupler": c.coupler, "fittingDepth": c.fittingDepth
                })
                send("GetRECDt_indiv9_NL2", {
                    "RECDmeasType": c.RECDmeasType, "dateOfBirth": c.dateOfBirth, "aidType": c.aidType,
                    "tubing": c.tubing, "vent": c.vent, "earpiece": c.earpiece, "coupler": c.coupler, "fittingDepth": c.fittingDepth
                })
                send("GetREDDindiv9", {"REDD_defValues": c.REDD_defValues})
                send("GetREURindiv9", {"REUR_defValues": c.REUR_defValues, "dateOfBirth": c.dateOfBirth,
                                       "direction": c.direction, "mic": c.mic})
            except Exception as e:
                self.win.errorReady.emit(f"获取RECD9/REDD9/REUR9失败: {e}")
        threading.Thread(target=worker, daemon=True).start()

    # ---------- RRR/参考数据/Step1-8（原 MainWindow 上的方法迁移） ----------
    def _log_send_resp(self, req: Dict[str, Any], resp: Dict[str, Any]):
        prev = dict(req); prev["sequence_num"] = self.win.client.sequence_num - 1
        self.win.logReady.emit("发送(Send):\n" + json.dumps(prev, ensure_ascii=False, indent=2))
        self.win.logReady.emit("响应(Response):\n" + json.dumps(resp, ensure_ascii=False, indent=2))
        self.win.logReady.emit("--------------------------------------------------------------------")

    def on_set_recd_19(self):
        if not self.win.client.connected:
            QtWidgets.QMessageBox.warning(self, "提示", "请先连接服务器"); return
        c = self.win.cfg
        def ok_len(arr, n): return isinstance(arr, list) and len(arr) == n
        if not ok_len(c.RECDh, 19) or not ok_len(c.RECDt, 19):
            QtWidgets.QMessageBox.warning(self, "提示", "配置文件中 RECDh/RECDt(19点) 不完整，无法设置"); return
        def send(function, params):
            req = {"function": function, "input_parameters": params}
            resp = self.win.client.post_json(req)
            self.win.handle_response_update_config(resp)
            self._log_send_resp(req, resp)
            return resp
        def worker():
            try:
                send("SetRECDh_indiv_NL2", {"RECDh": c.RECDh})
                send("SetRECDt_indiv_NL2", {"RECDt": c.RECDt})
            except Exception as e:
                self.win.errorReady.emit(f"设置RECD失败: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def on_set_redd_19(self):
        if not self.win.client.connected:
            QtWidgets.QMessageBox.warning(self, "提示", "请先连接服务器"); return
        c = self.win.cfg
        def ok_len(arr, n): return isinstance(arr, list) and len(arr) == n
        if not ok_len(c.REDD, 19):
            QtWidgets.QMessageBox.warning(self, "提示", "配置文件中 REDD(19点) 不完整，无法设置"); return
        def send(function, params):
            req = {"function": function, "input_parameters": params}
            resp = self.win.client.post_json(req)
            self.win.handle_response_update_config(resp)
            self._log_send_resp(req, resp)
            return resp
        def worker():
            try:
                send("SetREDDindiv", {"REDD": c.REDD, "REDD_defValues": c.REDD_defValues})
            except Exception as e:
                self.win.errorReady.emit(f"设置REDD失败: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def on_set_reur_19(self):
        if not self.win.client.connected:
            QtWidgets.QMessageBox.warning(self, "提示", "请先连接服务器"); return
        c = self.win.cfg
        def ok_len(arr, n): return isinstance(arr, list) and len(arr) == n
        if not ok_len(c.REUR, 19):
            QtWidgets.QMessageBox.warning(self, "提示", "配置文件中 REUR(19点) 不完整，无法设置"); return
        def send(function, params):
            req = {"function": function, "input_parameters": params}
            resp = self.win.client.post_json(req)
            self.win.handle_response_update_config(resp)
            self._log_send_resp(req, resp)
            return resp
        def worker():
            try:
                send("SetREURindiv", {
                    "REUR": c.REUR, "REUR_defValues": c.REUR_defValues,
                    "dateOfBirth": c.dateOfBirth, "direction": c.direction, "mic": c.mic
                })
            except Exception as e:
                self.win.errorReady.emit(f"设置REUR失败: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def on_set_recd_9(self):
        if not self.win.client.connected:
            QtWidgets.QMessageBox.warning(self, "提示", "请先连接服务器"); return
        c = self.win.cfg
        def ok_len(arr, n): return isinstance(arr, list) and len(arr) == n
        if not ok_len(c.RECDh9, 9) or not ok_len(c.RECDt9, 9):
            QtWidgets.QMessageBox.warning(self, "提示", "配置文件中 RECDh9/RECDt9(9点) 不完整，无法设置"); return
        def send(function, params):
            req = {"function": function, "input_parameters": params}
            resp = self.win.client.post_json(req)
            self.win.handle_response_update_config(resp)
            self._log_send_resp(req, resp)
            return resp
        def worker():
            try:
                send("SetRECDh_indiv9_NL2", {"RECDh9": c.RECDh9})
                send("SetRECDt_indiv9_NL2", {"RECDt9": c.RECDt9})
            except Exception as e:
                self.win.errorReady.emit(f"设置RECD9失败: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def on_set_redd_9(self):
        if not self.win.client.connected:
            QtWidgets.QMessageBox.warning(self, "提示", "请先连接服务器"); return
        c = self.win.cfg
        def ok_len(arr, n): return isinstance(arr, list) and len(arr) == n
        if not ok_len(c.REDD9, 9):
            QtWidgets.QMessageBox.warning(self, "提示", "配置文件中 REDD9(9点) 不完整，无法设置"); return
        def send(function, params):
            req = {"function": function, "input_parameters": params}
            resp = self.win.client.post_json(req)
            self.win.handle_response_update_config(resp)
            self._log_send_resp(req, resp)
            return resp
        def worker():
            try:
                send("SetREDDindiv9", {"REDD9": c.REDD9, "REDD_defValues": c.REDD_defValues})
            except Exception as e:
                self.win.errorReady.emit(f"设置REDD9失败: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def on_set_reur_9(self):
        if not self.win.client.connected:
            QtWidgets.QMessageBox.warning(self, "提示", "请先连接服务器"); return
        c = self.win.cfg
        def ok_len(arr, n): return isinstance(arr, list) and len(arr) == n
        if not ok_len(c.REUR9, 9):
            QtWidgets.QMessageBox.warning(self, "提示", "配置文件中 REUR9(9点) 不完整，无法设置"); return
        def send(function, params):
            req = {"function": function, "input_parameters": params}
            resp = self.win.client.post_json(req)
            self.win.handle_response_update_config(resp)
            self._log_send_resp(req, resp)
            return resp
        def worker():
            try:
                send("SetREURindiv9", {
                    "REUR9": c.REUR9, "REUR_defValues": c.REUR_defValues,
                    "dateOfBirth": c.dateOfBirth, "direction": c.direction, "mic": c.mic
                })
            except Exception as e:
                self.win.errorReady.emit(f"设置REUR9失败: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def on_clear_rrr_data(self):
        self.win.cfg.RECDh  = [0.0]*19
        self.win.cfg.RECDt  = [0.0]*19
        self.win.cfg.REDD   = [0.0]*19
        self.win.cfg.REUR   = [0.0]*19
        self.win.cfg.RECDh9 = [0.0]*9
        self.win.cfg.RECDt9 = [0.0]*9
        self.win.cfg.REDD9  = [0.0]*9
        self.win.cfg.REUR9  = [0.0]*9
        self.win.save_config(self.win.config_path)
        def ui_clear(edits):
            if isinstance(edits, list):
                for w in edits:
                    try: w.setText("")
                    except Exception: pass
        for row in [self.RECDh_edits19, self.RECDt_edits19, self.REDD_edits19, self.REUR_edits19,
                    self.RECDh_edits9, self.RECDt_edits9, self.REDD_edits9, self.REUR_edits9]:
            ui_clear(row)

    def on_clear_ref_data(self):
        self.win.cfg.MLE     = [0.0]*19
        self.win.cfg.MAF     = [0.0]*19
        self.win.cfg.BWC     = [0.0]*19
        self.win.cfg.ESCD    = [0.0]*19
        self.win.cfg.Tubing  = [0.0]*19
        self.win.cfg.Ventout = [0.0]*19
        self.win.cfg.Tubing9  = [0.0]*9
        self.win.cfg.Ventout9 = [0.0]*9
        self.win.save_config(self.win.config_path)
        def ui_clear(edits):
            if isinstance(edits, list):
                for w in edits:
                    try: w.setText("")
                    except Exception: pass
        for row in [self.MLE_edits19, self.MAF_edits19, self.BWC_edits19, self.ESCD_edits19,
                    self.Tubing_edits19, self.Ventout_edits19, self.Tubing9_edits9, self.Ventout9_edits9]:
            ui_clear(row)

    def update_ref_entries_from_cfg(self):
        def fill(edits: List[QtWidgets.QLineEdit], data: List[float], n: int):
            for i in range(n):
                try:
                    v = float(data[i])
                    edits[i].setText(f"{v:.1f}")
                except Exception:
                    edits[i].setText("")
        if hasattr(self, "MLE_edits19"):
            fill(self.MLE_edits19, self.win.cfg.MLE or [], 19)
            fill(self.MAF_edits19, self.win.cfg.MAF or [], 19)
            fill(self.BWC_edits19, self.win.cfg.BWC or [], 19)
            fill(self.ESCD_edits19, self.win.cfg.ESCD or [], 19)
            fill(self.Tubing_edits19, self.win.cfg.Tubing or [], 19)
            fill(self.Ventout_edits19, self.win.cfg.Ventout or [], 19)
        if hasattr(self, "Tubing9_edits9"):
            fill(self.Tubing9_edits9, self.win.cfg.Tubing9 or [], 9)
            fill(self.Ventout9_edits9, self.win.cfg.Ventout9 or [], 9)
        self.win.save_config(self.win.config_path)

    def on_fetch_ref_data(self):
        if not self.win.client.connected:
            QtWidgets.QMessageBox.warning(self, "提示", "请先连接服务器")
            return
        c = self.win.cfg
        def send(function, params):
            req = {"function": function, "input_parameters": params}
            prev = dict(req); prev["sequence_num"] = self.win.client.sequence_num
            self.win.logReady.emit("发送(Send):\n" + json.dumps(prev, ensure_ascii=False, indent=2))
            resp = self.win.client.post_json(req)
            self.win.logReady.emit("响应(Response):\n" + json.dumps(resp, ensure_ascii=False, indent=2))
            self.win.logReady.emit("--------------------------------------------------------------------\n")
            return resp
        def worker():
            try:
                resp = send("GetMLE", {"aidType": c.aidType, "direction": c.direction, "mic": c.mic})
                outp = (resp or {}).get("output_parameters", {}) or {}
                if "MLE" in outp and isinstance(outp["MLE"], list): self.win.cfg.MLE = outp["MLE"]

                resp = send("ReturnValues_NL2", {})
                outp = (resp or {}).get("output_parameters", {}) or {}
                if "MAF" in outp and isinstance(outp["MAF"], list): self.win.cfg.MAF = outp["MAF"]
                if "BWC" in outp and isinstance(outp["BWC"], list): self.win.cfg.BWC = outp["BWC"]
                if "ESCD" in outp and isinstance(outp["ESCD"], list): self.win.cfg.ESCD = outp["ESCD"]

                resp = send("GetTubing_NL2", {"tubing": c.tubing})
                outp = (resp or {}).get("output_parameters", {}) or {}
                if "Tubing" in outp and isinstance(outp["Tubing"], list): self.win.cfg.Tubing = outp["Tubing"]

                resp = send("GetVentOut_NL2", {"vent": c.vent})
                outp = (resp or {}).get("output_parameters", {}) or {}
                if "Ventout" in outp and isinstance(outp["Ventout"], list): self.win.cfg.Ventout = outp["Ventout"]

                resp = send("GetTubing9_NL2", {"tubing": c.tubing})
                outp = (resp or {}).get("output_parameters", {}) or {}
                if "Tubing9" in outp and isinstance(outp["Tubing9"], list): self.win.cfg.Tubing9 = outp["Tubing9"]

                resp = send("GetVentOut9_NL2", {"vent": c.vent})
                outp = (resp or {}).get("output_parameters", {}) or {}
                if "Ventout9" in outp and isinstance(outp["Ventout9"], list): self.win.cfg.Ventout9 = outp["Ventout9"]

                self.update_ref_entries_from_cfg()
                self.win.save_config(self.win.config_path)
            except Exception as e:
                self.win.errorReady.emit(f"获取参考数据与修正失败: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def on_apply_steps(self):
        if not self.win.client.connected:
            QtWidgets.QMessageBox.warning(self, "提示", "请先连接服务器")
            return
        self.autosave_config()
        self.apply_log.clear()
        threading.Thread(target=self._apply_steps_thread, daemon=True).start()

    def _apply_steps_thread(self):
        def log(msg: str):
            self.win.logReady.emit(msg)
        def send(function: str, params: Dict[str, Any]):
            req = {"function": function, "input_parameters": params}
            prev = dict(req); prev["sequence_num"] = self.win.client.sequence_num
            log("发送(Send):\n" + json.dumps(prev, ensure_ascii=False, indent=2))
            resp = self.win.client.post_json(req)
            log("响应(Response):\n" + json.dumps(resp, ensure_ascii=False, indent=2))
            log("--------------------------------------------------------------------\n")
            self.win.handle_response_update_config(resp)
            return resp
        try:
            c = self.win.cfg
            # 1-5 基本设置
            send("SetAdultChild", {"adultChild": c.adultChild, "dateOfBirth": c.dateOfBirth})
            send("SetExperience", {"experience": c.experience})
            send("SetCompSpeed", {"compSpeed": c.compSpeed})
            send("SetTonalLanguage", {"tonal": c.tonal})
            send("SetGender", {"gender": c.gender})
            # 6 - 分频
            send("CrossOverFrequencies_NL2", {"channels": c.channels, "AC": c.AC, "BC": c.AC})# Step1~9 文档里说明BC NOT USED，使用AC替代
            # 7 - setBWC
            crossOver = self.win.cfg.CFArray if self.win.cfg.CFArray else []
            send("setBWC", {"channels": c.channels, "crossOver": crossOver})
            # 8 - CT
            send("CompressionThreshold_NL2", {
                "bandWidth": c.bandWidth, "selection": c.selection, "WBCT": c.WBCT,
                "aidType": c.aidType, "direction": c.direction, "mic": c.mic, "calcCh": c.calcCh})
            # 20 - CenterFrequencies
            send("CenterFrequencies", {"CFArray": crossOver, "channels": c.channels})
            log("步骤(1-8)完成")
        except Exception as e:
            log(f"执行异常: {e}")
        finally:
            self.win.seqUpdated.emit(self.win.client.sequence_num)
            self.win.outputsChanged.emit()

    # ---------- RECD/REDD/REUR view ----------
    def update_rrr_entries_from_cfg(self):
        def fill(edits: List[QtWidgets.QLineEdit], data: List[float], n: int):
            for i in range(n):
                v = ""
                try:
                    x = data[i]
                    v = "" if x is None else f"{float(x):.1f}"
                except Exception:
                    v = ""
                edits[i].setText(v)
        fill(self.RECDh_edits19, self.win.cfg.RECDh or [], 19)
        fill(self.RECDt_edits19, self.win.cfg.RECDt or [], 19)
        fill(self.REDD_edits19, self.win.cfg.REDD or [], 19)
        fill(self.REUR_edits19, self.win.cfg.REUR or [], 19)
        fill(self.RECDh_edits9, self.win.cfg.RECDh9 or [], 9)
        fill(self.RECDt_edits9, self.win.cfg.RECDt9 or [], 9)
        fill(self.REDD_edits9, self.win.cfg.REDD9 or [], 9)
        fill(self.REUR_edits9, self.win.cfg.REUR9 or [], 9)
        self.win.save_config(self.win.config_path)

    # ---------- Config 文件 ----------
    def on_load_config(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "选择配置文件", "", "JSON (*.json);;All (*.*)")
        if not path: return
        self.win.cfg = self.win.load_config(path)
        self.win.config_path = path
        # 刷新本页服务器与输入区
        self.load_server_from_config()
        for i, v in enumerate(self.win.cfg.AC):
            if i < len(self.AC_edits): self.AC_edits[i].setText(str(v))
        for i, v in enumerate(self.win.cfg.BC):
            if i < len(self.BC_edits): self.BC_edits[i].setText(str(v))
        for i, v in enumerate(self.win.cfg.ACother):
            if i < len(self.ACother_edits): self.ACother_edits[i].setText(str(v))
        # 刷新其他页
        if hasattr(self.win, "func_tab") and hasattr(self.win.func_tab, "reload_from_cfg"):
            self.win.func_tab.reload_from_cfg()
        if hasattr(self.win, "gr_tab"):
            self.win.gr_tab._load_from_cfg()
        self.update_rrr_entries_from_cfg()
        if hasattr(self, "update_ref_entries_from_cfg"):
            self.update_ref_entries_from_cfg()

    def on_saveas_config(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "另存配置为", "", "JSON (*.json);;All (*.*)")
        if not path: return
        self.win.save_config(path)
        self.win.config_path = path
        QtWidgets.QMessageBox.information(self, "提示", "配置已保存")

    def load_server_from_config(self):
        self.ip_edit.setText(self.win.cfg.server_ip)
        self.port_edit.setText(str(self.win.cfg.server_port))
        self.path_edit.setText(self.win.cfg.server_path)

    def reload_from_cfg(self):
        # 切页时从磁盘重载后的刷新
        self.load_server_from_config()
        # 左侧选择项
        CommonFunc.set_combo_safely(self.adultChild_combo, self.win.cfg.adultChild)
        self.dob_edit.setText(str(self.win.cfg.dateOfBirth))
        CommonFunc.set_combo_safely(self.gender_combo, self.win.cfg.gender)
        CommonFunc.set_combo_safely(self.tonal_combo, self.win.cfg.tonal)
        CommonFunc.set_combo_safely(self.experience_combo, self.win.cfg.experience)
        CommonFunc.set_combo_safely(self.compSpeed_combo, self.win.cfg.compSpeed)
        for edits, arr in [(self.AC_edits, self.win.cfg.AC), (self.BC_edits, self.win.cfg.BC), (self.ACother_edits, self.win.cfg.ACother)]:
            for i, e in enumerate(edits):
                try: e.setText(str(arr[i]))
                except Exception: e.setText("")
        CommonFunc.set_combo_safely(self.channels_combo, self.win.cfg.channels)
        CommonFunc.set_combo_safely(self.bandWidth_combo, self.win.cfg.bandWidth)
        CommonFunc.set_combo_safely(self.selection_combo_cfg, self.win.cfg.selection)
        self.WBCT_edit.setText(str(self.win.cfg.WBCT))
        CommonFunc.set_combo_safely(self.aidType_combo, self.win.cfg.aidType)
        CommonFunc.set_combo_safely(self.direction_combo, self.win.cfg.direction)
        CommonFunc.set_combo_safely(self.mic_combo, self.win.cfg.mic)
        CommonFunc.set_combo_safely(self.limiting_combo, self.win.cfg.limiting)
        CommonFunc.set_combo_safely(self.noOfAids_combo, self.win.cfg.noOfAids)
        CommonFunc.set_combo_safely(self.tubing_combo, self.win.cfg.tubing)
        CommonFunc.set_combo_safely(self.vent_combo, self.win.cfg.vent)
        CommonFunc.set_combo_safely(self.coupler_combo, self.win.cfg.coupler)
        CommonFunc.set_combo_safely(self.fittingDepth_combo, self.win.cfg.fittingDepth)
        CommonFunc.set_combo_safely(self.earpiece_combo, self.win.cfg.earpiece)
        CommonFunc.set_combo_safely(self.RECDmeasType_combo, self.win.cfg.RECDmeasType)
        CommonFunc.set_combo_safely(self.REDD_defValues_combo, self.win.cfg.REDD_defValues)
        CommonFunc.set_combo_safely(self.REUR_defValues_combo, self.win.cfg.REUR_defValues)
        self.update_rrr_entries_from_cfg()
        if hasattr(self, "update_ref_entries_from_cfg"):
            self.update_ref_entries_from_cfg()

class FunctionTestTab(QtWidgets.QWidget):
    """函数测试 Tab：原 MainWindow._build_functions_test_tab 及相关事件/方法迁移到此"""
    def __init__(self, mainwin: "MainWindow"):
        super().__init__()
        self.win = mainwin
        self.templates: List[Dict[str, Any]] = []
        self._build_ui()
        # 连接 MainWindow 的通用信号到本页槽
        self.win.respReady.connect(self._on_resp_ready)
        self.win.errorReady.connect(self._on_error_ready)
        self.win.seqUpdated.connect(self._on_seq_updated)
        self.win.reqPreviewReady.connect(self._on_req_preview_ready)
        # 初次加载模板与只读输出
        self.load_templates()
        self.refresh_outputs_view()

    def _build_ui(self, ):
        layout = QtWidgets.QVBoxLayout(self)

        # 参数
        gb_param = QtWidgets.QGroupBox("参数")
        layout.addWidget(gb_param)
        v_param = QtWidgets.QVBoxLayout(gb_param)

        line1 = QtWidgets.QHBoxLayout()
        v_param.addLayout(line1)
        labL = QtWidgets.QLabel("宽带输入电平(L)"); labL.setFixedWidth(self.win.LABEL_W)
        self.L_edit = QtWidgets.QLineEdit(str(self.win.cfg.L)); self.L_edit.setFixedWidth(self.win.EDIT_W)
        line1.addWidget(labL)
        line1.addWidget(self.L_edit)
        line1.addWidget(QtWidgets.QLabel("dB SPL"))
        line1.addSpacing(20)

        labSel = QtWidgets.QLabel("CT的增益类型(selection)"); labSel.setFixedWidth(self.win.LABEL_W)
        self.selection_combo = QtWidgets.QComboBox(); self.selection_combo.setFixedWidth(self.win.COMBO_W)
        for k,v in [(0,"REIG"),(1,"REAG"),(2,"2ccCoupler"),(3,"EarSimulator")]:
            self.selection_combo.addItem(f"{k} - {v}", k)
        CommonFunc.set_combo_by_value(self.selection_combo, self.win.cfg.selection)
        line1.addWidget(labSel)
        line1.addWidget(self.selection_combo)

        labTgt = QtWidgets.QLabel("要使用的增益目标(target)"); labTgt.setFixedWidth(self.win.LABEL_W)
        self.target_combo = QtWidgets.QComboBox(); self.target_combo.setFixedWidth(self.win.COMBO_W)
        for k,v in [(0,"REIG"),(1,"REAG")]:
            self.target_combo.addItem(f"{k} - {v}", k)
        CommonFunc.set_combo_by_value(self.target_combo, self.win.cfg.target)
        line1.addWidget(labTgt)
        line1.addWidget(self.target_combo)
        line1.addStretch()

        line2 = QtWidgets.QHBoxLayout()
        v_param.addLayout(line2)
        labIOcurve = QtWidgets.QLabel("输入/输出曲线(函数6/7/8)：")
        line2.addWidget(labIOcurve); labIOcurve.setFixedWidth(180)
        labGF = QtWidgets.QLabel("绘制频率(graphFreq)"); labGF.setFixedWidth(self.win.LABEL_W)
        self.graphFreq_combo = QtWidgets.QComboBox(); self.graphFreq_combo.setFixedWidth(self.win.COMBO_W)
        for i, f in enumerate(["125","160","200","250","315","400","500","630","800","1000",
                               "1250","1600","2000","2500","3150","4000","5000","6300","8000"]):
            self.graphFreq_combo.addItem(f"{i} - {f}Hz", i)
        CommonFunc.set_combo_by_value(self.graphFreq_combo, self.win.cfg.graphFreq)
        line2.addWidget(labGF)
        line2.addWidget(self.graphFreq_combo)

        for cap, attr in [("startLevel","startLevel"), ("finishLevel","finishLevel")]:
            lab = QtWidgets.QLabel(cap); lab.setFixedWidth(70)
            edit = QtWidgets.QLineEdit(str(getattr(self.win.cfg, attr))); edit.setFixedWidth(40)
            setattr(self, f"{attr}_edit", edit)
            line2.addWidget(lab)
            line2.addWidget(edit)
            line2.addWidget(QtWidgets.QLabel("dB SPL"))

        line3 = QtWidgets.QHBoxLayout()
        v_param.addLayout(line3)
        labType = QtWidgets.QLabel("所需MPO类型(type)"); labType.setFixedWidth(self.win.LABEL_W)
        self.type_combo = QtWidgets.QComboBox(); self.type_combo.setFixedWidth(self.win.COMBO_W)
        for k,v in [(0,"RESR"),(1,"SSPL")]:
            self.type_combo.addItem(f"{k} - {v}", k)
        CommonFunc.set_combo_by_value(self.type_combo, self.win.cfg.type)
        line3.addWidget(labType); line3.addWidget(self.type_combo)

        labS = QtWidgets.QLabel("语音电平(s)"); labS.setFixedWidth(self.win.LABEL_W)
        self.s_combo = QtWidgets.QComboBox(); self.s_combo.setFixedWidth(self.win.COMBO_W)
        for i, txt in enumerate(["55dB","60dB","65dB","70dB","75dB","72dB","69dB"]):
            self.s_combo.addItem(f"{i} - {txt}", i)
        CommonFunc.set_combo_by_value(self.s_combo, self.win.cfg.s)
        line3.addWidget(labS); line3.addWidget(self.s_combo)
        line3.addStretch()

        # 只读显示（缓存输出）
        gb_out = QtWidgets.QGroupBox("派生/缓存输出（自动随响应更新；可复制）")
        layout.addWidget(gb_out)
        h_out = QtWidgets.QHBoxLayout(gb_out)
        self.txt_CFArray = CommonFunc.mk_ro_text(h_out, "CFArray")
        self.txt_FreqInCh = CommonFunc.mk_ro_text(h_out, "FreqInCh")
        self.txt_CT = CommonFunc.mk_ro_text(h_out, "CT")
        self.txt_CR = CommonFunc.mk_ro_text(h_out, "CR")

        # 模板/请求/响应
        mid = QtWidgets.QVBoxLayout()
        layout.addLayout(mid, 1)

        bar = QtWidgets.QHBoxLayout()
        mid.addLayout(bar)
        bar.addWidget(QtWidgets.QLabel("单条函数调用"))
        self.tmpl_combo = QtWidgets.QComboBox(); self.tmpl_combo.setFixedWidth(self.win.COMBO_W + 120)
        bar.addWidget(self.tmpl_combo)
        btn_insert_tmpl = QtWidgets.QPushButton("插入模板（从配置取值）")
        btn_reload_tmpl = QtWidgets.QPushButton("重载模板")
        bar.addWidget(btn_insert_tmpl)
        bar.addWidget(btn_reload_tmpl)
        bar.addStretch()

        panes = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        mid.addWidget(panes, 1)

        req_box = QtWidgets.QGroupBox("请求 JSON（可手动编辑）")
        resp_box = QtWidgets.QGroupBox("响应 JSON（可选择复制）")
        panes.addWidget(req_box)
        panes.addWidget(resp_box)

        self.req_text = QtWidgets.QPlainTextEdit()
        self.resp_text = QtWidgets.QPlainTextEdit()
        v_req = QtWidgets.QVBoxLayout(req_box); v_req.addWidget(self.req_text)
        v_resp = QtWidgets.QVBoxLayout(resp_box); v_resp.addWidget(self.resp_text)

        # 初始请求内容
        self.req_text.setPlainText(json.dumps({
            "function": "SetAdultChild",
            "input_parameters": {"adultChild": self.win.cfg.adultChild, "dateOfBirth": self.win.cfg.dateOfBirth}
        }, ensure_ascii=False, indent=2))

        btm = QtWidgets.QHBoxLayout()
        layout.addLayout(btm)
        btn_send = QtWidgets.QPushButton("发送")
        btn_clear_req = QtWidgets.QPushButton("清空请求")
        btn_clear_resp = QtWidgets.QPushButton("清空响应")
        btm.addWidget(btn_send)
        btm.addWidget(btn_clear_req)
        btm.addWidget(btn_clear_resp)
        btm.addStretch()

        # 事件
        btn_insert_tmpl.clicked.connect(self.on_insert_template)
        btn_reload_tmpl.clicked.connect(self.load_templates)
        btn_send.clicked.connect(self.on_send)
        btn_clear_req.clicked.connect(lambda: self.req_text.setPlainText(""))
        btn_clear_resp.clicked.connect(lambda: self.resp_text.setPlainText(""))

        # 参数变更 -> 保存
        self.L_edit.editingFinished.connect(self.save_home_params_to_cfg)
        self.selection_combo.currentIndexChanged.connect(self._on_sel_change)
        self.target_combo.currentIndexChanged.connect(self._on_tgt_change)
        self.graphFreq_combo.currentIndexChanged.connect(self._on_graphFreq_change)
        self.type_combo.currentIndexChanged.connect(self._on_type_change)
        self.s_combo.currentIndexChanged.connect(self._on_s_change)
        self.startLevel_edit.editingFinished.connect(self.save_home_params_to_cfg)
        self.finishLevel_edit.editingFinished.connect(self.save_home_params_to_cfg)

    # ---------- templates ----------
    def load_templates(self):
        try:
            with open(DEFAULT_TEMPLATES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.templates = data.get("templates", [])
            self.tmpl_combo.clear()
            for t in self.templates:
                self.tmpl_combo.addItem(t["label"], t)
            if self.tmpl_combo.count() > 0:
                self.tmpl_combo.setCurrentIndex(0)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "错误", f"加载模板失败: {e}")
            self.templates = []

    def on_insert_template(self):
        if self.tmpl_combo.count() == 0:
            return
        t = self.tmpl_combo.currentData()
        function = t.get("function")
        params = t.get("params", [])
        input_params = self.build_input_from_config(params)
        req = {"function": function, "input_parameters": input_params}
        self.req_text.setPlainText(json.dumps(req, ensure_ascii=False, indent=2))

    def build_input_from_config(self, params: List[str]) -> Dict[str, Any]:
        cfgd = asdict(self.win.cfg)
        out: Dict[str, Any] = {}
        for p in params:
            if p == "crossOver":
                out[p] = cfgd.get("CFArray", [])
            elif p == "centreFreq":
                out[p] = cfgd.get("centerF", [])
            else:
                out[p] = cfgd.get(p)
        return out

    # ---------- send ----------
    def on_send(self):
        if not self.win.client.connected:
            QtWidgets.QMessageBox.warning(self, "提示", "请先连接服务器")
            return
        raw = self.req_text.toPlainText().strip()
        try:
            req = json.loads(raw)
        except json.JSONDecodeError as e:
            QtWidgets.QMessageBox.critical(self, "错误", f"请求 JSON 语法错误:\n{e}")
            return
        if "function" not in req or "input_parameters" not in req:
            QtWidgets.QMessageBox.critical(self, "错误", "JSON 必须包含 function 和 input_parameters 字段")
            return
        threading.Thread(target=self._send_thread, args=(req,), daemon=True).start()

    def _send_thread(self, req: Dict[str, Any]):
        try:
            preview = dict(req); preview["sequence_num"] = self.win.client.sequence_num
            self.win.reqPreviewReady.emit(json.dumps(preview, ensure_ascii=False, indent=2))
            resp = self.win.client.post_json(req)
            self.win.handle_response_update_config(resp)
            self.win.respReady.emit(json.dumps(resp, ensure_ascii=False, indent=2))
        except RequestException as e:
            self.win.errorReady.emit(f"网络错误: {e}")
        except Exception as e:
            self.win.errorReady.emit(f"异常: {e}")
        finally:
            self.win.seqUpdated.emit(self.win.client.sequence_num)

    @QtCore.Slot(str)
    def _on_resp_ready(self, payload: str):
        self.resp_text.setPlainText(payload)

    @QtCore.Slot(str)
    def _on_error_ready(self, msg: str):
        QtWidgets.QMessageBox.critical(self, "错误", msg)

    @QtCore.Slot(int)
    def _on_seq_updated(self, seq: int):
        # 函数测试页不显示 seq；若需要可加 UI
        pass

    @QtCore.Slot(str)
    def _on_req_preview_ready(self, s: str):
        self.req_text.setPlainText(s)

    # ---------- outputs view ----------
    def refresh_outputs_view(self):
        def set_ro_text(widget: QtWidgets.QPlainTextEdit, data):
            widget.setPlainText(json.dumps(data, ensure_ascii=False))
        set_ro_text(self.txt_CFArray, self.win.cfg.CFArray)
        set_ro_text(self.txt_FreqInCh, self.win.cfg.FreqInCh)
        set_ro_text(self.txt_CT, self.win.cfg.CT)
        set_ro_text(self.txt_CR, self.win.cfg.CR)

    # ---------- 保存与参数变更 ----------
    def save_home_params_to_cfg(self):
        try:
            self.win.cfg.L = int(float(self.L_edit.text().strip() or self.win.cfg.L))
            self.win.cfg.selection = int(self.selection_combo.currentData())
            self.win.cfg.target = int(self.target_combo.currentData())
            self.win.cfg.graphFreq = int(self.graphFreq_combo.currentData())
            self.win.cfg.startLevel = int(float(self.startLevel_edit.text().strip() or self.win.cfg.startLevel))
            self.win.cfg.finishLevel = int(float(self.finishLevel_edit.text().strip() or self.win.cfg.finishLevel))
            self.win.cfg.type = int(self.type_combo.currentData())
            self.win.cfg.s = int(self.s_combo.currentData())
            self.win.save_config(self.win.config_path)
        except Exception as e:
            print("save_home_params_to_cfg:", e)

    def _on_sel_change(self):
        self.win.cfg.selection = int(self.selection_combo.currentData())
        self.save_home_params_to_cfg()

    def _on_tgt_change(self):
        self.win.cfg.target = int(self.target_combo.currentData())
        self.save_home_params_to_cfg()

    def _on_graphFreq_change(self):
        self.win.cfg.graphFreq = int(self.graphFreq_combo.currentData())
        self.save_home_params_to_cfg()

    def _on_type_change(self):
        self.win.cfg.type = int(self.type_combo.currentData())
        self.save_home_params_to_cfg()

    def _on_s_change(self):
        self.win.cfg.s = int(self.s_combo.currentData())
        self.save_home_params_to_cfg()

    def reload_from_cfg(self):
        # 切页时从磁盘重载后的刷新
        c = self.win.cfg
        self.L_edit.setText(str(c.L))
        CommonFunc.set_combo_safely(self.selection_combo, c.selection)
        CommonFunc.set_combo_safely(self.target_combo, c.target)
        CommonFunc.set_combo_safely(self.graphFreq_combo, c.graphFreq)
        self.startLevel_edit.setText(str(c.startLevel))
        self.finishLevel_edit.setText(str(c.finishLevel))
        CommonFunc.set_combo_safely(self.type_combo, c.type)
        CommonFunc.set_combo_safely(self.s_combo, c.s)
        self.refresh_outputs_view()

class MainWindow(QtWidgets.QMainWindow):
    respReady = QtCore.Signal(str)
    errorReady = QtCore.Signal(str)
    logReady = QtCore.Signal(str)
    seqUpdated = QtCore.Signal(int)
    reqPreviewReady = QtCore.Signal(str)
    outputsChanged = QtCore.Signal()
    rrrViewUpdate = QtCore.Signal()

    # 统一控件宽度（用于列对齐）（供 HomePageTab / FunctionTestTab 读取）
    LABEL_W = 130
    COMBO_W = 150
    EDIT_W = 120
    TOP_IP_W = 150
    TOP_PORT_W = 80
    TOP_PATH_W = 220

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME}  {APP_VERSION}")
        self.resize(1600, 960)

        icon_path = "resource/icon.png"
        if os.path.exists(icon_path):
            self.setWindowIcon(QtGui.QIcon(icon_path))

        ensure_templates_file(DEFAULT_TEMPLATES_FILE)

        self.client = NALClient()
        self.config_path = DEFAULT_CONFIG_FILE
        self.cfg = self.load_config(DEFAULT_CONFIG_FILE)

        self._build_ui()

        # 强制“点击后才聚焦 + 未聚焦时滚轮滚动父滚动区”（供 GainRespTab 调用）
        self._apply_strict_focus_behavior()

        # 当输出更新时，刷新“函数测试”页右侧只读显示
        self.outputsChanged.connect(lambda: getattr(self.func_tab, "refresh_outputs_view", lambda: None)())

    # ---------- UI ----------
    def _build_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        vmain = QtWidgets.QVBoxLayout(central)

        self.tabs = QtWidgets.QTabWidget()
        vmain.addWidget(self.tabs)

        # 主页 -> 独立类
        self.home_tab = HomePageTab(self)
        self.tabs.addTab(self.home_tab, "  主页  ")

        # 函数测试 -> 独立类
        self.func_tab = FunctionTestTab(self)
        self.tabs.addTab(self.func_tab, "  函数测试  ")

        # 其余页保持原实现
        self.gr_tab = GainRespTab(self)
        self.tabs.addTab(self.gr_tab, "  增益/响应曲线  ")

        self.io_tab = IO_tab(self)
        self.tabs.addTab(self.io_tab, "  输入/输出曲线  ")

        # 切换页签时，如页面实现了 reload_from_cfg，就刷新一次 UI
        self.tabs.currentChanged.connect(self._on_tab_changed)

    # ---------- response -> cfg ----------
    def handle_response_update_config(self, resp: Dict[str, Any]):
        try:
            fn = resp.get("function","")
            outp = resp.get("output_parameters", {}) or {}
            changed = False

            def upd(name, key):
                nonlocal changed
                if key in outp and outp[key] is not None:
                    setattr(self.cfg, name, outp[key])
                    changed = True

            if fn == "CrossOverFrequencies_NL2":
                upd("CFArray", "CFArray"); upd("FreqInCh", "FreqInCh")
            elif fn == "CenterFrequencies":
                upd("centerF", "centerF")
                if "centreFreq" in outp:
                    setattr(self.cfg, "centerF", outp["centreFreq"]); changed = True
            elif fn == "CompressionThreshold_NL2":
                upd("CT", "CT")
            elif fn == "CompressionRatio_NL2":
                upd("CR", "CR")
            elif fn == "ReturnValues_NL2":
                upd("MAF", "MAF"); upd("BWC", "BWC"); upd("ESCD", "ESCD")
            elif fn == "RealEarAidedGain_NL2":
                for k in ("REAG","gain","REAG19"):
                    if k in outp:
                        self.cfg.REAG = outp[k]; changed = True; break
            elif fn == "RealEarInsertionGain_NL2":
                for k in ("REIG","gain","REIG19"):
                    if k in outp:
                        self.cfg.REIG = outp[k]; changed = True; break
            elif fn == "Speech_o_Gram_NL2":
                upd("Speech_thresh", "Speech_thresh")

            elif fn == "GetREURindiv":
                upd("REUR", "REUR")
            elif fn == "GetREURindiv9":
                if "REUR9" in outp and outp["REUR9"] is not None:
                    self.cfg.REUR9 = outp["REUR9"]; changed = True
            elif fn == "GetREDDindiv":
                upd("REDD", "REDD")
            elif fn == "GetREDDindiv9":
                if "REDD9" in outp and outp["REDD9"] is not None:
                    self.cfg.REDD9 = outp["REDD9"]; changed = True
            elif fn == "GetRECDh_indiv_NL2":
                if "RECDh" in outp and outp["RECDh"] is not None:
                    self.cfg.RECDh = outp["RECDh"]; changed = True
            elif fn == "GetRECDh_indiv9_NL2":
                if "RECDh9" in outp and outp["RECDh9"] is not None:
                    self.cfg.RECDh9 = outp["RECDh9"]; changed = True
            elif fn == "GetRECDt_indiv_NL2":
                if "RECDt" in outp and outp["RECDt"] is not None:
                    self.cfg.RECDt = outp["RECDt"]; changed = True
            elif fn == "GetRECDt_indiv9_NL2":
                if "RECDt9" in outp and outp["RECDt9"] is not None:
                    self.cfg.RECDt9 = outp["RECDt9"]; changed = True

            if changed:
                self.save_config(self.config_path)
                self.outputsChanged.emit()
                self.rrrViewUpdate.emit()
        except Exception as e:
            print("handle_response_update_config error:", e)

    # ---------- config load/save ----------
    def _compact_numeric_arrays(self, s: str) -> str:
        out = []
        i, n = 0, len(s)
        def is_numeric_array_content(txt: str) -> bool:
            for ch in txt:
                if ch in '0123456789eE+-. ,\t\r\n':
                    continue
                return False
            return True
        while i < n:
            ch = s[i]
            if ch == '"':
                out.append(ch); i += 1
                while i < n:
                    c = s[i]; out.append(c); i += 1
                    if c == '\\':
                        if i < n: out.append(s[i]); i += 1
                        continue
                    if c == '"': break
            elif ch == '[':
                depth = 1; j = i + 1; in_str = False; esc = False
                while j < n and depth > 0:
                    c = s[j]
                    if in_str:
                        if esc: esc = False
                        elif c == '\\': esc = True
                        elif c == '"': in_str = False
                    else:
                        if c == '"': in_str = True
                        elif c == '[': depth += 1
                        elif c == ']': depth -= 1
                    j += 1
                if depth != 0:
                    out.append(ch); i += 1; continue
                segment = s[i:j]; inner = segment[1:-1]
                if ('[' in inner) or ('{' in inner) or ('}' in inner):
                    out.append(segment)
                else:
                    if is_numeric_array_content(inner):
                        items = [x.strip() for x in inner.strip().split(',')]
                        items = [x for x in items if x != '']
                        compact = '[' + ', '.join(items) + ']'
                        out.append(compact)
                    else:
                        out.append(segment)
                i = j
            else:
                out.append(ch); i += 1
        return ''.join(out)

    def load_config(self, path: str) -> AppConfig:
        if not os.path.exists(path):
            cfg = AppConfig()
            self.save_config(path, cfg)
            return cfg
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            base = AppConfig()
            for k, v in data.items():
                if hasattr(base, k):
                    setattr(base, k, v)
            if base.channels < 1: base.channels = 1
            if base.channels > 18: base.channels = 18
            return base
        except Exception:
            return AppConfig()

    def save_config(self, path: str, cfg: Optional[AppConfig] = None):
        if cfg is None:
            cfg = self.cfg
        s = json.dumps(asdict(cfg), ensure_ascii=False, indent=2)
        s = self._compact_numeric_arrays(s)
        with open(path, "w", encoding="utf-8") as f:
            f.write(s)
        # 更新“当前文件”标签（主页中的 lbl_cfg）
        try:
            if hasattr(self, "home_tab") and hasattr(self.home_tab, "lbl_cfg"):
                self.home_tab.lbl_cfg.setText(f"Current file: {os.path.basename(path)}")
        except Exception:
            pass

    # ---------- focus behavior ----------
    def _apply_strict_focus_behavior(self):
        # 设置：只有点击才获得焦点；未聚焦时把滚轮事件转发给最近的滚动区域
        self._wheel_filter = _WheelFocusFilter(self)
        kinds = (QtWidgets.QComboBox, QtWidgets.QLineEdit, QtWidgets.QPlainTextEdit, QtWidgets.QTextEdit)
        for cls in kinds:
            for w in self.findChildren(cls):
                w.setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)
                w.installEventFilter(self._wheel_filter)

    # ---------- tab change ----------
    def _on_tab_changed(self, idx: int):
        # 每次切换页签：先从磁盘重载 config，再刷新目标页 UI
        try:
            self.cfg = self.load_config(self.config_path)
        except Exception as e:
            print("Reload config on tab change failed:", e)

        w = self.tabs.widget(idx)
        getattr(w, "reload_from_cfg", lambda: None)()


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)

    # 1.选择主题
    QtWidgets.QApplication.setStyle(QtWidgets.QStyleFactory.create("Fusion")) # Windows / WindowsVista / Fusion / 
    #app.setPalette(app.style().standardPalette())
    # 2. 创建一个自定义的浅色调色板
    light_palette = QtGui.QPalette()
    # 设置所有主要颜色角色为浅色方案，可以根据需要调整这些 RGB 值
    light_palette.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor(240, 240, 240)) # 窗口背景 (浅灰色)
    light_palette.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor(0, 0, 0))   # 窗口文本 (黑色)
    light_palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor(255, 255, 255))   # 输入框、列表视图等可编辑或可选择控件的背景 (白色)
    light_palette.setColor(QtGui.QPalette.ColorRole.AlternateBase, QtGui.QColor(230, 230, 230)) # 间隔行背景 (稍深的浅灰色)
    light_palette.setColor(QtGui.QPalette.ColorRole.ToolTipBase, QtGui.QColor(255, 255, 220)) # 工具提示背景 (淡黄色)
    light_palette.setColor(QtGui.QPalette.ColorRole.ToolTipText, QtGui.QColor(0, 0, 0))   # 工具提示文本 (黑色)
    light_palette.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor(0, 0, 0))         # 正常文本 (黑色)
    light_palette.setColor(QtGui.QPalette.ColorRole.Button, QtGui.QColor(240, 240, 240)) # 按钮背景 (浅灰色)
    light_palette.setColor(QtGui.QPalette.ColorRole.ButtonText, QtGui.QColor(0, 0, 0))   # 按钮文本 (黑色)
    light_palette.setColor(QtGui.QPalette.ColorRole.BrightText, QtGui.QColor(255, 0, 0)) # 亮色文本 (通常是红色，用于错误等)
    light_palette.setColor(QtGui.QPalette.ColorRole.Link, QtGui.QColor(0, 0, 238))       # 链接颜色 (蓝色)
    # 设置高亮颜色 (例如，选中列表项或按钮获得焦点时的颜色)
    light_palette.setColor(QtGui.QPalette.ColorRole.Highlight, QtGui.QColor(60, 120, 210)) # 高亮背景 (中等蓝色)
    light_palette.setColor(QtGui.QPalette.ColorRole.HighlightedText, QtGui.QColor(255, 255, 255)) # 高亮文本 (白色)
    # 3. 将自定义的浅色调色板应用到应用程序
    app.setPalette(light_palette)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())
