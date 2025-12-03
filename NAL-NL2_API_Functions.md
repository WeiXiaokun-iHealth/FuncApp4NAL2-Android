# NAL-NL2 DLL API 函数参考

**版本:** 1.0.0.0  
**更新日期:** 2025-12-02

---

## 数组定义

```typescript
// 9元素数组 - 标准听力测试频率
type AC[9] = [250Hz, 500Hz, 1kHz, 1.5kHz, 2kHz, 3kHz, 4kHz, 6kHz, 8kHz]

// 19元素数组 - 三分之一倍频程频率
type REIG[19] = [125Hz, 160Hz, 200Hz, 250Hz, 315Hz, 400Hz, 500Hz, 630Hz, 800Hz,
                 1000Hz, 1250Hz, 1600Hz, 2000Hz, 2500Hz, 3150Hz, 4000Hz, 5000Hz, 6300Hz, 8000Hz]
```

---

## API 函数

### 1. dllVersion

```c
// 功能: 获取DLL版本号
// 依赖: 无
int dllVersion(
    output int* major,      // 主版本号
    output int* minor       // 次版本号
) -> int                    // 返回: 0=成功
```

---

### 2. RealEarInsertionGain_NL2

```c
// 功能: 计算真耳插入增益 (REIG)
// 依赖: 23, 21, 34, 35, 36, 37, 38
int RealEarInsertionGain_NL2(
    output double REIG[19],     // 真耳插入增益 (三分之一倍频程)
    input double AC[9],         // 气导听阈
    input double BC[9],         // 骨导听阈
    input double L,             // 宽带信号输入级 (dB)
    input int limiting,         // 限制类型: 0=关闭, 1=宽带, 2=多通道
    input int channels,         // 通道数 (1-18)
    input int direction,        // 声音方向: 0=0度, 1=45度
    input int mic,              // 麦克风位置: 0=自由场, 1=头表面
    input double ACother[9],    // 对侧耳气导听阈
    input int noOfAids          // 助听器数量: 0=单侧, 1=双侧
) -> int                        // 返回: 0=成功
```

---

### 3. RealEarAidedGain_NL2

```c
// 功能: 计算真耳助听增益 (REAG)
// 依赖: 23, 21, 34, 35, 36, 37, 38
int RealEarAidedGain_NL2(
    output double REAG[19],      // 真耳助听增益 (三分之一倍频程)
    input double AC[9],         // 气导听阈
    input double BC[9],         // 骨导听阈
    input double L,             // 宽带信号输入级 (dB)
    input int limiting,         // 限制类型: 0=关闭, 1=宽带, 2=多通道
    input int channels,         // 通道数 (1-18)
    input int direction,        // 声音方向: 0=0度, 1=45度
    input int mic,              // 麦克风位置: 0=自由场, 1=头表面
    input double ACother[9],    // 对侧耳气导听阈
    input int noOfAids          // 助听器数量: 0=单侧, 1=双侧
) -> int                        // 返回: 0=成功
```

---

### 4. TccCouplerGain_NL2

```c
// 功能: 计算2cc耦合腔增益
// 依赖: 23, 43或44, 17或18, 21, 34, 35, 36, 37, 38
int TccCouplerGain_NL2(
    output double TccCG[19],        // 2cc耦合腔增益 (三分之一倍频程)
    input double AC[9],            // 气导听阈
    input double BC[9],            // 骨导听阈
    input double L,                // 宽带信号输入级 (dB)
    input int limiting,            // 限制类型: 0=关闭, 1=宽带, 2=多通道
    input int channels,            // 通道数 (1-18)
    input int direction,           // 声音方向: 0=0度, 1=45度
    input int mic,                 // 麦克风位置: 0=自由场, 1=头表面
    input int target,              // 增益目标: 0=REIG, 1=REAG
    input int aidType,             // 助听器类型: 0=CIC, 1=ITC, 2=ITE, 3=BTE
    input double ACother[9],       // 对侧耳气导听阈
    input int noOfAids,            // 助听器数量: 0=单侧, 1=双侧
    input int tubing,              // 声管类型
    input int vent,                // 通气孔类型
    input int RECDmeasType,        // RECD测量方法: 0=预测, 1=测量
    output int lineType[19]        // 曲线类型: 0=实线, 1=虚线
) -> int                           // 返回: 0=成功
```

