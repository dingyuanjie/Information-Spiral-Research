# 三个案例与已有理论的范围初筛

日期：2026-09-11。用途：为本轮闭合审计限定跨领域解释。以下是三个分别形式化的案例，**不是三个已完成的新实验，也不是跨领域同构证明**。文献事实与本项目拟采用的模型分开陈述。

## Case P — Physics

**Micro：** 二维周期盒中的 N 个硬球，微观态 Γ_N=((q_i,v_i))，球径 a。自由运动与弹性碰撞确定演化。

**Meso：** N 体密度的单粒子边缘分布 f_N^(1)(t,q,v)；它在有限 N 时通常与更高阶边缘耦合。特定稀薄气体、近平衡与尺度条件下，极限经线性化 Boltzmann 描述。以 Maxwell 分布 M 为参照，可写扰动 f≈M(1+δg)。归一化的扩散尺度形式为

\[
\partial_tg_\varepsilon+\varepsilon^{-1}v\cdot\nabla_qg_\varepsilon
=-\varepsilon^{-2}Lg_\varepsilon.
\]

这里 a 是粒径、ε 是无量纲尺度参数，两者不可混用。不能省略相关性、初始态与极限次序，直接把有限 N 的边缘方程宣称为闭合。

**Macro：** 碰撞不变量的矩 ρ、u、θ 是候选慢变量；例如 u=∫vgMdv。相应扩散极限的速度与温度满足线性 Stokes–Fourier 型方程

\[
\nabla\cdot u=0,\quad\partial_tu+\nabla p=\nu\Delta u,
\quad\partial_t\theta=\kappa\Delta\theta.
\]

**严格结果的边界：** Bodineau–Gallagher–Saint-Raymond 在二维硬球、近平衡扰动及受限制的联合尺度极限下，经线性化 Boltzmann 推导线性声学和 Stokes–Fourier 方程。不是从任意粒子初态到任意非线性流体方程的一般证明。[原论文](https://arxiv.org/abs/1511.03057)

**Transition：** 被消去的是细节相关性和快速速度模态，保留碰撞不变量相关慢模态；时间/空间尺度与闭合误差一起变化。流体场仍有空间自由度，“少数场”不等于整个系统只有少数实数。闭合场方程没有自动生成一个有出生、死亡和边界的流体个体。

## Case B — Biology

**Micro：** 细胞基因型、表型、位置及局部生死/转换事件。**Meso 候选：** 每个集体的细胞组成、空间结构与生命周期阶段 (M_g=(n_{g,1},n_{g,2},\ell_g,\text{geometry}))。仅保留平均合作比例不保证预测集体的存活或繁殖。

**Macro 与研究模型：** 若已能独立识别母集体和子集体，可定义集体类型 g 到 g' 的平均子代数 (K_{g'g})。在离散世代、独立繁殖、类型集合充分且没有密度依赖的多类型分枝近似中，

\[
\mathbb E[Z_{t+1}\mid Z_t]=KZ_t.
\]

这里 Z_g 是类型 g 的集体数量；稳定增长可由 K 的谱半径描述。这是项目的最小数学建模选择，不是声称下引实验已验证这个具体核，更不是完整随机过程仅靠均值就闭合。

