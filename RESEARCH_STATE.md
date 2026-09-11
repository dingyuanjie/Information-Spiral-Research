# Information-Spiral-Research — 当前证据状态

更新：2026-09-11。本文是新增的证据索引与状态压缩；历史 RESEARCH_CORE_v2.md 和 ResearchCoreFullEdition.md 保留原样。判断优先服从对应原始数据、协议与可复现实验。

## 本轮已完成

问题：**高压缩、高预测保留和很小的平均闭合误差，能否保证固定宏观状态、更换其微观实现后仍使用同一动力学？**

结论：**不能。Reduced to Existing Theory。** 在满支持、全正转移的四状态 Markov 模型中，平均闭合误差可趋零，但同一宏观状态内的转移分布差异保持 TV=0.98。固定目标的一步预测信息可以保留 99.9992932%，仍不保证对罕见微观准备有效。

关键限定：满支持下的**精确**零条件互信息仍等价于本模型类别的一步强 lumpability；本轮否定的是把任意小的平均误差当作不依赖覆盖率的最坏误差保证。强 lumpability 的保证限于固定微观机制，不包含任意改变机制。

同容量对照：在互补噪声模型中，A 与 A XOR B 都只有一比特；后者精确闭合并保留固定目标的全部可预测信息。轻微破坏互补噪声关系即破坏此修复。保留什么比仅报告容量更有信息量；未发现新的理论或架构。

## 证据入口

- [完整 A–H 判断与直接证明](experiments/effective_unit_closure/closure_judgment.md)
- [精确枚举代码](experiments/effective_unit_closure/closure_enumeration.py) 与 [原始结果](experiments/effective_unit_closure/closure_results.json)
- [三领域数学案例、已有理论范围初筛](experiments/effective_unit_closure/cross_domain_cases.md)
- [历史及关联 IST 证据审计](experiments/effective_unit_closure/evidence_audit.md) 与 [哈希/协议清单](experiments/effective_unit_closure/evidence_manifest.json)

四个历史 minimal_core 实验均在独立目录复跑，输出逐字节一致。IST v0.5.1 本轮只做原始统计和代码核验：Oracle 读出不等于自然证据保留，evidence_only 不提供 Core 增益证据，尚无统一公平基线的架构优势结论。

## 以后使用候选标准时需要记录的条件

预测目标与时间尺度；表示容量/熵/数值精度口径；环境及允许输入；微观干预的实际实现；数据覆盖分布；平均与最坏误差；领域适用的边界/身份标准。不能把这些条件抹去后合成未经验证的单参数阈值。

## 尚未解决

有效状态不自动等于新的整体个体。尚无六项条件联合的充要定理、共同 scaling law、跨领域临界量或新的 downward causation 证据。物理的闭合场、生物的可遗传集体、AI 的受控预测态只完成分别建模与归约初筛，未证明三者数学同构。

下一轮最高信息问题：**加上明确的环境接口和允许动作，最小受控预测表示能否完全归约到受控 lumpability / bisimulation / PSR？若可以，整体身份需要哪个独立可检验条件？**

该下一步尚未执行；本轮不启动持续训练或后台自动研究。