---

### 5. EarSimulatorGain_NL2

```c
// 功能: 计算耳模拟器增益
// 依赖: 23, 43或44, 17或18, 21, 34, 35, 36, 37, 38
int EarSimulatorGain_NL2(
    output double ESG[19],          // 耳模拟器增益 (三分之一倍频程)
    input double AC[9],            // 气导听阈
    input double BC[9],            // 骨导听阈
    input double L,                // 宽带信号输入级 (dB)
    input int direction,           // 声音方向: 0=0度, 1=45度
    input int mic,                 // 麦克风位置: 0=自由场, 1=头表面
    input int limiting,            // 限制类型: 0=关闭, 1=宽带, 2=多通道
    input int channels,            // 通道数 (1-18)
    input int target,              // 增益目标: 0=REIG, 1=REAG
    input int aidType,             // 助听器类型: 0=CIC, 1=ITC, 2=ITE, 3=BTE
    input double ACother[9],       // 对侧耳气导听阈
    input int noOfAids,            // 助听器数量: 0=单侧, 1=双侧
    input int tubing,              // 未使用
    input int vent,                // 通气孔类型
    input int RECDmeasType,        // 未使用
    output int lineType[19]        // 曲线类型: 0=实线, 1=虚线
) -> int                           // 返回: 0=成功
```

---

### 6. RealEarInputOutputCurve_NL2

```c
// 功能: 计算真耳输入/输出曲线
// 依赖: 23, 17或18, 21, 34, 35, 36, 37, 38
int RealEarInputOutputCurve_NL2(
    output double REIO[100],        // 真耳输入/输出曲线 (有限制)
    output double REIOunl[100],     // 真耳输入/输出曲线 (无限制)
    input double AC[9],            // 气导听阈
    input double BC[9],            // 骨导听阈
    input int graphFreq,           // 频率索引 (0=125Hz ~ 18=8000Hz)
    input int startLevel,          // 起始输入级 (dB)
    input int finishLevel,         // 结束输入级 (dB)
    input int limiting,            // 限制类型: 0=关闭, 1=宽带, 2=多通道
    input int channels,            // 通道数 (1-18)
    input int direction,           // 声音方向: 0=0度, 1=45度
    input int mic,                 // 麦克风位置: 0=自由场, 1=头表面
    input int target,              // 增益目标: 0=REIG, 1=REAG
    input double ACother[9],       // 对侧耳气导听阈
    input int noOfAids             // 助听器数量: 0=单侧, 1=双侧
) -> int                           // 返回: 0=成功
```

---

### 7. TccInputOutputCurve_NL2

```c
// 功能: 计算2cc耦合腔输入/输出曲线
// 依赖: 23, 43或44, 17或18, 21, 34, 35, 36, 37, 38
int TccInputOutputCurve_NL2(
    output double TccIO[100],       // 2cc耦合腔输入/输出曲线 (有限制)
    output double TccIOunl[100],    // 2cc耦合腔输入/输出曲线 (无限制)
    input double AC[9],            // 气导听阈
    input double BC[9],            // 骨导听阈
    input int graphFreq,           // 频率索引
    input int startLevel,          // 起始输入级 (dB)
    input int finishLevel,         // 结束输入级 (dB)
    input int limiting,            // 限制类型: 0=关闭, 1=宽带, 2=多通道
    input int channels,            // 通道数 (1-18)
    input int direction,           // 声音方向: 0=0度, 1=45度
    input int mic,                 // 麦克风位置: 0=自由场, 1=头表面
    input int target,              // 增益目标: 0=REIG, 1=REAG
    input int aidType,             // 助听器类型: 0=CIC, 1=ITC, 2=ITE, 3=BTE
    input double ACother[9],       // 对侧耳气导听阈
    input int noOfAids,            // 助听器数量: 0=单侧, 1=双侧
    input int tubing,              // 未使用
    input int vent,                // 通气孔类型
    input int RECDmeasType,        // 未使用
    output int lineType[100]       // 曲线类型: 0=实线, 1=虚线
) -> int                           // 返回: 0=成功
```

