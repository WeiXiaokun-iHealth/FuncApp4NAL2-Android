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
APP_VERSION = "Ver2025.12.01-Qt"

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
         "params": ["AC", "BC", "L", "limiting", "channels", "direction", "mic", "target", "aidType",
                    "ACother", "noOfAids", "tubing", "vent", "RECDmeasType"]},
        {"label": "5 - EarSimulatorGain_NL2", "function": "EarSimulatorGain_NL2",
         "params": ["AC", "BC", "L", "direction", "mic", "limiting", "channels", "target", "aidType",
                    "ACother", "noOfAids", "tubing", "vent", "RECDmeasType"]},
        {"label": "6 - RealEarInputOutputCurve_NL2", "function": "RealEarInputOutputCurve_NL2",
         "params": ["AC", "BC", "graphFreq", "startLevel", "finishLevel", "limiting", "channels",
                    "direction", "mic", "target", "ACother", "noOfAids"]},
        {"label": "7 - TccInputOutputCurve_NL2", "function": "TccInputOutputCurve_NL2",
         "params": ["AC", "BC", "graphFreq", "startLevel", "finishLevel", "limiting", "channels",
                    "direction", "mic", "target", "aidType", "ACother", "noOfAids", "tubing", "vent", "RECDmeasType"]},
        {"label": "8 - EarSimulatorInputOutputCurve_NL2", "function": "EarSimulatorInputOutputCurve_NL2",
         "params": ["AC", "BC", "graphFreq", "startLevel", "finishLevel", "limiting", "channels",
                    "direction", "mic", "target", "aidType", "ACother", "noOfAids", "tubing", "vent", "RECDmeasType"]},
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
        {"label": "19 - CrossOverFrequencies_NL2", "function": "CrossOverFrequencies_NL2", "params": ["channels", "AC", "BC"]},
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
        {"label": "32 - Get_SI_NL2", "function": "Get_SI_NL2", "params": ["s", "REAG", "Limit"]},
        {"label": "33 - Get_SII", "function": "Get_SII",
         "params": ["nCompSpeed", "Speech_thresh", "s", "REAG", "REAGp", "REAGm", "REUR"]},
        {"label": "34 - SetAdultChild", "function": "SetAdultChild", "params": ["adultChild", "dateOfBirth"]},
        {"label": "35 - SetExperience", "function": "SetExperience", "params": ["experience"]},
        {"label": "36 - SetCompSpeed", "function": "SetCompSpeed", "params": ["compSpeed"]},
        {"label": "37 - SetTonalLanguage", "function": "SetTonalLanguage", "params": ["tonal"]},
        {"label": "38 - SetGender", "function": "SetGender", "params": ["gender"]},
        {"label": "39 - GetRECDh_indiv_NL2", "function": "GetRECDh_indiv_NL2",
         "params": ["RECDmeasType", "dateOfBirth", "aidType", "tubing", "vent", "coupler", "fittingDepth"]},
        {"label": "40 - GetRECDh_indiv9_NL2", "function": "GetRECDh_indiv9_NL2",
         "params": ["RECDmeasType", "dateOfBirth", "aidType", "tubing", "vent", "coupler", "fittingDepth"]},
        {"label": "41 - GetRECDt_indiv_NL2", "function": "GetRECDt_indiv_NL2",
         "params": ["RECDmeasType", "dateOfBirth", "aidType", "tubing", "vent", "earpiece", "coupler", "fittingDepth"]},
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
    BC:      List[float] = field(default_factory=lambda: [45, 40, 40, 999, 65, 999, 70, 999, 999]) # (2i 3i 4i 5i 6i 7i 8i 9i 10i 19i 22i 24i 25i)
    ACother: List[float] = field(default_factory=lambda: [45, 45, 45, 999, 65, 999, 70, 65, 55])   # (2i 3i 4i 5i 6i 7i 8i 9i 10i 22i 25i)


# ==============================
# 常用参数（多数 API 共享）
# ==============================
    channels: int = 18           # 1..18 (2i 3i 4i 5i 6i 7i 8i 10i 19i 20i 22i 23i 24i 25i)
    bandWidth: int = 0           # 0=宽带;1=窄带 (21i 25i)
    selection: int = 1           # 0=REIG;1=REAG;2=2cc;3=EarSimulator (21i)
    WBCT: int = 52               # 宽带压缩阈         (21i)
    aidType: int = 3             # 0=CIC;1=ITC;2=ITE;3=BTE (4i 5i 7i 8i 21i 25i 26i 39i 40i 41i 42i)
    direction: int = 0           # 0=0°;1=45°            (2i 3i 4i 5i 6i 7i 8i 9i 10i 13i 14i 17i 18i 21i 22i 25i 26i)
    mic: int = 1                 # 0=自由场;1=头表面(MRP) (2i 3i 4i 5i 6i 7i 8i 9i 10i 13i 14i 17i 18i 21i 22i 25i 26i)
    limiting: int = 0            # 0=关;1=宽带;2=多通道 (2i 3i 4i 5i 6i 7i 8i 9i 10i 22i 24i 25i)
    noOfAids: int = 1            # 0=单耳;1=双耳           (2i 3i 4i 5i 6i 7i 8i 9i 10i 22i 25i)
    calcCh: List[int] = field(default_factory=lambda: [1] * 19)  # CompressionThreshold 重算标志 (21i)


# ==============================
# 装配/耦合相关（RECD/管路/通气孔等）
# ==============================
    tubing: int = 3              # 0=Libby4;1=Libby3;2=#13;3=细管;4=RITC;5=None (4i 5i 7i 8i 25i 28i 29i 39i 40i 41i 42i)
    vent: int = 0                # 0=紧;1=封闭;2=封闭穹顶;3=1mm;4=2mm;5=3mm;6=开放穹顶 (4i 5i 7i 8i 25i 30i 31i 39i 40i 41i 42i)
    coupler: int = 0             # 0=HA1;1=HA2 (39i 40i 41i 42i)
    fittingDepth: int = 0        # 0=标准;1=深;2=浅 (39i 40i 41i 42i)
    earpiece: int = 0            # 0=泡棉;1=自制耳模 (41i 42i)
    RECDmeasType: int = 0        # 0=预测;1=实测 (4i 5i 7i 8i 25i 39i 40i 41i 42i)
    REDD_defValues: int = 0      # Get/Set REDD: 0=预测;1=客户数据 (11i 12i 15i 16i)
    REUR_defValues: int = 0      # Get/Set REUR: 0=预测;1=客户数据 (13i 14i 17i 18i)

