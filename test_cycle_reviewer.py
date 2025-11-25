import json
from ai_researcher import CycleReviewer


def main():
    paper_latex = r"""
Title: Modelling Microbial Communities with Graph Neural Networks

ABSTRACT

Understanding the interactions and interplay of microorganisms is a great challenge with many applications in medical and environmental settings. In this work, we model bacterial communities directly from their genomes using graph neural networks (GNNs). GNNs leverage the inductive bias induced by the set nature of bacteria, enforcing permutation equivariance and granting combinatorial generalization. We propose to learn the dynamics implicitly by directly predicting community relative abundance profiles at steady state, thus escaping the need for growth curves. On two real-world datasets, we show for the first time generalization to unseen bacteria and different community structures. To investigate the prediction results more deeply, we create a simulation for flexible data generation and analyze effects of bacteria interaction strength, community size, and training data amount.

1 INTRODUCTION

Microorganisms are ubiquitous and essential: in our gut, they digest our food and influence our behavior (Cani et al., 2019); in industrial plants, they treat our wastewater (Mathew et al., 2022); their biomining ability outside of Earth was even tested on the International Space Station (Cockell et al., 2020). Accordingly, understanding their functioning and optimizing their use are crucial challenges.

Microbial communities are driven by interactions that dictate the assembly of communities and consequently microbial output. To comprehend the functioning of a community, it is necessary to characterize these interactions. Ideally, one would acquire time-series data for every combination of bacteria to obtain a complete understanding of their dynamics. However, in reality, this is not possible because the number of experiments grows exponentially with the number of bacteria. Accordingly, several challenges are faced when modeling bacterial interactions: (i) available data generally depict a single time-point of a community; (ii) models of interactions should generalize to new bacteria and communities to limit the need for additional experiments; (iii) models should be interpretable and provide insights on the system.

The most common approach to model interactions in bacterial communities is to use generalized Lotka-Volterra models (Gonze et al., 2018; van den Berg et al., 2022; Picot et al., 2023) (gLV, see Sec. 2.1). However, these deterministic models fit parameters on time-series data for each bacterium in the system: therefore, they cannot generalize to new bacteria and are limited by experimental data. Furthermore, as they only model pairwise interactions, they may fail to recover higher-order/complex interactions (Chang et al., 2023; Gonze et al., 2018; Picot et al., 2023). However, it should be noted that there is a debate in the field about whether bacterial communities are shaped by simple (Friedman et al., 2017; Goldford et al., 2018) or complex (Bairey et al., 2016; Chang et al., 2023) assembly rules. To address the potential complexity of microbial systems, neural networks are emerging as alternatives to gLV models, as they can capture complex interactions (Baranwal et al., 2022; Michel-Mata et al., 2022). For instance, Baranwal et al. (2022) fit recurrent neural networks to microbial communities of up to 26 bacteria to predict their assembly and ultimately a function of interest, namely butyrate production. Although their results are encouraging, their models are fitted on growth trajectories and rely on time-series, impeding their generalization to new bacteria and communities.

In this work, we model bacterial communities directly from bacterial genomes using graph neural networks (GNNs). Our contribution can be described as follows.

We propose using GNNs as a powerful class of function approximators to model microbial communities, such that each node in the graph represents a bacterial species and the GNN performs regression on nodes. Through the graph structure, GNNs isolate information and share parameters across nodes, thus granting permutation equivariance and generalization to unseen bacteria, and enabling the prediction of compositions of microbial communities.

We explore learning community dynamics directly from genomes: since nucleic acids are the universal information carrier of living organisms, this can, in principle, allow generalizing to any unseen microorganisms.

We propose learning dynamics implicitly by directly predicting community relative abundance profiles at steady state, thus escaping the need for growth curves.

We propose a simulation framework to facilitate exploratory benchmarks for models of microbial communities using genome features.

In practice, we evaluate the ability of conventional architectures (i.e. MLPs) and GNNs to model bacterial communities on two publicly available datasets (Friedman et al., 2017; Baranwal et al., 2022), and further explore hypotheses in simulations. Our results show that GNNs can accurately predict the relative abundances of bacteria in communities from their genomes for communities of various compositions and sizes. Furthermore, GNNs can generalize to marginally bigger communities and new bacteria not seen during training.

2 METHODS

2.1 TERMINOLOGY AND PROBLEM DEFINITION

Bacterial communities A bacterium, plural bacteria, is a unicellular microorganism. Bacteria are classified via a taxonomy based on the DNA, the finer-grained groupings being the genus, species, and strain. The bacteria in one strain are clones with almost identical DNA. In this work, we will use the species designation to refer to different bacteria. A bacterial community is formed by two or more species of bacteria that grow in the same environment. A community can be described by a set S of bacterial species. At any time t, each bacterial species si ∈S is present in the environment in abundance ni(t). We define yi(t) := ni(t)/ P j∈[1,|S|] nj(t) as the relative abundance of bacterium si at time t. Over time, these metrics vary according to the properties of each species (e.g. growth rate), as well as complex inter-species interactions. Extrinsic factors may affect the amount of bacteria in the environment, for instance, the amount of resources, but we will ignore them for simplicity as in previous work (Bashan et al., 2016). This is especially justified in the case of experimental data from controlled environments (van den Berg et al., 2022).

Generalized Lotka-Volterra model Our method learns to model community dynamics implicitly through a neural network and thus makes minimal modeling assumptions. Nevertheless, to give an intuition of how bacterial communities change over time, we now describe a simplified predictive model.

The generalized Lotka-Volterra model (Lotka, 1920; Volterra, 1926) describes the change in abundances in the environment (van den Berg et al., 2022; Gonze et al., 2018) according to

dni

dt = ni(t) · µi ·  1 −1

Ki

|S| X

j=1 ai,jnj(t)  , (1)

with S the set of bacterial species in the environment. For a given species si ∈S, µi is the growth rate and Ki represents the carrying capacity, which limits the amount of bacteria that can exist in the environment. Finally, ai,j is an interaction factor describing the effect of species si on species sj, and ai,i = 1 ∀i ∈[1, |S|].

2

Genomes Bacterial genomes consist of DNA sequences organized into genes, coding for all information related to bacterial functioning, e.g. metabolism, growth. Thus, genomes can be represented by the presence/absence of genes or groups of genes. An example of gene grouping is their mapping to the KEGG Orthology database to group them by molecular function (Moriya et al., 2007). For instance, the genome of Anaerostipes caccae carries the gene coding for the enzyme EC 1.3.8.1, which is a butyryl-CoA dehydrogenase belonging to the KEGG group KO K00248. Through the KEGG Orthology database mapping, genes coding for proteins with similar functions across species have the same annotation, and bacteria with similar molecular abilities have more similar representations.

In the context of this work, we represent genomes using feature vectors. Such vectors should have the same dimensionality and semantics across all bacteria. To represent all bacteria in a unified way, we consider all genes that occur in any genome in the pool of bacteria and record their presence/absence in the feature vector. Given an ordered set of M genes (gk)M k=0, we represent the genome of species si ∈ S as a binary indicator vector xi = (xk i )M k=0 such that xk i is one if gene gk is present in the genome of si, and zero otherwise. Hence, each bacterium, or node, has for attributes a binary vector representing the genome. For real data, the representation is taken from geanome annotations and for simulations the representation is abstracted to contain information on bacterial growth (see section 2.4).

Task Our aim is to predict the composition of bacterial communities C ⊆S at steady state from the genomes of the mixed bacteria. More specifically, we cast this task as a supervised learning problem. Assuming an equilibrium is reached at time-step T, our learning target is the observed relative abundance of each bacterial species si ∈C at equilibrium: y(T) = (y1(T), . . . , y|C|(T)). Our inputs are the feature vector representation of genomes of bacteria present in the mixture xi ∀i ∈[1, |C|]. To compare architectures with fixed length input, namely MLPS, we add null feature vectors xi = (0)M k=0 for the bacteria absent from the mix.

2.2 MODELS

Our method learns an implicit model of the dynamics of a bacterial community. Instead of estimating the parameters of a differential equation, which can then be solved to retrieve an equilibrium, we apply a flexible class of function approximators and directly regress the solution at equilibrium. MLPs constitute a simple baseline, as they can in principle approximate arbitrary functions (Cybenko,

1989). As most commonly used neural network architectures, MLPs assume that the position of each input carries a semantic value. The prediction of bacterial community dynamics, however, has an interesting property, namely permutation equivariance. This is due to the fact that a community is a set of species, and the predictions of the model should not be affected by the order in which the species are presented. For this reason, we propose to leverage Graph Neural Networks (GNNs) (Scarselli et al., 2009; Gilmer et al., 2017; Kipf & Welling, 2017; Battaglia et al., 2018) to exploit this particular inductive bias.

GNNs can be formalized as Message Passing Neural Networks (MPNNs) (Gilmer et al., 2017). A graph is described by the tuple G = (V, E), where V denotes the set of vertices and E the edges. The neighborhood of a vertex, i.e. node, v ∈V is described by N(v) = {u|{u, v} ∈E}. The attribute of each node is given by xi for i ∈[1, |V |]. In general, the attribute xi of each node in the graph is updated as follows in each message passing step:

e(i,j) = ge xi, xj  (2)

x′ i = gv xi, aggrj∈N (i) e(i,j)  . (3)

where ge and gv are arbitrary functions used for the edge and node computations respectively. The permutation-equivariant aggregation function is given by aggr. Depending on the choice of the node and edge update rules, we can recover different GNN architectures. In this work, we investigate two architectures: a spatial-convolutional GNN using the GraphSAGE implementation (Hamilton et al., 2017), and a slight variation of the message passing GNN architecture in Kipf et al. (2020), which we will refer to as MPGNN. The GATv2 (Veliˇ ckovi´c et al., 2018; Brody et al., 2022) and GCNII (Kipf & Welling, 2017; Chen et al., 2020) architectures were also tested but underperform the above models; see results in the Appendix A and Table S3. Given the lack of prior knowledge about the underlying graph topology, we use fully connected graphs such that each node is updated based on all other nodes within one message-passing step. The information propagation over k-hops can capture k-order relations between entities: the first message passing is limited to the neighboring

3

node attributes (pairwise interactions) and the next ones propagate the interactions of neighbors (bacterium ni receives information from nj and how it has been affected by others).

For GraphSAGE, the edge computation e(i,j) returns the attributes of neighboring nodes j ∈N(i), i.e. ge xi, xj  = xj. The node update function gv is given by: x′ i = W1xi + W2 · meanj∈N (i) xj, where W1 and W2 are learnable parameters. The mean is used as the aggregation function. By using k graph convolutional layers after one another, we can achieve k-hop information propagation. Finally, we have an additional linear layer at the end with sigmoid activation for the node attribute readouts.

In the MPGNN, we update the node attributes as x′ i = gv

xi, meanj∈N (i)(ge(xi, xj))  . Here, gv and ge are MLPs with l linear layers, each followed by a non-linearity, e.g. ReLU activation. Layer normalization is applied in the final layer. For the mapping from the node attributes to the outputs, we also have a linear layer with sigmoid activation. For MPGNN, k message-passing steps are equivalent to the k-hop information propagation we get by stacking k GraphSAGE layers. We treat k as a hyperparameter for both MPGNN and GraphSAGE. For MPGNN, the number and size of the hidden layers of ge and gv are both tuned as hyperparameters, more details are given in Table S2.

Models were trained with the Adam optimizer (Kingma & Ba, 2015) to minimize the Mean Squared Error (MSE). We use the coefficient of determination R2 to assess model performance on test set, with R2 = 1 −

P

i∈N(xi−b xi) P

i∈N(xi−b x) . To allow calculating R2 across communities, we center values with

each community such that b x = 0. We compute R2 on 100 bootstraps of communities and report its average and 95% confidence interval; R2 = 1 correspond to a perfect model, R2 ≤0 means the model is worse than random (i.e. predicting the mean). Implementation details, data splits, and reported metrics are detailed in Appendix A.

2.3 PUBLICLY AVAILABLE REAL DATA

We use two publicly available datasets independently recorded by separate laboratories; we describe them here and provide more details in Appendix A.2. Networks were trained independently on each.

FRIEDMAN2017 Experimental data from Friedman et al. (2017) consists of the relative abundances of 2, 3, 7, and 8-bacteria communities. The dataset contains 93 samples with 2 to 15 replicates each. Raw data was kindly provided by Friedman et al. (2017) and is now available on our project webpage https://sites.google.com/view/microbegnn.

BARANWALCLARK2022 The dataset is published by Baranwal et al. (2022), with certain samples originally produced by Clark et al. (2021). The dataset is composed of relative abundances of 459 samples of 2 to 26-bacteria communities, each replicated 1 to 9 times. When testing generalization to excluded bacteria (see Sec. 3.3), we do not attempt to generalize to (i) Holdemanella biformis (HB) as the samples containing this bacterium are only present in two community sizes (2 and 26), resulting in a small test set, and (ii) Coprococcus comes (CC), Eubacterium rectale (ER), Roseburia intestinalis (RI), and Faecalibacterium praustnitzii (FP) due to their over-representation in samples, and so the resulting small training sets.

Genomes of bacterial species were downloaded from NCBI (Sayers et al., 2022) or the ATCC Genome Portal (Yarmosh et al., 2022), annotated with the NCBI prokaryotic genome annotation pipeline Tatusova et al. (2016), and genes were mapped to the KEGG database to obtain functional groups (Moriya et al., 2007). When a specific strain’s genome was unavailable, the genome of the closest type strain was used instead. Details on strain genomes are provided in Supplementary Table S4. We used the presence/absence of each KO group as input for fitting models; KO annotations present in all genomes in a dataset were excluded.

2.4 MODELING BACTERIAL COMMUNITIES IN SIMULATION

We design a simulator for the growth of bacterial communities based on the generalized LotkaVolterra model (see Sec. 2.1), to control data parameters and specifically assess the application of GNNs to bacterial communities. This simulator is not meant to produce a faithful representation of real communities, but rather to provide a generative procedure that captures certain challenges in the data, e.g. large dimensionality, while controlling other characteristics, e.g. sample size.

4

Bacterial growth The growth of each bacterium in the community was simulated using the generalized Lotka-Volterra equation (Eq. 1), with: ln(µi) ∼N(1, 0.52) clipped to [0.5, 2], Ki ∼U(5, 15), and ai,j ∼Laplace(0, 0.22) clipped to [−2, 2], ∀i, j ∈[1, |S|]. The target relative abundance was calculated by simulating community growth until equilibrium: ni(0) = 10 ∀i ∈[1, |S|] and equilibrium was reached when dni/dt ≤10−3 ∀i ∈[1, |S|]. Theoretically, this is similar to solving the roots of Eq. 1 which implies that steady-states depend on the parameters Ki and ai,j ∀i, j ∈[1, |S|]. Given our set of parameters, all simulated communities were stable.

Bacterial genomes Bacterial genomes are generated to encode the simulated growth parameters such that there exists an approximately bijective mapping from genomes to parameters. We achieve this by rescaling parameters to [0, 1], discretizing them, and performing a simple binary encoding to ng bits as gbin = bin round (g −gmin)/(gmax −gmin) · (2ng −1)  . Although the encoding is not representative of any biological process, the mapping can be computed efficiently, provides a compact representation, and can be inverted up to discretization. This method is applied directly to the parameters µ and K, resulting in two binary vectors of size ng.

Encoding the interaction factors ai,j into the genomes of each bacteria requires an additional step. Given a bacterial community S, two intermediate ndim-dimensional vectors for each bacterium si ∈S are needed: one determining its effect on interaction partners, νs i ∈Rn, and the other determining how it is affected by others, νr i ∈Rn. These vectors should contain sufficient information, such that the influence of bacterium si on sj (encoded in ai,j) can be retrieved from νs i and νr j . For each pair of bacteria (si, sj) ∈S2, we simply reconstruct interactions through inner products: ˆ ai,j = νs i · νr j . We treat intermediate vectors as learnable parameters, and optimize them through gradient descent by minimizing the distance of the reconstructed interaction matrix from its ground truth: J = P

i∈[1,|S|] P

j∈[1,|S|](ˆ ai,j −ai,j)2. The ndim vector coordinates for both vectors are finally encoded in the genomes as described above for µ and K.

Here, we use ng = 7 for all parameters, ndim = 20 for the 25 simulated bacteria, and add 5 % of random genes. Empirically, we verify that µ, K, and νs, νr can be accurately recovered from simulated genomes.

3 EXPERIMENTS AND RESULTS

The general goal of this work is to train and evaluate neural models for the dynamics of bacterial communities, directly from their genomes. On real data (FRIEDMAN2017 and BARANWALCLARK2022), we first investigate whether in-distribution predictions of unseen bacterial communities with known bacteria are possible. Then, we evaluate the generalization of learned models to (i) larger communities and (ii) unseen bacteria with respect to those used for training. Finally, due to the scarcity of real data, we leverage our proposed simulator to produce a dense and controllable distribution over communities: by retraining models on simulated data, we are able to validate whether trends emerging in real data can be explained in a simplified setting.

3.1 CAN WE MODEL REAL COMMUNITIES? — YES

We first set out to evaluate the general feasibility of predicting bacterial community profiles from bacterial genomes using GNNs. Due to the set nature of communities, their dynamics are inherently permutation equivariant. This known property of the target function might however not be captured by universal function approximators such as MLPs. To confirm this, we train both GNNs and MLPs on the FRIEDMAN2017 dataset. When shuffling the order of bacteria within the train and test communities, the accuracy of MLPs drops significantly, clearly showing that the dynamics learned by MLPs are not equivariant to permutations, and thus fundamentally incorrect. Both MPGNN and GraphSAGE provide accurate predictions. After some parameter tuning (see Supplementary Table S2), our best model predicts unseen bacterial mixes with a goodness of fit R2 = 0.8088 and R2 = 0.7656, for FRIEDMAN2017 and BARANWALCLARK2022 respectively.

3.2 CAN WE GENERALIZE TO LARGER COMMUNITIES? — MARGINALLY.

We assess the ability of the models to generalize to communities of larger or smaller sizes. The motivation in the former case is to transfer knowledge from lab experiments on smaller communities to larger ones observed in the wild. In the latter case, the motivation is to evaluate whether one can learn a model from a large dataset of observed samples, and infer a model of bacterial interactions from it to monitor bacteria in the lab.

We train GNNs on communities with 2- and 3-bacteria and predict those with 7- and 8-bacteria from the FRIEDMAN2017 set. For the BARANWALCLARK2022 dataset, we train either on communities with 2- to 15- or 2- to 22bacteria and predict the 23- to 26-bacteria communities. The best ensemble models for each dataset have an accuracy of R2 = 0.5525, R2 = 0.2606, and R2 = 0.4486, respectively. For BARANWALCLARK2022, including communities of sizes closer to test sizes greatly improves accuracy, suggesting that interactions may be different in larger communities, hence limiting the models’ ability to generalize; we explore this hypothesis on simulated data in Sec. 2.4. This may explain why the models wrongly predict the growth of Pseudomonas citronellolis (Pci) and Serratia marcescens (Sm) in the FRIEDMAN2017 dataset. Although in the observed communities, these bacteria do not survive, the models predict a significant abundance.

5

For the BARANWALCLARK2022 data, predictions on Anaerostipes caccae (AC) are the less accurate: the relative abundance of the bacterium is largely overestimated with an MSE = 0.0185 compared to MSE = 0.0006 for the other bacteria. This difficulty to generalize to AC is consistent across our results (see Sec. 3.3). Training on larger communities to predict smaller ones does not achieve good results with all R2 lower than zero, indicating worse accuracy than predicting the average. Empirically, our results suggest that generalization to smaller communities poses different challenges with respect to generalization to larger communities.

3.3 CAN WE GENERALIZE TO UNKNOWN BACTERIA? — SORT OF.

Generalization to unseen bacteria is a challenging task that to our knowledge has not yet been performed for community growth dynamics. If successful, this suggests that models are able to extract relevant information from genomes that likely relate to biological processes causing the observed relative abundance of a bacterium in a community. This could open new possibilities, such as anticipating the effect of new pathogens on microbiomes or creating communities in an informed way by forecasting which bacteria is most likely to serve a desired purpose.

In practice, for every bacterium si ∈S we filter the training set to remove all communities that contain si, and use all communities that contain si for testing. As no parameter tuning was performed, we do not use a validation set; results are shown for the test set directly.

The results vary depending on which species was left out as an unseen bacterium. For instance, reasonable accuracies were obtained on the FRIEDMAN2017 dataset for predicting unseen bacteria Enterobacter aerogenes (Ea) and Sm (R2 = 0.5528 and R2 = 0.5796, respectively). Interestingly, these two bacteria were the most distant to the rest, being the only non-Pseudomonas. A hypothesis is that they do not interact much with the Pseudomonas, or that they both interact in a similar manner. In line with this hypothesis, for Pseudomonas, growing with either Sm or Ea led to resembling communities, making it possible for the knowledge gained from the genome of one non-Pseudomonas to be accurately transferred to the other. This hypothesis is supported by the comparable relative abundances of Pseudomonas in 2- and 3-bacteria communities with Sm or Ea. Predictions of communities with Pseudomonas chlororaphis (Pch) achieve the lowest accuracy, in fact lower than predicting the mean relative abundance for both types of models (R2 < 0). The genome of this species is not available on public databases, so the genome of the closest species had to be used instead. Hence, an uncontrolled error was introduced in the data. Furthermore, the substitute genome belongs to the same species as Pseudomonas aurantiaca (Pa), which has a different phenotype than Pch in cultures, leading to different relative abundances in communities. Nonetheless, models generalize better to Pa (R2 = 0.1279 for GraphSAGE). Hence, we can hypothesize that the models learn well from other Pseudomonas genomes, but cannot generalize well to Pch due to its substitute genome.

The results obtained on BARANWALCLARK2022 are superior to those on FRIEDMAN2017 data. This could be attributed to the larger dataset size, which includes more bacteria and community sizes, thus providing a better resolution of the feature space (a wider range of genomes to learn from) and output space (more examples of co-cultures due to the increased number of communities). Nevertheless, we report significantly lower accuracy when generalizing to communities including AC. This bacterium is not particularly phylogenetically distant from others, but is the only one that can produce butyrate from lactate and is a driver of butyrate production (Clark et al., 2021). Empirically, it inhibits the growth of CC, CH, BO, BT, BU, BC, and BY in communities of 11- to 13-bacteria while promoting the growth of CA and DL (see the abbreviations in Supplementary Table S4). However, these effects are less clear in communities of 23- to 25bacteria. The other bacterium to which models can transfer less accurately is Bacteroides thetaiotaomicron (BT). This bacterium is considered a keystone of the human gut microbiota, meaning that it drives community assembly (Banerjee et al., 2018). Consequently, communities including such a bacterium may be harder to predict due to the changes in interactions compared to communities without the bacterium, which explains the lower accuracy of the GNNs when generalizing to communities with BT. Actinobacteria, the phylum to which AC belongs, are also considered a keystone of the human microbiota (Banerjee et al., 2018). Although AC itself has not been reported to be a keystone, our results, together with the observation of butyrate production from Clark et al. (2021), suggests that it may be one. We explored this hypothesis on simulated data in Sec. 2.4.

Our results suggest that GNNs can generalize predictions of bacterial relative abundances to communities including unseen bacteria. In practice, the performance of models may still be limited due to noise in inputs (genomes) and output resolution (similar genomes but different phenotypes).

3.4 VALIDATING SOURCES OF MODEL INACCURACIES THROUGH SIMULATION

Due to the scarcity and lack of control of real data, we take advantage of the simulator introduced in Sec. 2.4 to assess whether model inaccuracies originate from community-specific features. We remark that these experiments are carried out on simulated data, generated through a simplified process, and therefore results in this section are meant to undergo further validation in the real world.

First, we investigate the effect of the density of community interactions on the performance of prediction models. We simulate communities with varying amount of interactions between bacteria by controlling the probability of an edge in the interaction matrix. We observe that, as we simulate denser interactions in the train and test sets, the GNN accuracies stay stable on average. For the MLP, we show two versions. MLP∗receives input bacteria in a fixed order. Thus, it can solely rely on positional information, and avoid extracting information from the genome. Consequently, it cannot generalize to unseen bacteria. This MLP∗shows the prediction performance that could be obtained by overfitting to each bacterium. The second version, marked MLP, receives bacteria in a shuffled order as input in training and testing. It is forced to extract all information from the genomes, but is evidently unable to make useful predictions.

Next, we test the ability of the models to generalize to unseen keystone bacteria, which could explain the drop in accuracy for certain species in Fig. 6. For that, we increase the edge density for two specific bacteria by increasing the probability of an edge to exist from 0.2 to 0.8 for these nodes only. We simulate communities, exclude each keystone from training, and predict the growth for communities including them as in Sec. 3.3. We perform the same procedure on five non-keystone bacteria for comparison. However, the results do not validate our hypothesis. This implies that GNNs are, in principle, capable of generalizing well to keystone bacteria and that other factors may explain the lack of generalization to AC and its communities in BARANWALCLARK2022. In Appendix B and Supplementary Fig. S10, we additionally study the aspect of scaling the number of bacterial species across all communities, while training on a sufficient number of communities. We find that increasing the diversity of bacteria seen during training helps generalize to unseen species, while maintaining good accuracy for seen ones.

Finally, we explore the impact of community sizes in training versus testing sets. For that, we initially assess whether we can reproduce the decrease in accuracy when generalizing to larger communities with our simulations. Crucially, while in real data higher-order interactions can drive the drop in accuracy on the test sets, this effect cannot be verified with our simulated data, as it includes only pairwise interactions. In fact, we see a decrease in accuracy when the size of the training communities is reduced compared to the test communities. Specifically, models trained on samples with communities of up to 10 bacteria cannot accurately predict communities of 16 to 25 bacteria (R2 < 0). Furthermore, we find that, in simulation, relative abundances are systematically over-estimated in predictions with larger communities. This is likely a consequence of the higher relative abundances in the smaller communities of the training set, indicating a tendency to overfit to training communities. It also suggests that in real data where over- and under-estimations are observed, other factors must influence the lack of generalization. Moreover, we report a trend of higher accuracy when a larger number of communities is used for training, while controlling for community size. We investigate this effect in more detail in Appendix B and Supplementary Fig. S9. We show that our approach can scale to more complex microbial networks of up to 200 bacterial species when provided with sufficient samples for training.

Overall, our results suggest that it is crucial to ensure that sufficient data is gathered along three axes: (1) a sufficient number of bacterial species, (2) a sufficient number of community samples, and (3) communities of size similar to target.

4 CONCLUSION

Our work sets the stage for the application of GNNs to microbial communities. These models can implicitly learn growth dynamics, and empirically outperform MLPs in terms of accuracy and generalization. Empirically, they outperform MLPs in terms of accuracy and generalization capabilities. Altogether, GNNs hold great potential for further applications. Furthermore, our results show that genomes are sufficient to learn an accurate model that can generalize predictions beyond observed communities. To our knowledge, this is the first attempt at predicting microbial community profiles from genomes directly. Recently, Lam et al. (2020) employed genome-scale metabolic models (GEMs) (van den Berg et al., 2022) adapted for microbial communities (Machado et al., 2018) to predict pairwise bacterial interactions. Hence, a potential next step would be to apply GNNs to such GEMs. Finally, our simulations provide a flexible data generation procedure, which can be used to benchmark models for bacterial growth from genomes. In the future, the simulation can be further improved to account for higher-order interactions and potentially environmental factors. Nonetheless, we hope that its accessibility will encourage the explainable ML community to develop tools to interpret GNN models of bacterial communities. As new properties emerge from microbial communities, scientific discoveries may arise from interactions between our fields.

6

REPRODUCIBILITY STATEMENT

We will make our code as well as the trained models available on our project webpage https: //sites.google.com/view/microbegnn such that all figures presented in the paper can be reproduced. The real-world datasets used in our work are open-source for which we thank the authors of Friedman et al. (2017) and Baranwal et al. (2022). The datasets can also be found on our webpage. Implementation details and training parameters are detailed in Appendix A.
"""

    # 创建论文数据结构
    paper_data = {
        "title": "Modelling Microbial Communities with Graph Neural Networks",
        # "abstract": "Understanding the interactions and interplay of microorganisms is a great challenge with many applications in medical and environmental settings. In this work, we model bacterial communities directly from their genomes using graph neural networks (GNNs). GNNs leverage the inductive bias induced by the set nature of bacteria, enforcing permutation equivariance and granting combinatorial generalization. We propose to learn the dynamics implicitly by directly predicting community relative abundance profiles at steady state, thus escaping the need for growth curves. On two real-world datasets, we show for the first time generalization to unseen bacteria and different community structures. To investigate the prediction results more deeply, we create a simulation for flexible data generation and analyze effects of bacteria interaction strength, community size, and training data amount.",
        "latex": paper_latex
    }

    print("创建测试论文...")
    print(f"论文标题: {paper_data['title']}")
    # print(f"摘要长度: {len(paper_data['abstract'])} 字符")
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