---

### 8. EarSimulatorInputOutputCurve_NL2

```c
// 功能: 计算耳模拟器输入/输出曲线
// 依赖: 23, 43或44, 17或18, 21, 34, 35, 36, 37, 38
int EarSimulatorInputOutputCurve_NL2(
    output double ESIO[100],        // 耳模拟器输入/输出曲线 (有限制)
    output double ESIOunl[100],     // 耳模拟器输入/输出曲线 (无限制)
    input double AC[9],            // 气导听阈
    input double BC[9],            // 骨导听阈
    input int graphFreq,           // 频率索引
    input int startLevel,          // 起始输入级 (dB)
    input int finishLevel,         // 结束输入级 (dB)
    input int limiting,            // 限制类型: 0=关闭, 1=宽带, 2=多通道
    input int channels,            // 通道数 (1-18)
    input int direction,           // 声音方向: 0=0度, 1=45度
    input int mic,                 // 麦克风位置: 0=自由场, 1=头表面
    input int target,              // 增益目标: 0=REIG, 1=REAG
    input int aidType,             // 助听器类型: 0=CIC, 1=ITC, 2=ITE, 3=BTE
    input double ACother[9],       // 对侧耳气导听阈
    input int noOfAids,            // 助听器数量: 0=单侧, 1=双侧
    input int tubing,              // 未使用
    input int vent,                // 通气孔类型
    input int RECDmeasType,        // 未使用
    output int lineType[100]       // 曲线类型: 0=实线, 1=虚线
) -> int                           // 返回: 0=成功
```

---

### 9. Speech_o_Gram_NL2

```c
// 功能: 计算语音图的RMS、最大值、最小值和阈值曲线
// 依赖: 23, 15或16, 21, 34, 35, 36, 37, 38
int Speech_o_Gram_NL2(
    output double Speech_rms[19],    // 语音RMS (三分之一倍频程)
    output double Speech_max[19],    // 语音最大值
    output double Speech_min[19],    // 语音最小值
    output double Speech_thresh[19], // 语音阈值
    input double AC[9],             // 气导听阈
    input double BC[9],             // 骨导听阈
    input double L,                 // 宽带信号输入级 (dB)
    input int limiting,             // 限制类型: 0=关闭, 1=宽带, 2=多通道
    input int channels,             // 通道数 (1-18)
    input int direction,            // 声音方向: 0=0度, 1=45度
    input int mic,                  // 麦克风位置: 0=自由场, 1=头表面
    input double ACother[9],        // 对侧耳气导听阈
    input int noOfAids              // 助听器数量: 0=单侧, 1=双侧
) -> int                            // 返回: 0=成功
```

---

### 10. AidedThreshold_NL2

```c
// 功能: 计算助听阈值
// 依赖: 23, 15或16, 17或18, 21, 34, 35, 36, 37, 38
int AidedThreshold_NL2(
    output double AT[19],           // 助听阈值 (三分之一倍频程)
    input double AC[9],            // 气导听阈
    input double BC[9],            // 骨导听阈
    input double CT[19],           // 压缩阈值 (三分之一倍频程)
    input int dbOption,            // 阈值显示类型: 0=dB HL, 1=dB SPL
    input double ACother[9],       // 对侧耳气导听阈
    input int noOfAids,            // 助听器数量: 0=单侧, 1=双侧
    input int limiting,            // 限制类型: 0=关闭, 1=宽带, 2=多通道
    input int channels,            // 通道数 (1-18)
    input int direction,           // 声音方向: 0=0度, 1=45度
    input int mic                  // 麦克风位置: 0=自由场, 1=头表面
) -> int                           // 返回: 0=成功
```

---

### 11. GetREDDindiv

```c
// 功能: 获取REDD数据 (三分之一倍频程)
// 依赖: 15或16 (如果返回用户输入值)
int GetREDDindiv(
    output double REDD[19],         // REDD值
    input int REDD_defValues            // 数据来源: 0=预测, 1=客户数据
) -> int                           // 返回: 0=成功
```

