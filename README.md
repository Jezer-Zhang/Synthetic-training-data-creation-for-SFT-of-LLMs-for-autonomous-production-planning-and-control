# Research Focus
Given the stringent data security requirements in the industry, optimizing the use of less-advanced, open-source LLMs could also bolster data security and reduce costs. This Research focuses on the performance improvement of these less-advanced models through fine-tuning. It hypothesizes that a tailored approach, employing fine-tuning with domain-specific synthetic data, can significantly improve the planning and control processes in production environments. This hypothesis is grounded in the capability of LLMs to interpret and execute complex tasks with greater accuracy when trained with relevant, high-quality data.

# Methodology
First, the physical autonomous system was modeled into event logs that LLMs can unterstand. These event logs contain sensor signal changes, actuator operation and command functions that LLM agents call. Then a dataset was created based on a brainstorm structure, which covers many real-world cases. Subsequently, based on this dataset, different fine-tuning strategies were executed and the performances were evaluated.

![video](https://github.com/Jezer-Zhang/Synthetic-training-data-creation-for-SFT-of-LLMs-for-autonomous-production-planning-and-control/blob/main/multi_media/ICRA_LLM_AT_cor.mp4)

# Results
The hypothesis that such fine-tuning could significantly enhance operational efficiencies was proved by the results, which demonstrated improvements in accuracy of production planning and control. This finding underscores the potential of integrating fine-tuned LLMs into autonomous systems, further supported by the negligible presence of catastrophic forgetting and overfitting in our results. Significantly, these results suggest the possibility of employing an open-source model such as Llama3-70B over proprietary models like GPT-4.0 for autonomous tasks.

![image](https://github.com/Jezer-Zhang/Synthetic-training-data-creation-for-SFT-of-LLMs-for-autonomous-production-planning-and-control/blob/main/multi_media/Performance_whole.png)

The performance when the temperature is set to 0 is similar to the performance when the temperature is set to 0.7. Thus, in the automation scenario,  the temperature can be set to 0 for a more consistent output.

![image](https://github.com/Jezer-Zhang/Synthetic-training-data-creation-for-SFT-of-LLMs-for-autonomous-production-planning-and-control/blob/main/multi_media/termperature_compare.png)