# ==============================
# 获取增益或曲线用
# ==============================
    L: int = 65                  # 宽带输入电平(dB)          (2i 3i 4i 5i 6i 7i 8i 9i 25i)
    target: int = 1              # 目标：0=REIG;1=REAG (4i 5i 6i 7i 8i 25i)
    targetType: int = 1          # GainAt_NL2: 0=REIG;1=REAG;2=2cc;3=EarSim (25i)
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

class MainWindow(QtWidgets.QMainWindow):
    respReady = QtCore.Signal(str)
    errorReady = QtCore.Signal(str)
    logReady = QtCore.Signal(str)
    seqUpdated = QtCore.Signal(int)
    reqPreviewReady = QtCore.Signal(str)
    outputsChanged = QtCore.Signal()
    rrrViewUpdate = QtCore.Signal()

    # 统一控件宽度（用于列对齐）
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

        self.templates: List[Dict[str, Any]] = []
        self._build_ui()
        self.load_templates()
        self.load_server_from_config()
        self.autosave_config()

        # 强制“点击后才聚焦 + 未聚焦时滚轮滚动父滚动区”
        self._apply_strict_focus_behavior()

        # signals
        self.respReady.connect(self._on_resp_ready)
        self.errorReady.connect(self._on_error_ready)
        self.logReady.connect(self._on_log_ready)
        self.seqUpdated.connect(self._on_seq_updated)
        self.reqPreviewReady.connect(self._on_req_preview_ready)
        self.outputsChanged.connect(self.refresh_outputs_view)
        self.rrrViewUpdate.connect(self.update_rrr_entries_from_cfg)

    # ---------- UI ----------
    def _build_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        vmain = QtWidgets.QVBoxLayout(central)

        self.tabs = QtWidgets.QTabWidget()
        vmain.addWidget(self.tabs)

        self.main_tab = QtWidgets.QWidget()
        self.tabs.addTab(self.main_tab, "  主页  ")
        self._build_main_tab(self.main_tab)

        self.func_tab = QtWidgets.QWidget()
        self.tabs.addTab(self.func_tab, "  函数测试  ")
        self._build_functions_test_tab(self.func_tab)

    def _build_top_connect_bar(self, parent_layout: QtWidgets.QLayout):
        top = QtWidgets.QGridLayout()
        parent_layout.addLayout(top)

        self.ip_edit = QtWidgets.QLineEdit(self.cfg.server_ip);  self.ip_edit.setFixedWidth(self.TOP_IP_W)
        self.port_edit = QtWidgets.QLineEdit(str(self.cfg.server_port)); self.port_edit.setFixedWidth(self.TOP_PORT_W)
        self.path_edit = QtWidgets.QLineEdit(self.cfg.server_path); self.path_edit.setFixedWidth(self.TOP_PATH_W)

        row = 0
        lbl = QtWidgets.QLabel("Server: IP"); lbl.setFixedWidth(80)
        top.addWidget(lbl, row, 0)
        top.addWidget(self.ip_edit, row, 1)
        top.addWidget(QtWidgets.QLabel("Port"), row, 2)
        top.addWidget(self.port_edit, row, 3)
        top.addWidget(QtWidgets.QLabel("Path"), row, 4)
        top.addWidget(self.path_edit, row, 5)

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

    def _build_main_tab(self, parent: QtWidgets.QWidget):
        layout = QtWidgets.QVBoxLayout(parent)

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
            lab.setFixedWidth(self.LABEL_W)
            cb = QtWidgets.QComboBox()
            cb.setFixedWidth(self.COMBO_W)
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

        # 用户设置
        gb_user = QtWidgets.QGroupBox("用户设置")
        left.addWidget(gb_user)
        grid_user = QtWidgets.QGridLayout(gb_user)

        self.adultChild_combo = mk_combo(grid_user, 0, 0, "成人/儿童(adultChild)",
                                         [(0,"成人(adult)"),(1,"儿童(child)"),(2,"按出生日期计算(calculate from date of birth)")],
                                         self.cfg.adultChild)
        lab_dob = QtWidgets.QLabel("出生日期(YYYYMMDD)"); lab_dob.setFixedWidth(self.LABEL_W)
        self.dob_edit = QtWidgets.QLineEdit(str(self.cfg.dateOfBirth)); self.dob_edit.setFixedWidth(self.COMBO_W)
        #grid_user.addWidget(lab_dob, 0, 2*2, QtCore.Qt.AlignmentFlag.AlignLeft)
        #grid_user.addWidget(self.dob_edit, 0, 2*2+1, QtCore.Qt.AlignmentFlag.AlignLeft)
        grid_user.addWidget(lab_dob, 0, 2, QtCore.Qt.AlignmentFlag.AlignLeft)
        grid_user.addWidget(self.dob_edit, 0, 3, QtCore.Qt.AlignmentFlag.AlignLeft)

        self.gender_combo = mk_combo(grid_user, 1, 0, "性别(gender)",
                                     [(0,"未知(unknown)"),(1,"男(male)"),(2,"女(female)")],
                                     self.cfg.gender)
        self.tonal_combo = mk_combo(grid_user, 1, 1, "语言类型(tonal)",
                                    [(0,"非声调(non-tonal)"),(1,"声调(tonal)")],
                                    self.cfg.tonal)

        self.experience_combo = mk_combo(grid_user, 2, 0, "经验(experience)",
                                         [(0,"有经验(experienced)"),(1,"新用户(new user)")],
                                         self.cfg.experience)
        self.compSpeed_combo = mk_combo(grid_user, 2, 1, "压缩速度(compSpeed)",
                                        [(0,"慢(slow)"),(1,"快(fast)"),(2,"双速(dual)")],
                                        self.cfg.compSpeed)

        grid_user.setColumnStretch(4, 1)

        # 听阈
        gb_thr = QtWidgets.QGroupBox("听阈(dB HL) :      250      500      1000      1500      2000     3000     4000     6000     8000 Hz (999 表示未测)")
        left.addWidget(gb_thr)
        v_thr = QtWidgets.QVBoxLayout(gb_thr)
        self.AC_edits = self._mk_array_row(v_thr, "AC[9]:", self.cfg.AC)
        self.BC_edits = self._mk_array_row(v_thr, "BC[9]:", self.cfg.BC)
        self.ACother_edits = self._mk_array_row(v_thr, "ACother[9]:", self.cfg.ACother)

        # 助听器/测量相关
        gb_ha = QtWidgets.QGroupBox("助听器/测量相关")
        left.addWidget(gb_ha)
        grid_ha = QtWidgets.QGridLayout(gb_ha)

        self.channels_combo = mk_combo(grid_ha, 0, 0, "通道数(channels)", [(i,str(i)) for i in range(1,19)], self.cfg.channels)
        self.direction_combo = mk_combo(grid_ha, 0, 1, "声音方向(direction)", [(0,"0°"),(1,"45°")], self.cfg.direction)
        self.bandWidth_combo = mk_combo(grid_ha, 1, 0, "噪声带宽(bandWidth)", [(0,"宽带(broadband)"),(1,"窄带(narrowband)")], self.cfg.bandWidth)
        self.mic_combo = mk_combo(grid_ha, 1, 1, "麦克风参考位置(mic)", [(0,"自由场(undisturbed field)"),(1,"头表面(head surface)")], self.cfg.mic)
        self.selection_combo_cfg = mk_combo(grid_ha, 2, 0, "CT的增益类型(selection)", [(0,"REIG"),(1,"REAG"),(2,"2cc"),(3,"EarSimulator")], self.cfg.selection)
        self.limiting_combo = mk_combo(grid_ha, 2, 1, "限制类型(limiting)", [(0,"关(off)"),(1,"宽带(wideband)"),(2,"多通道(multichannel)")], self.cfg.limiting)

        lab_wbct = QtWidgets.QLabel("宽带压缩阈值(WBCT)"); lab_wbct.setFixedWidth(self.LABEL_W)
        self.WBCT_edit = QtWidgets.QLineEdit(str(self.cfg.WBCT)); self.WBCT_edit.setFixedWidth(self.EDIT_W)
        grid_ha.addWidget(lab_wbct, 3, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        grid_ha.addWidget(self.WBCT_edit, 3, 1, QtCore.Qt.AlignmentFlag.AlignLeft)
        self.noOfAids_combo = mk_combo(grid_ha, 3, 1, "助听器数量(noOfAids)", [(0,"单侧(unilateral)"),(1,"双侧(bilateral)")], self.cfg.noOfAids)

        self.aidType_combo = mk_combo(grid_ha, 4, 0, "助听器类型(aidType)", [(0,"CIC(completely in canal)"),(1,"ITC(in the canal)"),(2,"ITE(in the ear)"),(3,"BTE(behind the ear)")], self.cfg.aidType)

        grid_ha.setColumnStretch(4, 1)

        # 管路/通气/耦合器/插入件
        gb_fit = QtWidgets.QGroupBox("管路/通气/耦合器/插入件")
        left.addWidget(gb_fit)
        grid_fit = QtWidgets.QGridLayout(gb_fit)

        self.tubing_combo = mk_combo(grid_fit, 0, 0, "导管(tubing)", [(0,"Libby4"),(1,"Libby3"),(2,"#13"),(3,"Thintube"),(4,"RITC"),(5,"None")], self.cfg.tubing)
        self.fittingDepth_combo = mk_combo(grid_fit, 0, 1, "验配深度(fittingDepth)", [(0,"标准(standard)"),(1,"深(deep)"),(2,"浅(shallow)")], self.cfg.fittingDepth)
        self.vent_combo = mk_combo(grid_fit, 1, 0, "开口(vent)", [(0,"紧(Tight)"),(1,"堵耳(Occluded)"),(2,"封闭帽(Closed Dome)"),(3,"1mm"),(4,"2mm"),(5,"3mm"),(6,"开放帽(Open Dome)")], self.cfg.vent)
        self.earpiece_combo = mk_combo(grid_fit, 1, 1, "耳塞(earpiece)", [(0,"泡沫耳塞(Foam Tip)"),(1,"自有耳模(Own Mold)")], self.cfg.earpiece)
        self.coupler_combo = mk_combo(grid_fit, 2, 0, "耦合腔(coupler)", [(0,"HA1"),(1,"HA2")], self.cfg.coupler)

        grid_fit.setColumnStretch(4, 1)

        # RECD/REDD/REUR 类型选择
        gb_types = QtWidgets.QGroupBox("RECD/REDD/REUR")
        left.addWidget(gb_types)
        grid_types = QtWidgets.QGridLayout(gb_types)
        self.RECDmeasType_combo = mk_combo(grid_types, 0, 0, "RECD数据类型(RECDmeasType)", [(0,"预估值(Predicted)"),(1,"实测值(Measured)")], self.cfg.RECDmeasType)
        self.REDD_defValues_combo = mk_combo(grid_types, 0, 1, "REDD数据类型(REDD_defValues)", [(0,"预估值(Predicted)"),(1,"用户数据(use client data)")], self.cfg.REDD_defValues)
        self.REUR_defValues_combo = mk_combo(grid_types, 1, 0, "REUR数据类型(REUR_defValues)", [(0,"预估值(Predicted)"),(1,"用户数据(use client data)")], self.cfg.REUR_defValues)

        grid_types.setColumnStretch(4, 1)

        '''
        # RECD/REDD/REUR 读写与显示
        gb_rrr = QtWidgets.QGroupBox("RECD/REDD/REUR 读写与显示")
        left.addWidget(gb_rrr)
        v_rrr = QtWidgets.QVBoxLayout(gb_rrr)

        row_btn = QtWidgets.QHBoxLayout()
        v_rrr.addLayout(row_btn)
        btn_get_19 = QtWidgets.QPushButton("获取RECD/REDD/REUR")
        btn_get_9 = QtWidgets.QPushButton("获取RECD9/REDD9/REUR9")
        row_btn.addWidget(btn_get_19)
        row_btn.addWidget(btn_get_9)
        btn_set_row = QtWidgets.QHBoxLayout()
        v_rrr.addLayout(btn_set_row)
        btn_set_19 = QtWidgets.QPushButton("设置RECD/REDD/REUR")
        btn_set_9 = QtWidgets.QPushButton("设置RECD9/REDD9/REUR9")
        btn_set_row.addWidget(btn_set_19)
        btn_set_row.addWidget(btn_set_9)
        '''
        
        # RECD/REDD/REUR 读写与显示
        gb_rrr = QtWidgets.QGroupBox("RECD/REDD/REUR 读写与显示")
        left.addWidget(gb_rrr)
        v_rrr = QtWidgets.QVBoxLayout(gb_rrr)
        # ------------------- 第一行按钮 -------------------
        row_btn = QtWidgets.QHBoxLayout()
        v_rrr.addLayout(row_btn)

        btn_get_19 = QtWidgets.QPushButton("获取RECD/REDD/REUR")
        btn_get_19.setFixedWidth(160) # 设置固定宽度，你可以根据需要调整这个值
        btn_get_9 = QtWidgets.QPushButton("获取RECD9/REDD9/REUR9")
        btn_get_9.setFixedWidth(160) # 保持宽度一致

        row_btn.addWidget(btn_get_19)
        row_btn.addSpacing(4) # 在按钮之间添加8像素的固定间隔
        row_btn.addWidget(btn_get_9)
        row_btn.addStretch() # 添加伸缩空间，将按钮推向左侧
        # ------------------- 第二行按钮 -------------------
        btn_set_row = QtWidgets.QHBoxLayout()
        v_rrr.addLayout(btn_set_row)

        btn_set_19 = QtWidgets.QPushButton("设置RECD/REDD/REUR")
        btn_set_19.setFixedWidth(160) # 设置固定宽度
        btn_set_9 = QtWidgets.QPushButton("设置RECD9/REDD9/REUR9")
        btn_set_9.setFixedWidth(160) # 保持宽度一致

        btn_set_row.addWidget(btn_set_19)
        btn_set_row.addSpacing(4) # 在按钮之间添加8像素的固定间隔
        btn_set_row.addWidget(btn_set_9)
        btn_set_row.addStretch() # 添加伸缩空间，将按钮推向左侧

        # 19频率表头
        hdr = QtWidgets.QHBoxLayout()
        hdr.addWidget(QtWidgets.QLabel("通道频率(Hz)   "))
        for f in FREQS_19:
            lab = QtWidgets.QLabel(str(f))
            lab.setFixedWidth(40)
            hdr.addWidget(lab)
        hdr.addStretch()
        v_rrr.addLayout(hdr)

        def mk_row19(name: str) -> List[QtWidgets.QLineEdit]:
            row = QtWidgets.QHBoxLayout()
            title = QtWidgets.QLabel(name); title.setFixedWidth(80)
            row.addWidget(title)
            edits = []
            for _ in range(19):
                e = QtWidgets.QLineEdit()
                e.setFixedWidth(40)
                #e.setReadOnly(True)
                edits.append(e)
                row.addWidget(e)
            row.addStretch()
            v_rrr.addLayout(row)
            return edits

        self.RECDh_edits19 = mk_row19("RECDh")
        self.RECDt_edits19 = mk_row19("RECDt")
        self.REDD_edits19 = mk_row19("REDD")
        self.REUR_edits19 = mk_row19("REUR")

        # 9频率表头
        hdr9 = QtWidgets.QHBoxLayout()
        hdr9.addWidget(QtWidgets.QLabel("测听频率(Hz)   "))
        for f in FREQS_9:
            lab = QtWidgets.QLabel(str(f))
            lab.setFixedWidth(40)
            hdr9.addWidget(lab)
        hdr9.addStretch()
        v_rrr.addLayout(hdr9)

        def mk_row9(name: str) -> List[QtWidgets.QLineEdit]:
            row = QtWidgets.QHBoxLayout()
            title = QtWidgets.QLabel(name); title.setFixedWidth(80)
            row.addWidget(title)
            edits = []
            for _ in range(9):
                e = QtWidgets.QLineEdit()
                e.setFixedWidth(40)
                #e.setReadOnly(True)
                edits.append(e)
                row.addWidget(e)
            row.addStretch()
            v_rrr.addLayout(row)
            return edits

        self.RECDh_edits9 = mk_row9("RECDh9")
        self.RECDt_edits9 = mk_row9("RECDt9")
        self.REDD_edits9 = mk_row9("REDD9")
        self.REUR_edits9 = mk_row9("REUR9")

        btn_get_19.clicked.connect(self.on_fetch_rrr_19)
        btn_get_9.clicked.connect(self.on_fetch_rrr_9)
        btn_set_19.clicked.connect(self.on_set_rrr_19)
        btn_set_9.clicked.connect(self.on_set_rrr_9)

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
        self.lbl_cfg = QtWidgets.QLabel(f"Current file: {os.path.basename(self.config_path)}")
        v_file.addWidget(self.lbl_cfg)

        gb_apply = QtWidgets.QGroupBox("Apply to server (Step 1-8)")
        right_layout.addWidget(gb_apply)
        v_apply = QtWidgets.QVBoxLayout(gb_apply)
        btn_apply = QtWidgets.QPushButton("Step 1-8 Initialize")
        v_apply.addWidget(btn_apply)

        # 日志 + 清除
        self.apply_log = QtWidgets.QTextEdit()
        self.apply_log.setReadOnly(False)
        right_layout.addWidget(self.apply_log, 1)
        btn_clear_log = QtWidgets.QPushButton("清除log")
        right_layout.addWidget(btn_clear_log)

        btn_load_cfg.clicked.connect(self.on_load_config)
        btn_saveas_cfg.clicked.connect(self.on_saveas_config)
        btn_apply.clicked.connect(self.on_apply_steps)
        btn_clear_log.clicked.connect(lambda: self.apply_log.clear())

        # 初始化数据显示
        self.update_rrr_entries_from_cfg()

        # 绑定更改 -> 自动保存
        for cb, setter in [
            (self.adultChild_combo, lambda v: setattr(self.cfg, "adultChild", v)),
            (self.gender_combo, lambda v: setattr(self.cfg, "gender", v)),
            (self.tonal_combo, lambda v: setattr(self.cfg, "tonal", v)),
            (self.experience_combo, lambda v: setattr(self.cfg, "experience", v)),
            (self.compSpeed_combo, lambda v: setattr(self.cfg, "compSpeed", v)),
            (self.channels_combo, lambda v: setattr(self.cfg, "channels", v)),
            (self.direction_combo, lambda v: setattr(self.cfg, "direction", v)),
            (self.bandWidth_combo, lambda v: setattr(self.cfg, "bandWidth", v)),
            (self.mic_combo, lambda v: setattr(self.cfg, "mic", v)),
            (self.selection_combo_cfg, lambda v: setattr(self.cfg, "selection", v)),
            (self.limiting_combo, lambda v: setattr(self.cfg, "limiting", v)),
            (self.noOfAids_combo, lambda v: setattr(self.cfg, "noOfAids", v)),
            (self.aidType_combo, lambda v: setattr(self.cfg, "aidType", v)),
            (self.tubing_combo, lambda v: setattr(self.cfg, "tubing", v)),
            (self.fittingDepth_combo, lambda v: setattr(self.cfg, "fittingDepth", v)),
            (self.vent_combo, lambda v: setattr(self.cfg, "vent", v)),
            (self.earpiece_combo, lambda v: setattr(self.cfg, "earpiece", v)),
            (self.coupler_combo, lambda v: setattr(self.cfg, "coupler", v)),
            (self.RECDmeasType_combo, lambda v: setattr(self.cfg, "RECDmeasType", v)),
            (self.REDD_defValues_combo, lambda v: setattr(self.cfg, "REDD_defValues", v)),
            (self.REUR_defValues_combo, lambda v: setattr(self.cfg, "REUR_defValues", v)),
        ]:
            cb.currentIndexChanged.connect(lambda _=None, c=cb, s=setter: self._on_combo_changed(c, s))

        self.dob_edit.editingFinished.connect(self.autosave_config)
        self.WBCT_edit.editingFinished.connect(self.autosave_config)
        for e in self.AC_edits + self.BC_edits + self.ACother_edits:
            e.editingFinished.connect(self.autosave_config)

    def _apply_strict_focus_behavior(self):
        # 设置：只有点击才获得焦点；未聚焦时把滚轮事件转发给最近的滚动区域
        self._wheel_filter = _WheelFocusFilter(self)
        kinds = (QtWidgets.QComboBox, QtWidgets.QLineEdit, QtWidgets.QPlainTextEdit, QtWidgets.QTextEdit)
        for cls in kinds:
            for w in self.findChildren(cls):
                w.setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)
                w.installEventFilter(self._wheel_filter)

    def _mk_array_row(self, parent_layout: QtWidgets.QVBoxLayout, label: str, values: List[float]) -> List[QtWidgets.QLineEdit]:
        roww = QtWidgets.QHBoxLayout()
        lab = QtWidgets.QLabel(label); lab.setFixedWidth(70)
        roww.addWidget(lab)
        edits: List[QtWidgets.QLineEdit] = []
        for v in values:
            e = QtWidgets.QLineEdit(str(v))
            e.setFixedWidth(40)
            edits.append(e)
            roww.addWidget(e)
        roww.addStretch()
        parent_layout.addLayout(roww)
        return edits

    def _build_functions_test_tab(self, parent: QtWidgets.QWidget):
        layout = QtWidgets.QVBoxLayout(parent)

        # 参数
        gb_param = QtWidgets.QGroupBox("参数")
        layout.addWidget(gb_param)
        v_param = QtWidgets.QVBoxLayout(gb_param)

        line1 = QtWidgets.QHBoxLayout()
        v_param.addLayout(line1)
        labL = QtWidgets.QLabel("宽带输入电平(L)"); labL.setFixedWidth(self.LABEL_W)
        self.L_edit = QtWidgets.QLineEdit(str(self.cfg.L)); self.L_edit.setFixedWidth(self.EDIT_W)
        line1.addWidget(labL)
        line1.addWidget(self.L_edit)
        line1.addWidget(QtWidgets.QLabel("dB SPL"))
        line1.addSpacing(20)

        labSel = QtWidgets.QLabel("CT的增益类型(selection)"); labSel.setFixedWidth(self.LABEL_W)
        self.selection_combo = QtWidgets.QComboBox(); self.selection_combo.setFixedWidth(self.COMBO_W)
        for k,v in [(0,"REIG"),(1,"REAG"),(2,"2ccCoupler"),(3,"EarSimulator")]:
            self.selection_combo.addItem(f"{k} - {v}", k)
        self._set_combo_by_value(self.selection_combo, self.cfg.selection)
        line1.addWidget(labSel)
        line1.addWidget(self.selection_combo)

        labTgt = QtWidgets.QLabel("要使用的增益目标(target)"); labTgt.setFixedWidth(self.LABEL_W)
        self.target_combo = QtWidgets.QComboBox(); self.target_combo.setFixedWidth(self.COMBO_W)
        for k,v in [(0,"REIG"),(1,"REAG")]:
            self.target_combo.addItem(f"{k} - {v}", k)
        self._set_combo_by_value(self.target_combo, self.cfg.target)
        line1.addWidget(labTgt)
        line1.addWidget(self.target_combo)
        line1.addStretch()

        line2 = QtWidgets.QHBoxLayout()
        v_param.addLayout(line2)
        labIOcurve = QtWidgets.QLabel("输入/输出曲线(函数6/7/8)：")
        line2.addWidget(labIOcurve);labIOcurve.setFixedWidth(180)
        labGF = QtWidgets.QLabel("绘制频率(graphFreq)"); labGF.setFixedWidth(self.LABEL_W)
        self.graphFreq_combo = QtWidgets.QComboBox(); self.graphFreq_combo.setFixedWidth(self.COMBO_W)
        for i, f in enumerate(["125","160","200","250","315","400","500","630","800","1000",
                               "1250","1600","2000","2500","3150","4000","5000","6300","8000"]):
            self.graphFreq_combo.addItem(f"{i} - {f}Hz", i)
        self._set_combo_by_value(self.graphFreq_combo, self.cfg.graphFreq)
        line2.addWidget(labGF)
        line2.addWidget(self.graphFreq_combo)

        for cap, attr in [("startLevel","startLevel"), ("finishLevel","finishLevel")]:
            lab = QtWidgets.QLabel(cap); lab.setFixedWidth(70)
            edit = QtWidgets.QLineEdit(str(getattr(self.cfg, attr))); edit.setFixedWidth(40)
            setattr(self, f"{attr}_edit", edit)
            line2.addWidget(lab)
            line2.addWidget(edit)
            line2.addWidget(QtWidgets.QLabel("dB SPL"))

        line3 = QtWidgets.QHBoxLayout()
        v_param.addLayout(line3)
        labType = QtWidgets.QLabel("所需MPO类型(type)"); labType.setFixedWidth(self.LABEL_W)
        self.type_combo = QtWidgets.QComboBox(); self.type_combo.setFixedWidth(self.COMBO_W)
        for k,v in [(0,"RESR"),(1,"SSPL")]:
            self.type_combo.addItem(f"{k} - {v}", k)
        self._set_combo_by_value(self.type_combo, self.cfg.type)
        line3.addWidget(labType); line3.addWidget(self.type_combo)

        labS = QtWidgets.QLabel("语音电平(s)"); labS.setFixedWidth(self.LABEL_W)
        self.s_combo = QtWidgets.QComboBox(); self.s_combo.setFixedWidth(self.COMBO_W)
        for i, txt in enumerate(["55dB","60dB","65dB","70dB","75dB","72dB","69dB"]):
            self.s_combo.addItem(f"{i} - {txt}", i)
        self._set_combo_by_value(self.s_combo, self.cfg.s)
        line3.addWidget(labS); line3.addWidget(self.s_combo)
        line3.addStretch()

        # 只读显示（缓存输出）
        gb_out = QtWidgets.QGroupBox("派生/缓存输出（自动随响应更新；可复制）")
        layout.addWidget(gb_out)
        h_out = QtWidgets.QHBoxLayout(gb_out)
        self.txt_CFArray = self._mk_ro_text(h_out, "CFArray")
        self.txt_FreqInCh = self._mk_ro_text(h_out, "FreqInCh")
        self.txt_CT = self._mk_ro_text(h_out, "CT")
        self.txt_CR = self._mk_ro_text(h_out, "CR")

        # 模板/请求/响应
        mid = QtWidgets.QVBoxLayout()
        layout.addLayout(mid, 1)

        bar = QtWidgets.QHBoxLayout()
        mid.addLayout(bar)
        bar.addWidget(QtWidgets.QLabel("单条函数调用"))
        self.tmpl_combo = QtWidgets.QComboBox(); self.tmpl_combo.setFixedWidth(self.COMBO_W + 120)
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
            "input_parameters": {"adultChild": self.cfg.adultChild, "dateOfBirth": self.cfg.dateOfBirth}
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

    def _mk_ro_text(self, layout: QtWidgets.QHBoxLayout, label: str) -> QtWidgets.QPlainTextEdit:
        box = QtWidgets.QGroupBox(label)
        layout.addWidget(box)
        v = QtWidgets.QVBoxLayout(box)
        t = QtWidgets.QPlainTextEdit()
        t.setReadOnly(True)
        v.addWidget(t)
        return t

    # ---------- helpers ----------
    def _set_combo_by_value(self, combo: QtWidgets.QComboBox, val: int):
        idx = 0
        for i in range(combo.count()):
            if combo.itemData(i) == val:
                idx = i
                break
        combo.setCurrentIndex(idx)

    def _on_combo_changed(self, combo: QtWidgets.QComboBox, setter):
        try:
            val = int(combo.currentData())
        except Exception:
            val = 0
        setter(val)
        self.autosave_config()

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

    def load_server_from_config(self):
        self.ip_edit.setText(self.cfg.server_ip)
        self.port_edit.setText(str(self.cfg.server_port))
        self.path_edit.setText(self.cfg.server_path)

    # ---------- connect ----------
    def on_connect(self):
        try:
            ip = self.ip_edit.text().strip()
            port = int(self.port_edit.text().strip())
            path = self.path_edit.text().strip()
        except ValueError:
            QtWidgets.QMessageBox.critical(self, "错误(Error)", "端口号不正确(Wrong port number)")
            return
        self.client.set_server(ip, port, path)
        ok = self.client.connect()
        if ok:
            self.status_label.setText(f"已连接(Connected): {self.client.url()}")
            self.btn_connect.setEnabled(False); self.btn_disconnect.setEnabled(True)
            self.cfg.server_ip = ip; self.cfg.server_port = port; self.cfg.server_path = path if path else "/"
            self.save_config(self.config_path)
        else:
            self.status_label.setText("无法连接（请检查 IP/端口/网络）")

    def on_disconnect(self):
        self.client.disconnect()
        self.status_label.setText("未连接(Disconnected)")
        self.btn_connect.setEnabled(True); self.btn_disconnect.setEnabled(False)

    # ---------- template insert ----------
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
        cfgd = asdict(self.cfg)
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
        if not self.client.connected:
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
            preview = dict(req); preview["sequence_num"] = self.client.sequence_num
            self.reqPreviewReady.emit(json.dumps(preview, ensure_ascii=False, indent=2))
            resp = self.client.post_json(req)
            self.handle_response_update_config(resp)
            self.respReady.emit(json.dumps(resp, ensure_ascii=False, indent=2))
        except RequestException as e:
            self.errorReady.emit(f"网络错误: {e}")
        except Exception as e:
            self.errorReady.emit(f"异常: {e}")
        finally:
            self.seqUpdated.emit(self.client.sequence_num)

    @QtCore.Slot(str)
    def _on_resp_ready(self, payload: str):
        self.resp_text.setPlainText(payload)

    @QtCore.Slot(str)
    def _on_error_ready(self, msg: str):
        QtWidgets.QMessageBox.critical(self, "错误", msg)

    @QtCore.Slot(int)
    def _on_seq_updated(self, seq: int):
        self.seq_label.setText(f"sequence_num: {seq}")

    @QtCore.Slot(str)
    def _on_log_ready(self, msg: str):
        self.apply_log.append(msg)

    @QtCore.Slot(str)
    def _on_req_preview_ready(self, s: str):
        self.req_text.setPlainText(s)

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
                if "REUR" in outp and outp["REUR"] is not None:
                    self.cfg.REUR9 = outp["REUR"]; changed = True
            elif fn == "GetREDDindiv":
                upd("REDD", "REDD")
            elif fn == "GetREDDindiv9":
                if "REDD" in outp and outp["REDD"] is not None:
                    self.cfg.REDD9 = outp["REDD"]; changed = True
            elif fn == "GetRECDh_indiv_NL2":
                if "RECDh" in outp and outp["RECDh"] is not None:
                    self.cfg.RECDh = outp["RECDh"]; changed = True
            elif fn == "GetRECDh_indiv9_NL2":
                if "RECDh" in outp and outp["RECDh"] is not None:
                    self.cfg.RECDh9 = outp["RECDh"]; changed = True
            elif fn == "GetRECDt_indiv_NL2":
                if "RECDt" in outp and outp["RECDt"] is not None:
                    self.cfg.RECDt = outp["RECDt"]; changed = True
            elif fn == "GetRECDt_indiv9_NL2":
                if "RECDt" in outp and outp["RECDt"] is not None:
                    self.cfg.RECDt9 = outp["RECDt"]; changed = True

            if changed:
                self.save_config(self.config_path)
                self.outputsChanged.emit()
                self.rrrViewUpdate.emit()
        except Exception as e:
            print("handle_response_update_config error:", e)

    def refresh_outputs_view(self):
        def set_ro_text(widget: QtWidgets.QPlainTextEdit, data):
            widget.setPlainText(json.dumps(data, ensure_ascii=False))
        set_ro_text(self.txt_CFArray, self.cfg.CFArray)
        set_ro_text(self.txt_FreqInCh, self.cfg.FreqInCh)
        set_ro_text(self.txt_CT, self.cfg.CT)
        set_ro_text(self.txt_CR, self.cfg.CR)

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

        fill(self.RECDh_edits19, self.cfg.RECDh or [], 19)
        fill(self.RECDt_edits19, self.cfg.RECDt or [], 19)
        fill(self.REDD_edits19, self.cfg.REDD or [], 19)
        fill(self.REUR_edits19, self.cfg.REUR or [], 19)

        fill(self.RECDh_edits9, self.cfg.RECDh9 or [], 9)
        fill(self.RECDt_edits9, self.cfg.RECDt9 or [], 9)
        fill(self.REDD_edits9, self.cfg.REDD9 or [], 9)
        fill(self.REUR_edits9, self.cfg.REUR9 or [], 9)

        self.save_config(self.config_path)

    # ---------- RRR actions ----------
    def _log_send_resp(self, req: Dict[str, Any], resp: Dict[str, Any]):
        prev = dict(req); prev["sequence_num"] = self.client.sequence_num - 1
        self.logReady.emit("发送:\n" + json.dumps(prev, ensure_ascii=False, indent=2))
        self.logReady.emit("响应:\n" + json.dumps(resp, ensure_ascii=False, indent=2))
        self.logReady.emit("--------------------------------------------------------------------")

    def on_fetch_rrr_19(self):
        if not self.client.connected:
            QtWidgets.QMessageBox.warning(self, "提示", "请先连接服务器")
            return
        c = self.cfg

        def send(function, params):
            req = {"function": function, "input_parameters": params}
            resp = self.client.post_json(req)
            self.handle_response_update_config(resp)
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
                self.errorReady.emit(f"获取RECD/REDD/REUR失败: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def on_fetch_rrr_9(self):
        if not self.client.connected:
            QtWidgets.QMessageBox.warning(self, "提示", "请先连接服务器")
            return
        c = self.cfg

        def send(function, params):
            req = {"function": function, "input_parameters": params}
            resp = self.client.post_json(req)
            self.handle_response_update_config(resp)
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
                self.errorReady.emit(f"获取RECD9/REDD9/REUR9失败: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def on_set_rrr_19(self):
        if not self.client.connected:
            QtWidgets.QMessageBox.warning(self, "提示", "请先连接服务器")
            return
        c = self.cfg

        def ok_len(arr, n): return isinstance(arr, list) and len(arr) == n
        if not ok_len(c.RECDh, 19) or not ok_len(c.RECDt, 19) or not ok_len(c.REDD, 19) or not ok_len(c.REUR, 19):
            QtWidgets.QMessageBox.warning(self, "提示", "配置文件中 RECDh/RECDt/REDD/REUR(19点) 不完整，无法设置")
            return

        def send(function, params):
            req = {"function": function, "input_parameters": params}
            resp = self.client.post_json(req)
            self.handle_response_update_config(resp)
            self._log_send_resp(req, resp)
            return resp

        def worker():
            try:
                send("SetRECDh_indiv_NL2", {"RECDh": c.RECDh})
                send("SetRECDt_indiv_NL2", {"RECDt": c.RECDt})
                send("SetREDDindiv", {"REDD": c.REDD, "REDD_defValues": c.REDD_defValues})
                send("SetREURindiv", {"REUR": c.REUR, "REUR_defValues": c.REUR_defValues,
                                      "dateOfBirth": c.dateOfBirth, "direction": c.direction, "mic": c.mic})
            except Exception as e:
                self.errorReady.emit(f"设置RECD/REDD/REUR失败: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def on_set_rrr_9(self):
        if not self.client.connected:
            QtWidgets.QMessageBox.warning(self, "提示", "请先连接服务器")
            return
        c = self.cfg

        def ok_len(arr, n): return isinstance(arr, list) and len(arr) == n
        if not ok_len(c.RECDh9, 9) or not ok_len(c.RECDt9, 9) or not ok_len(c.REDD9, 9) or not ok_len(c.REUR9, 9):
            QtWidgets.QMessageBox.warning(self, "提示", "配置文件中 RECDh9/RECDt9/REDD9/REUR9(9点) 不完整，无法设置")
            return

        def send(function, params):
            req = {"function": function, "input_parameters": params}
            resp = self.client.post_json(req)
            self.handle_response_update_config(resp)
            self._log_send_resp(req, resp)
            return resp

        def worker():
            try:
                send("SetRECDh_indiv9_NL2", {"RECDh9": c.RECDh9})
                send("SetRECDt_indiv9_NL2", {"RECDt9": c.RECDt9})
                send("SetREDDindiv9", {"REDD9": c.REDD9, "REDD_defValues": c.REDD_defValues})
                send("SetREURindiv9", {"REUR9": c.REUR9, "REUR_defValues": c.REUR_defValues,
                                       "dateOfBirth": c.dateOfBirth, "direction": c.direction, "mic": c.mic})
            except Exception as e:
                self.errorReady.emit(f"设置RECD9/REDD9/REUR9失败: {e}")
        threading.Thread(target=worker, daemon=True).start()

    # ---------- Step 1-8 ----------
    def on_apply_steps(self):
        if not self.client.connected:
            QtWidgets.QMessageBox.warning(self, "提示", "请先连接服务器")
            return
        self.autosave_config()
        self.apply_log.clear()
        threading.Thread(target=self._apply_steps_thread, daemon=True).start()

    def _apply_steps_thread(self):
        def log(msg: str):
            self.logReady.emit(msg)
        def send(function: str, params: Dict[str, Any]):
            req = {"function": function, "input_parameters": params}
            prev = dict(req); prev["sequence_num"] = self.client.sequence_num
            log("发送:\n" + json.dumps(prev, ensure_ascii=False, indent=2))
            resp = self.client.post_json(req)
            log("响应:\n" + json.dumps(resp, ensure_ascii=False, indent=2))
            log("--------------------------------------------------------------------\n")
            self.handle_response_update_config(resp)
            return resp
        try:
            c = self.cfg
            send("SetAdultChild", {"adultChild": c.adultChild, "dateOfBirth": c.dateOfBirth})
            send("SetExperience", {"experience": c.experience})
            send("SetCompSpeed", {"compSpeed": c.compSpeed})
            send("SetTonalLanguage", {"tonal": c.tonal})
            send("SetGender", {"gender": c.gender})
            send("CrossOverFrequencies_NL2", {"channels": c.channels, "AC": c.AC, "BC": c.BC})
            crossOver = self.cfg.CFArray if self.cfg.CFArray else []
            send("setBWC", {"channels": c.channels, "crossOver": crossOver})
            send("CompressionThreshold_NL2", {
                "bandWidth": c.bandWidth, "selection": c.selection, "WBCT": c.WBCT,
                "aidType": c.aidType, "direction": c.direction, "mic": c.mic, "calcCh": c.calcCh
            })
            log("步骤(1-8)完成")
        except Exception as e:
            log(f"执行异常: {e}")
        finally:
            self.seqUpdated.emit(self.client.sequence_num)
            self.outputsChanged.emit()

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
        if hasattr(self, 'lbl_cfg'):
            self.lbl_cfg.setText(f"Current file: {os.path.basename(path)}")

    def on_load_config(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "选择配置文件", "", "JSON (*.json);;All (*.*)")
        if not path: return
        self.cfg = self.load_config(path)
        self.config_path = path

        # 刷新 UI（常用参数/服务器）
        self.load_server_from_config()
        # 听阈
        for i, v in enumerate(self.cfg.AC):
            if i < len(self.AC_edits): self.AC_edits[i].setText(str(v))
        for i, v in enumerate(self.cfg.BC):
            if i < len(self.BC_edits): self.BC_edits[i].setText(str(v))
        for i, v in enumerate(self.cfg.ACother):
            if i < len(self.ACother_edits): self.ACother_edits[i].setText(str(v))
        # 顶部参数区
        self.L_edit.setText(str(self.cfg.L))
        self._set_combo_by_value(self.graphFreq_combo, self.cfg.graphFreq)
        self.startLevel_edit.setText(str(self.cfg.startLevel))
        self.finishLevel_edit.setText(str(self.cfg.finishLevel))
        self._set_combo_by_value(self.type_combo, self.cfg.type)
        self._set_combo_by_value(self.s_combo, self.cfg.s)

        self.refresh_outputs_view()
        self.autosave_config()
        self.update_rrr_entries_from_cfg()

    def on_saveas_config(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "另存配置为", "", "JSON (*.json);;All (*.*)")
        if not path: return
        self.save_config(path)
        self.config_path = path
        QtWidgets.QMessageBox.information(self, "提示", "配置已保存")

    # ---------- home params ----------
    def save_home_params_to_cfg(self):
        try:
            self.cfg.L = int(float(self.L_edit.text().strip() or self.cfg.L))
            self.cfg.selection = int(self.selection_combo.currentData())
            self.cfg.target = int(self.target_combo.currentData())
            self.cfg.graphFreq = int(self.graphFreq_combo.currentData())
            self.cfg.startLevel = int(float(self.startLevel_edit.text().strip() or self.cfg.startLevel))
            self.cfg.finishLevel = int(float(self.finishLevel_edit.text().strip() or self.cfg.finishLevel))
            self.cfg.type = int(self.type_combo.currentData())
            self.cfg.s = int(self.s_combo.currentData())
            self.save_config(self.config_path)
        except Exception as e:
            print("save_home_params_to_cfg:", e)

    def autosave_config(self):
        try:
            # 服务器
            self.cfg.server_ip = self.ip_edit.text().strip()
            try: self.cfg.server_port = int(self.port_edit.text().strip())
            except: pass
            p = self.path_edit.text().strip()
            self.cfg.server_path = p if p else "/"

            # 用户信息
            self.cfg.adultChild = int(self.adultChild_combo.currentData())
            try: self.cfg.dateOfBirth = int(self.dob_edit.text().strip() or 0)
            except: pass
            self.cfg.experience = int(self.experience_combo.currentData())
            self.cfg.compSpeed = int(self.compSpeed_combo.currentData())
            self.cfg.tonal = int(self.tonal_combo.currentData())
            self.cfg.gender = int(self.gender_combo.currentData())

            # 听阈
            self.cfg.AC = self._parse_9(self.AC_edits)
            self.cfg.BC = self._parse_9(self.BC_edits)
            self.cfg.ACother = self._parse_9(self.ACother_edits)

            # 助听器/测量
            ch = int(self.channels_combo.currentData())
            self.cfg.channels = 1 if ch < 1 else (18 if ch > 18 else ch)
            self.cfg.bandWidth = int(self.bandWidth_combo.currentData())
            self.cfg.selection = int(self.selection_combo_cfg.currentData())
            try: self.cfg.WBCT = int(self.WBCT_edit.text().strip() or self.cfg.WBCT)
            except: pass
            self.cfg.aidType = int(self.aidType_combo.currentData())
            self.cfg.direction = int(self.direction_combo.currentData())
            self.cfg.mic = int(self.mic_combo.currentData())
            self.cfg.limiting = int(self.limiting_combo.currentData())
            self.cfg.noOfAids = int(self.noOfAids_combo.currentData())

            # 装配/耦合
            self.cfg.tubing = int(self.tubing_combo.currentData())
            self.cfg.vent = int(self.vent_combo.currentData())
            self.cfg.coupler = int(self.coupler_combo.currentData())
            self.cfg.fittingDepth = int(self.fittingDepth_combo.currentData())
            self.cfg.earpiece = int(self.earpiece_combo.currentData())
            self.cfg.RECDmeasType = int(self.RECDmeasType_combo.currentData())
            self.cfg.REDD_defValues = int(self.REDD_defValues_combo.currentData())
            self.cfg.REUR_defValues = int(self.REUR_defValues_combo.currentData())

            self.save_config(self.config_path)
        except Exception as e:
            print("autosave_config error:", e)

    def _parse_9(self, edits: List[QtWidgets.QLineEdit]) -> List[int]:
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

    # ---------- param change handlers ----------
    def _on_sel_change(self):
        self.cfg.selection = int(self.selection_combo.currentData())
        self.save_home_params_to_cfg()

    def _on_tgt_change(self):
        self.cfg.target = int(self.target_combo.currentData())
        self.save_home_params_to_cfg()

    def _on_graphFreq_change(self):
        self.cfg.graphFreq = int(self.graphFreq_combo.currentData())
        self.save_home_params_to_cfg()

    def _on_type_change(self):
        self.cfg.type = int(self.type_combo.currentData())
        self.save_home_params_to_cfg()

    def _on_s_change(self):
        self.cfg.s = int(self.s_combo.currentData())
        self.save_home_params_to_cfg()

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