---

### 12. GetREDDindiv9

```c
// 功能: 获取REDD数据 (标准NAL-NL2频率)
// 依赖: 15或16 (如果返回用户输入值)
int GetREDDindiv9(
    output double REDD[9],          // REDD值
    input int REDD_defValues            // 数据来源: 0=预测, 1=客户数据
) -> int                           // 返回: 0=成功
```

---

### 13. GetREURindiv

```c
// 功能: 获取REUR数据 (三分之一倍频程)，根据麦克风位置和方向调整
// 依赖: 17或18 (如果返回用户输入值)
int GetREURindiv(
    output double REUR[19],         // REUR值
    input int REUR_defValues,           // 数据来源: 0=预测, 1=客户数据
    input int dateOfBirth,         // 出生日期 (YYYYMMDD格式)
    input int direction,           // 声音方向: 0=0度, 1=45度
    input int mic                  // 麦克风位置: 0=自由场, 1=头表面
) -> int                           // 返回: 0=成功
```

---

### 14. GetREURindiv9

```c
// 功能: 获取REUR数据 (标准NAL-NL2频率)，根据麦克风位置和方向调整
// 依赖: 17或18 (如果返回用户输入值)
int GetREURindiv9(
    output double REUR[9],          // REUR值
    input int REUR_defValues,           // 数据来源: 0=预测, 1=客户数据
    input int dateOfBirth,         // 出生日期 (YYYYMMDD格式)
    input int direction,           // 声音方向: 0=0度, 1=45度
    input int mic                  // 麦克风位置: 0=自由场, 1=头表面
) -> int                           // 返回: 0=成功
```

---

### 15. SetREDDindiv

```c
// 功能: 设置REDD数据 (三分之一倍频程)
// 依赖: 45或46 (如果设置预测值)
int SetREDDindiv(
    input double REDD[19],          // 要存储的REDD值
    input int REDD_defValues            // 数据类型: 0=预测, 1=客户数据
) -> int                           // 返回: 0=成功
```

---

### 16. SetREDDindiv9

```c
// 功能: 设置REDD数据 (标准NAL-NL2频率)
// 依赖: 45或46 (如果设置预测值)
int SetREDDindiv9(
    input double REDD[9],           // 要存储的REDD值
    input int REDD_defValues            // 数据类型: 0=预测, 1=客户数据
) -> int                           // 返回: 0=成功
```

---

### 17. SetREURindiv

```c
// 功能: 设置REUR数据 (三分之一倍频程)
// 依赖: 无
int SetREURindiv(
    input double REUR[19],          // 要存储的REUR值
    input int REUR_defValues,           // 数据类型: 0=预测, 1=客户数据
    input int dateOfBirth,          // 出生日期 (YYYYMMDD格式)
    input int direction,           // 声音方向: 0=0度, 1=45度
    input int mic                  // 麦克风位置: 0=自由场, 1=头表面
) -> int                           // 返回: 0=成功
```

---

### 18. SetREURindiv9

```c
// 功能: 设置REUR数据 (标准NAL-NL2频率)
// 依赖: 无
int SetREURindiv9(
    input double REUR[9],           // 要存储的REUR值
    input int REUR_defValues,           // 数据类型: 0=预测, 1=客户数据
    input int dateOfBirth,          // 出生日期 (YYYYMMDD格式)
    input int direction,           // 声音方向: 0=0度, 1=45度
    input int mic                  // 麦克风位置: 0=自由场, 1=头表面
) -> int                           // 返回: 0=成功
```

---

### 19. CrossOverFrequencies_NL2

```c
// 功能: 计算每个通道的交叉频率
// 依赖: 无
int CrossOverFrequencies_NL2(
    output double CFArray[],        // 交叉频率数组 (channels-1个元素)
    input int channels,            // 通道数 (1-18)
    input double AC[9],            // 气导听阈
    input double BC[9],            // 未使用
    output int FreqInCh[19]         // 返回每个频率所在的通道
) -> int                           // 返回: 0=成功
```

