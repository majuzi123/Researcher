import json
from ai_researcher import CycleReviewer


def main():
    paper_latex = r"""
\documentclass{article}
\usepackage{amsmath}
\usepackage{graphicx}

\title{Federated Learning with Adaptive Gradient Compression for Edge Devices}
\author{John Smith, Alice Johnson}
\date{2024}

\begin{document}

\maketitle

\begin{abstract}
Federated learning has emerged as a promising approach for training machine learning models on decentralized edge devices while preserving data privacy. However, communication overhead remains a significant bottleneck in federated learning systems. This paper proposes a novel adaptive gradient compression algorithm that dynamically adjusts compression ratios based on network conditions and model convergence state. Our method achieves up to 5x reduction in communication costs while maintaining model accuracy within 1\% of the baseline. Extensive experiments on three benchmark datasets demonstrate the effectiveness of our approach compared to existing compression techniques.
\end{abstract}

\section{Introduction}
The proliferation of edge devices and IoT sensors has generated massive amounts of distributed data. Federated learning enables model training across these devices without centralizing raw data, thus addressing privacy concerns. However, the communication overhead associated with transmitting model updates between clients and the server poses a major challenge, especially in bandwidth-constrained environments.

Existing gradient compression methods typically use fixed compression ratios, which may be inefficient under varying network conditions. Some methods adapt compression based on network bandwidth but ignore model training dynamics. Others consider model convergence but lack real-time adaptation to network fluctuations.

\section{Methodology}
Our proposed Adaptive Gradient Compression (AGC) method consists of three main components:

\subsection{Gradient Significance Estimation}
We introduce a gradient significance score based on the Fisher information matrix:
\begin{equation}
S(g_i) = \frac{|g_i|^2}{\mathbb{E}[|g_i|^2]}
\end{equation}
where $g_i$ represents the $i$-th gradient component.

\subsection{Network Condition Monitoring}
We continuously monitor available bandwidth $B_t$ and latency $L_t$ at time $t$:
\begin{equation}
C_t = \alpha \frac{B_t}{B_{max}} + (1-\alpha)(1 - \frac{L_t}{L_{max}})
\end{equation}

\subsection{Adaptive Compression}
The compression ratio $\rho_t$ is dynamically adjusted:
\begin{equation}
\rho_t = \beta \cdot C_t + (1-\beta) \cdot \frac{\|\nabla L(\theta_t)\|}{\|\nabla L(\theta_0)\|}
\end{equation}

\section{Experiments}
We evaluate our method on three datasets: CIFAR-10, Fashion-MNIST, and a real-world medical imaging dataset. Our approach achieves 4.8x communication reduction on CIFAR-10 while maintaining 98.2\% of the baseline accuracy.

\begin{table}[h]
\centering
\begin{tabular}{lccc}
\hline
Method & Comm. Reduction & Accuracy & Training Time \\
\hline
FedAvg & 1.0x & 95.1\% & 100h \\
Top-K & 3.2x & 94.8\% & 112h \\
Ours & 4.8x & 94.9\% & 98h \\
\hline
\end{tabular}
\caption{Comparison with baseline methods on CIFAR-10}
\end{table}

\section{Conclusion}
We present an adaptive gradient compression method for federated learning that dynamically adjusts compression ratios based on both network conditions and model convergence state. Our approach significantly reduces communication overhead while preserving model performance. Future work will explore extending this framework to non-IID data distributions and heterogeneous device capabilities.

\end{document}
"""

    # 创建论文数据结构
    paper_data = {
        "title": "Federated Learning with Adaptive Gradient Compression for Edge Devices",
        "abstract": "Federated learning has emerged as a promising approach for training machine learning models on decentralized edge devices while preserving data privacy. However, communication overhead remains a significant bottleneck in federated learning systems. This paper proposes a novel adaptive gradient compression algorithm that dynamically adjusts compression ratios based on network conditions and model convergence state. Our method achieves up to 5x reduction in communication costs while maintaining model accuracy within 1% of the baseline. Extensive experiments on three benchmark datasets demonstrate the effectiveness of our approach compared to existing compression techniques.",
        "latex": paper_latex
    }

    print("创建测试论文...")
    print(f"论文标题: {paper_data['title']}")
    print(f"摘要长度: {len(paper_data['abstract'])} 字符")
    print(f"LaTeX内容长度: {len(paper_data['latex'])} 字符")

    # 初始化审稿人
    print("\n初始化AI审稿人...")
    reviewer = CycleReviewer(model_size="8B")

    # 进行审稿
    print("开始审稿...")
    reviews = reviewer.evaluate([paper_data["latex"]])

    # 显示审稿结果
    if reviews and reviews[0]:
        review = reviews[0]
        print(f"\n审稿结果:")
        print(f"平均评分: {review['avg_rating']:.1f}/10")
        print(f"审稿决定: {review['paper_decision']}")

        print("\n主要优点:")
        for i, strength in enumerate(review['strength'][:3], 1):
            print(f"{i}. {strength}")

        print("\n需要改进:")
        for i, weakness in enumerate(review['weaknesses'][:3], 1):
            print(f"{i}. {weakness}")

        print("\n详细审稿意见:")
        print(review['meta_review'])


if __name__ == "__main__":
    main()