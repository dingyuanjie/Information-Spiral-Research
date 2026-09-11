# 原始证据与历史叙述核验

审计日期：2026-09-11。首先阅读 RESEARCH_CORE_v2.md，再核对实验和相关代码；其中的研究叙述不作为事实依据。原文件与已有 JSON 未改写。输入和复跑结果的 SHA256 见 [evidence_manifest.json](evidence_manifest.json)。

## 本仓库：四个有限枚举实验

四份脚本复制到独立临时目录后，使用本机 bundled Python 执行。四份新输出与原始 JSON **逐字节相同（4/4）**；主代理再次比较了两套文件的 SHA256。没有重新训练神经网络。

| 实验 | 可核验结果 | 允许保留的判断 |
|---|---|---|
| [phase_memory](../minimal_core/phase_memory_results.json) | 阶段盲一比特类最优 56.25%；带阶段状态与普通四状态类均 100% | 收益来自可用阶段信息/总状态，不构成独立周期原理 |
| [sample_efficiency](../minimal_core/sample_efficiency_results.json) | 相同规则、相同先验的两种参数化学习曲线完全相同；增加任务约束可改善指定任务表现 | 表示重命名不产生此协议下的新样本效率；任务偏好属于归纳偏置 |
| [misspecification](../minimal_core/misspecification_results.json) | 硬限制的相容收益与失配损失权衡产生依赖协议的边界 | 不能把表中阈值解释为跨领域常数 |
| [history_prior](../minimal_core/history_prior_results.json) | 两个已知任务函数下，历史计数提供分布偏好；总体反转时旧偏好可增加损失 | 归约到 Beta/Bernoulli 推断与经验频数决策，不证明周期或不断积累总有益 |

原 judgments 已注明确定性规则、有限输入、先验、额外时钟/历史信息与任务分布等限制；未发现这些核心数值与原始数据矛盾。但复现只验证代码输出一致，不能代替任务定义合理性或外部有效性检验。

## 关联 IST 仓库：本轮审阅的 v0.5.1

发现关联路径 `D:\code\InformationSpiralTransformer`，以及 `D:\code\svf`、`D:\code\svf-net`、`D:\code\StructureVitalityTheory`、`D:\code\SVT`。本轮没有完整审计所有关联仓库。

本轮选定原始文件为 [v0_5_1/results.json](D:/code/InformationSpiralTransformer/ist_v0_5/results/v0_5_1/results.json)，对应 [run_v0_5_1.py](D:/code/InformationSpiralTransformer/ist_v0_5/run_v0_5_1.py)。这里记录这一个已定位版本，不宣称已发现其他所有任务或仓库的最新实验。

代码明确使用 `HybridIST(config, "evidence_only")`，两种 Reader 条件各五个 seed，共十次运行；每次 300 步，batch 32，在 2/4/8 chunks 训练，在 2/4/8/16/32 chunks 评价，每个条件/长度/seed 128 个样本。训练把目标证据位置传给 Oracle；容量曲线评价关闭 Oracle。原始 JSON 的 split audit 记录 binding overlap=0，但共享 entity/value 词表；这不等同自然语言域外泛化。

两种 Reader 条件同时改变 gate 初值、temperature、reranker 与 contrastive loss 等，不是单因素消融。它们的差值不能唯一归因于某一个机制。

直接重新聚合原始五 seed 数据，在 32 chunks（64 facts）下：

| 条件 | 平均准确率 | 精确目标证据保留率 |
|---|---:|---:|
| oracle_current，Oracle 评价 | 0.796875 | 此行不能视为自然保留结果 |
| oracle_stable，Oracle 评价 | 0.900000 | 此行不能视为自然保留结果 |
| oracle_stable，非 Oracle，K=12 | 0.325000 | 0.1765625 |
| oracle_stable，非 Oracle，K=64 | 0.606250 | 1.0000000 |

“精确保留”由证据槽位置与目标事实位置匹配计算，区别于仅含相同 entity/value 的 same-binding retention。K=64 时精确保留全部目标仍未获得满分，说明此协议下不能只归因为证据容量；但没有进一步干预，不能唯一定位为某一个 Reader 子模块。

这份数据支持继续分离“保留证据”与“使用证据”的故障来源。它没有测得 Core 的增益，没有提供 Transformer/RNN/SSM/retrieval/compressive memory 的统一公平对照，也没有证明 IST 整体 Pareto 优势。FullEdition 中更早版本的性能叙述需要回到各自原始协议验证，不能直接外推到本版本。

本轮只重算这份 IST JSON 的统计并核对对应代码，没有 GPU 复训、权重重现或完整的模型实现审计。已有 seed 数不补足缺失的公平基线。

## 对本轮选题的影响

四个最小实验支持继续优先归约；IST 证据提示压缩后的信息内容和使用机制需要分开。由此选择可精确检验的“观测平均闭合是否足以保证微观准备后的闭合”，没有把 IST 的工程结果当成新层级或宇宙理论的证据。