---

### 20. CenterFrequencies

```c
// 功能: 计算每个通道的中心频率
// 依赖: 19
int CenterFrequencies(
    output int centerF[],           // 中心频率数组
    input double CFArray[],        // 交叉频率数组 (channels-1个元素)
    input int channels             // 通道数 (1-18)
) -> int                           // 返回: 0=成功
```

---

### 21. CompressionThreshold_NL2

```c
// 功能: 计算每个三分之一倍频程的压缩阈值
// 依赖: 23
int CompressionThreshold_NL2(
    output double CT[19],           // 压缩阈值 (三分之一倍频程)
    input int bandWidth,           // 噪声带宽: 0=宽带, 1=窄带
    input int selection,           // 增益类型: 0=REIG, 1=REAG, 2=2cc耦合腔, 3=耳模拟器
    input int WBCT,                // 宽带压缩阈值
    input int aidType,             // 助听器类型: 0=CIC, 1=ITC, 2=ITE, 3=BTE
    input int direction,           // 声音方向: 0=0度, 1=45度
    input int mic,                 // 麦克风位置: 0=自由场, 1=头表面
    input int calcCh[19]           // 是否重新计算该频率: 0=否, 1=是
) -> int                           // 返回: 0=成功
```

---

### 22. CompressionRatio_NL2

```c
// 功能: 计算每个通道的压缩比
// 依赖: 23, 21, 34, 35, 36, 37, 38
int CompressionRatio_NL2(
    output double CR[],             // 压缩比 (三分之一倍频程)
    input int channels,            // 通道数 (1-18)
    input int centreFreq[],        // 每个通道的中心频率数组 (channels+1个元素)
    input double AC[9],            // 气导听阈
    input double BC[9],            // 骨导听阈
    input int direction,           // 声音方向: 0=0度, 1=45度
    input int mic,                 // 麦克风位置: 0=自由场, 1=头表面
    input int limiting,            // 限制类型: 0=关闭, 1=宽带, 2=多通道
    input double ACother[9],       // 对侧耳气导听阈
    input int noOfAids             // 助听器数量: 0=单侧, 1=双侧
) -> int                           // 返回: 0=成功
```

---

### 23. setBWC

```c
// 功能: 设置每个三分之一倍频程的带宽校正数据
// 依赖: 19 (除非已自行计算交叉频率)
int setBWC(
    input int channels,             // 通道数 (1-18)
    input double crossOver[]        // 交叉频率 (max(1, channels-1)个元素)
) -> int                           // 返回: 0=成功
```

---

### 24. getMPO_NL2

```c
// 功能: 获取最大功率输出 (MPO) 数据
// 依赖: 43或44 (仅当type==SSPL时)
int getMPO_NL2(
    output double MPO[19],          // 每个三分之一倍频程的最大功率输出
    input int type,                // MPO类型: 0=RESR, 1=SSPL
    input double AC[9],            // 气导听阈
    input double BC[9],            // 骨导听阈
    input int channels,            // 通道数 (1-18)
    input int limiting             // 限制类型: 0=关闭, 1=宽带, 2=多通道
) -> int                           // 返回: 0=成功
```

---

### 25. GainAt_NL2

```c
// 功能: 计算单个频率的增益
// 依赖: 23, 17或18, 21, 34, 35, 36, 37, 38
double GainAt_NL2(
    input int freqRequired,         // 三分之一倍频程频率索引
    input int targetType,           // 增益类型: 0=REIG, 1=REAG, 2=2cc耦合腔, 3=耳模拟器
    input double AC[9],             // 气导听阈
    input double BC[9],             // 骨导听阈
    input double L,                 // 宽带信号输入级 (dB)
    input int limiting,             // 限制类型: 0=关闭, 1=宽带, 2=多通道
    input int channels,             // 通道数 (1-18)
    input int direction,            // 声音方向: 0=0度, 1=45度
    input int mic,                  // 麦克风位置: 0=自由场, 1=头表面
    input double ACother[9],        // 对侧耳气导听阈
    input int noOfAids,             // 助听器数量: 0=单侧, 1=双侧
    input int bandWidth,            // 噪声带宽: 0=宽带, 1=窄带
    input int target,               // 增益目标: 0=REIG, 1=REAG
    input int aidType,              // 助听器类型: 0=CIC, 1=ITC, 2=ITE, 3=BTE
    input int tubing,               // 声管类型
    input int vent,                 // 通气孔类型
    input int RECDmeasType          // RECD测量方法: 0=预测, 1=测量
) -> double                         // 返回: 选定频率和目标类型的增益值
```