Hammerschmidt 等的细菌实验比较包含与清除作弊类型的生命周期安排；包含作弊类型的条件下观察到发育转换和集体适合度与细胞适合度的脱耦。其证据涉及集体持续、繁殖和选择的组织方式，不只是群体状态可被压缩。[原研究](https://www.nature.com/articles/nature13884)

**Transition：** 要检验的是可识别的集体繁殖、母子关系、可遗传变异与集体/细胞选择之间的关系。强预测压缩不能替代这些测量；适合度脱耦也不应先被设成所有生物个体性的唯一充要条件。群体繁殖是研究 Darwinian individuality 的条件，不能推广为所有物理单元或每个生命个体都必须能繁殖。

**最强失败方向：** 稳定细胞团可能没有集体层级繁殖；精确群体计数动力学也可能只描述可交换个体的统计平均。需要在相同生命周期与外界条件下检验，不能从一个有限状态统计模型的闭合直接得出新生命个体。

## Case A — Artificial Intelligence

**Micro：** 行动与观测历史 (H_t=(o_0,a_0,\ldots,o_t))。对已知有限 POMDP，令转移 (T_a(s'|s))、观测核 (O(o|s',a))。

**Meso：** 后验信念 (b_t(s)=P(s_t=s\mid H_t))。在模型正确且归一化分母非零时，

\[
b_{t+1}(s')=\frac{O(o_{t+1}\mid s',a_t)\sum_sT_{a_t}(s'\mid s)b_t(s)}
{\sum_{u,s}O(o_{t+1}\mid u,a_t)T_{a_t}(u\mid s)b_t(s)}.
\]

**Macro：** 把指定动作下的未来测试概率作为预测态 (q_t=(P(\tau_i\mid H_t,\text{specified actions}))_i)。在测试集合生成所需预测空间时，可使用归一化递归更新

\[
q_{t+1}=B_{a_to_{t+1}}q_t/(b_{a_to_{t+1}}^Tq_t).
\]

PSR 原论文给出以行动条件未来预测表达状态的构造，并把所需预测维数与有限 POMDP 的状态数联系起来。[Littman–Sutton–Singh](https://proceedings.neurips.cc/paper/2001/file/1e4d36177d71bbb3558e43af9577d70e-Paper.pdf)

**Transition：** 有效自由度从随时间增长的历史变为充分的信念或预测坐标；闭合是受控、受观测驱动的递归闭合，不是无输入的自主常微分方程。PSR 与 b 可能是替代表示，不保证 q 比 b 更小，不能为了凑三层而宣称每条箭头都压缩。

IST 的 Evidence/Core 只是可实验比较的实现选择。需分别测量写入、保留、读取、绑定与适应，不因记忆存在就判定产生新层级。最新审阅的本地结果边界见 [evidence_audit.md](evidence_audit.md)。

## 可以比较什么，尚不能比较什么

三个案例都可提出“投影后演化”与“投影再演化”是否相容的问题；离散情形可写 Φ_*P_tμ≈Q_tΦ_*μ。但它们的状态空间、时间尺度、允许初始态和误差范数不同。物理案例是尺度极限，生物案例需要生命周期和母子关系，AI 案例是行动条件预测。这只是已有的约化/一致性问题形式，**不是新的跨领域不变量**。

| 候选比较量 | 必须固定的口径 | 本轮证据状态 |
|---|---|---|
| 预测信息 | 同一目标、时间跨度、条件变量 | 有限模型精确计算；三领域尚未同口径测量 |
| 压缩比 | 熵/容量/维数/精度选择其一，并报告噪声 | 不同口径不等价，物理场尤其需谨慎 |
| 闭合误差 | 分布加权或最坏误差、输入与干预集合 | 本轮已证明平均与最坏误差不能混用 |
| 鲁棒性 | 扰动对象、大小、可达性、环境范围 | 本轮只测离散微观准备，未测局部物理鲁棒性 |
| 因果有效性 | 宏观干预的微观实现与比较模型 | 不能由条件相关性定义新的 downward cause |
| 整合 | 相对于哪种分解、如何干预组件 | 无统一操作定义或跨领域测量 |
| 记忆深度 | 可观测历史、目标与采样间隔 | 本轮刷新 B，不提供长期记忆规律 |
| 边界/身份 | 界面、生命周期、外界识别规则 | 生物与物理/AI 标准不能直接互换 |

## 用户列出的已有理论：范围初筛

这张表逐项规定优先归约对象；不是一次文献穷尽检索，不把所有开放问题宣布为已被解决。

| 已有框架 | 对研究链的直接覆盖 | 仍需具体检验的环节 |
|---|---|---|
| Dynamical Systems；State Space Models | 状态、相互作用、流、反馈、递归；时间相关规则可扩展状态 | 什么观测坐标在指定尺度充分且稳健 |
| Statistical Mechanics；Nonequilibrium Physics | 由微观相互作用到分布、守恒律、输运与耗散 | 适用极限、初始相关性、误差与边界条件；参见 Case P |
| Renormalization Group；Coarse Graining | 尺度变换、有效参数、相关/无关自由度 | 是否存在可识别固定点和共同指数；不能仅由分层箭头认定 |
| Information Theory；Information Bottleneck | 对固定目标的信息保留与压缩权衡 | 目标与数据分布改变后的有效性；参见 [IB](https://arxiv.org/abs/physics/0004057) |
| Predictive State Representation；Bayesian Filtering | 历史到递归充分状态，含行动条件预测 | 模型失配、可学习性与测试集合覆盖；参见 Case A |
| Computational Mechanics | 根据完整未来分布等价类构造预测状态 | 预测意义的 causal state 不自动具有干预或个体性意义；参见 [原论文](https://arxiv.org/abs/cond-mat/9907176) |
| Control Theory | 输入输出实现、反馈、可观测性及受控状态约化 | 接入新环境/控制策略后是否仍充分 |
| Network Science | 关系图、模块与传播约束 | 图聚类不自动意味着动力学闭合或独立生命周期 |
| Causal Emergence | 不同层级的干预描述与因果效能比较 | 必须说明干预分布及微观实现；本轮先归约 [causal consistency](https://arxiv.org/abs/1707.00819) |
| Non-Markovian Dynamics | 被消去变量产生记忆与有效噪声 | 忽略记忆何时有误差控制；[Mori–Zwanzig 的研究实例](https://arxiv.org/abs/2202.10756) |
| Evolutionary Transitions in Individuality | 集体繁殖、遗传、冲突及选择层级 | 这些条件如何在特定系统实际产生；参见 Case B |
| Autopoiesis | 自生产组织与持续维持的候选个体边界 | 需给反应/生产网络与可证伪的维持标准；[原始工作](https://repositorio.uchile.cl/handle/2250/160309) 不等于一条压缩定理 |
| Active Inference | 以生成模型连接推断、行动与状态维持 | 特定假设是否成立及是否产生新定量预测；[Friston 的理论陈述](https://doi.org/10.1038/nrn2787) 不能代替本项目实验 |
| State Space Models in AI；RNN | 有限内部状态对输入序列的递归编码 | 状态大小、优化和任务分布下的保真/效率；[Mamba 原论文](https://arxiv.org/abs/2312.00752) 是既有实现参照 |
| Modern Memory Architectures；retrieval；compressive memory | 保存细节、外部检索、压缩过去表示 | Evidence/Core 分工是否有公平 Pareto 优势；[Compressive Transformer](https://arxiv.org/abs/1911.05507) 已涵盖记忆压缩构造 |

目前可保留的问题是：有效状态与作为整体存在的条件之间，是否有尚未被这些框架充分刻画的、可测的额外关系。本表没有发现这样的新核心，也没有证明它不存在。