---

### 26. GetMLE

```c
// 功能: 获取麦克风位置效应 (MLE) 数据
// 依赖: 无
int GetMLE(
    output double MLE[19],          // MLE (三分之一倍频程)
    input int aidType,             // 助听器类型: 0=CIC, 1=ITC, 2=ITE, 3=BTE
    input int direction,           // 声音方向: 0=0度, 1=45度
    input int mic                  // 麦克风位置: 0=自由场, 1=头表面
) -> int                           // 返回: 0=成功
```

---

### 27. ReturnValues_NL2

```c
// 功能: 返回MAF、BWC和ESCD数据
// 依赖: 23
int ReturnValues_NL2(
    output double MAF[19],          // 最小可听场 (三分之一倍频程)
    output double BWC[19],          // 带宽校正 (三分之一倍频程)
    output double ESCD[19]          // 耳模拟器到耦合腔差值 (三分之一倍频程)
) -> int                           // 返回: 0=成功
```

---

### 28. GetTubing_NL2

```c
// 功能: 获取声管校正数据 (三分之一倍频程)
// 依赖: 无
int GetTubing_NL2(
    output double Tubing[19],       // 声管校正 (三分之一倍频程)
    input int tubing               // 声管类型
) -> int                           // 返回: 0=成功
```

---

### 29. GetTubing9_NL2

```c
// 功能: 获取声管校正数据 (标准NAL-NL2频率)
// 依赖: 无
int GetTubing9_NL2(
    output double Tubing9[9],        // 声管校正 (标准NAL-NL2频率)，http 协议使用 Tubing9
    input int tubing               // 声管类型
) -> int                           // 返回: 0=成功
```

---

### 30. GetVentOut_NL2

```c
// 功能: 获取通气孔校正数据 (三分之一倍频程)
// 依赖: 无
int GetVentOut_NL2(
    output double Ventout[19],      // 通气孔校正 (三分之一倍频程)
    input int vent                 // 通气孔类型
) -> int                           // 返回: 0=成功
```

---

### 31. GetVentOut9_NL2

```c
// 功能: 获取通气孔校正数据 (标准NAL-NL2频率)
// 依赖: 无
int GetVentOut9_NL2(
    output double Ventout9[9],       // 通气孔校正 (标准NAL-NL2频率)，http 协议使用 Ventout9
    input int vent                 // 通气孔类型
) -> int                           // 返回: 0=成功
```

---

### 32. Get_SI_NL2

```c
// 功能: 计算饱和指数 (SI)
// 依赖: 无
double Get_SI_NL2(
    input int s,                    // 语音级别: 0=55, 1=60, 2=65, 3=70, 4=75, 5=72, 6=69
    input double REAG[19],          // 测量的REAG (三分之一倍频程)
    input double Limit[19]          // RESR或SSPL限制 (三分之一倍频程)
) -> double                         // 返回: 选定语音级别的SI值
```

---

### 33. Get_SII

```c
// 功能: 计算语音可懂度指数 (SII)
// 依赖: 无
double Get_SII(
    input int nCompSpeed,           // 压缩速度: 0=很慢, 1=很快, 2=双重
    input double Speech_thresh[19], // 听阈(AC) + REDD_adult_avg
    input int s,                    // 语音级别: 0=55, 1=60, 2=65, 3=70, 4=75, 5=72, 6=69
    input double REAG[19],          // 测量的REAG
    input double REAGp[19],         // 测量的REAG在L+x (快速x=15, 双重x=7.5)
    input double REAGm[19],         // 测量的REAG在L-x (快速x=15, 双重x=7.5)
    input double REUR[19]           // REURindiv值
) -> double                         // 返回: 选定语音级别的SII值
```

---

### 34. SetAdultChild

```c
// 功能: 设置客户年龄
// 依赖: 无
void SetAdultChild(
    input int adultChild,          // 年龄类型: 0=成人, 1=儿童, 2=根据出生日期计算
    input int dateOfBirth           // 出生日期 (YYYYMMDD格式)
)
```

---

### 35. SetExperience

```c
// 功能: 设置客户助听器使用经验
// 依赖: 无
void SetExperience(
    input int experience           // 经验水平: 0=有经验, 1=新用户
)
```

---

### 36. SetCompSpeed

```c
// 功能: 设置压缩速度
// 依赖: 无
void SetCompSpeed(
    input int compSpeed            // 压缩速度: 0=慢速, 1=快速, 2=双重
)
```

---

### 37. SetTonalLanguage

```c
// 功能: 设置语言类型 (声调/非声调)
// 依赖: 无
void SetTonalLanguage(
    input int tonal                // 语言类型: 0=非声调, 1=声调
)
```

---

### 38. SetGender

```c
// 功能: 设置客户性别
// 依赖: 无
void SetGender(
    input int gender               // 性别: 0=未知, 1=男性, 2=女性
)
```

---

### 39. GetRECDh_indiv_NL2

```c
// 功能: 获取RECDh数据 (三分之一倍频程)，根据HA1到HA2转换调整
// 依赖: 43或44 (如果返回用户输入值)
int GetRECDh_indiv_NL2(
    output double RECDh[19],        // RECD值
    input int RECDmeasType,        // RECD测量方法: 0=预测, 1=测量
    input int dateOfBirth,         // 出生日期 (YYYYMMDD格式)
    input int aidType,             // 未使用
    input int tubing,              // 声管类型
    input int vent,                // 通气孔类型
    input int coupler,             // 耦合腔类型: 0=HA1, 1=HA2
    input int fittingDepth         // 验配深度: 0=标准, 1=深, 2=浅
) -> int                           // 返回: 0=成功
```

---

### 40. GetRECDh_indiv9_NL2

```c
// 功能: 获取RECDh数据 (标准NAL-NL2频率)，根据HA1到HA2转换调整
// 依赖: 43或44 (如果返回用户输入值)
int GetRECDh_indiv9_NL2(
    output double RECDh9[9],         // RECD值，为了做出区分，映射给 http 时应该设置为 RECDh9，
    input int RECDmeasType,        // RECD测量方法: 0=预测, 1=测量
    input int dateOfBirth,         // 出生日期 (YYYYMMDD格式)
    input int aidType,             // 助听器类型: 0=CIC, 1=ITC, 2=ITE, 3=BTE
    input int tubing,              // 声管类型
    input int vent,                // 通气孔类型
    input int coupler,             // 耦合腔类型: 0=HA1, 1=HA2
    input int fittingDepth         // 验配深度: 0=标准, 1=深, 2=浅
) -> int                           // 返回: 0=成功
```

---

### 41. GetRECDt_indiv_NL2

```c
// 功能: 获取RECDt数据 (三分之一倍频程)，根据HA1到HA2转换调整
// 依赖: 45或46 (如果返回用户输入值)
int GetRECDt_indiv_NL2(
    output double RECDt[19],        // RECD值
    input int RECDmeasType,        // RECD测量方法: 0=预测, 1=测量
    input int dateOfBirth,         // 出生日期 (YYYYMMDD格式)
    input int aidType,             // 未使用
    input int tubing,              // 声管类型
    input int vent,                // 通气孔类型
    input int earpiece,            // 耳塞类型: 0=泡沫耳塞, 1=定制耳模
    input int coupler,             // 耦合腔类型: 0=HA1, 1=HA2
    input int fittingDepth         // 验配深度: 0=标准, 1=深, 2=浅
) -> int                           // 返回: 0=成功
```

---

### 42. GetRECDt_indiv9_NL2

```c
// 功能: 获取RECDt数据 (标准NAL-NL2频率)，根据HA1到HA2转换调整
// 依赖: 45或46 (如果返回用户输入值)
int GetRECDt_indiv9_NL2(
    output double RECDt9[9],         // RECDt值，为了做出区分，映射给 http 时应该设置为 RECDt9
    input int RECDmeasType,        // RECD测量方法: 0=预测, 1=测量
    input int dateOfBirth,         // 出生日期 (YYYYMMDD格式)
    input int aidType,             // 助听器类型: 0=CIC, 1=ITC, 2=ITE, 3=BTE
    input int tubing,              // 声管类型
    input int vent,                // 通气孔类型
    input int earpiece,            // 耳塞类型: 0=泡沫耳塞, 1=定制耳模
    input int coupler,             // 耦合腔类型: 0=HA1, 1=HA2
    input int fittingDepth         // 验配深度: 0=标准, 1=深, 2=浅
) -> int                           // 返回: 0=成功
```

---

### 43. SetRECDh_indiv_NL2

```c
// 功能: 设置RECDh数据 (三分之一倍频程)
// 依赖: 39或40 (如果设置预测值)
// 注意: 要存储预测数据，必须先使用GetRECDh_indiv*()函数获取
int SetRECDh_indiv_NL2(
    input double RECDh[19]          // 要存储的RECD值
) -> int                           // 返回: 0=成功
```

---

### 44. SetRECDh_indiv9_NL2

```c
// 功能: 设置RECDh数据 (标准NAL-NL2频率)
// 依赖: 39或40 (如果设置预测值)
// 注意: 要存储预测数据，必须先使用GetRECDh_indiv*()函数获取
int SetRECDh_indiv9_NL2(
    input double RECDh9[9]           // 要存储的RECD值，为了做出区分，映射给 http 时应该设置为 RECDh9
) -> int                           // 返回: 0=成功
```

---

### 45. SetRECDt_indiv_NL2

```c
// 功能: 设置RECDt数据 (三分之一倍频程)
// 依赖: 41或42 (如果设置预测值)
// 注意: 要存储预测数据，必须先使用GetRECDt_indiv*()函数获取
int SetRECDt_indiv_NL2(
    input double RECDt[19]          // 要存储的RECD值
) -> int                           // 返回: 0=成功
```

---

### 46. SetRECDt_indiv9_NL2

```c
// 功能: 设置RECDt数据 (标准NAL-NL2频率)
// 依赖: 41或42 (如果设置预测值)
// 注意: 要存储预测数据，必须先使用GetRECDt_indiv*()函数获取
int SetRECDt_indiv9_NL2(
    input double RECDt9[9]           // 要存储的RECD值，为了做出区分，映射给 http 时应该设置为 RECDt9
) -> int                           // 返回: 0=成功
```

---

## 已弃用的函数

以下函数已被弃用，不应使用：

- **SetRECDindiv(double RECD[19])** - 使用 `SetRECDh_indiv_NL2` 或 `SetRECDt_indiv_NL2` 替代
- **SetRECDindiv9(double RECD[9])** - 使用 `SetRECDh_indiv9_NL2` 或 `SetRECDt_indiv9_NL2` 替代

---

## 使用说明

### 日期格式

- 所有日期参数使用 **YYYYMMDD** 格式
- 例如：1969 年 4 月 20 日 = `19690420`

### 数组大小

- **9 元素数组**: 标准听力测试频率
- **19 元素数组**: 三分之一倍频程频率
- **100 元素数组**: 输入/输出曲线数据

### 函数依赖

- 调用函数前必须先调用其依赖的函数
- 依赖关系在每个函数的注释中标明
- 例如：函数 2 依赖于函数 23, 21, 34, 35, 36, 37, 38

### 返回值

- 大多数函数返回 `0` 表示成功
- 部分函数直接返回计算值（如 `GainAt_NL2`, `Get_SI_NL2`, `Get_SII`）

---

**文档版本:** 1.0.0.0  
**基于:** NAL-NL2 DLL Ver 1.0.0.0 documentation  
**最后更新:** 2025-12-02
