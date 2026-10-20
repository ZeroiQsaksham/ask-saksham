# Projects

## Overview of all projects
Saksham's main projects, from most to least advanced:
1. Ask Saksham - a RAG-based AI agent (this website's assistant) built with LangChain, ChromaDB and an LLM on Groq.
2. Chest X-Ray Multi-Label Diagnosis - deep learning (PyTorch, DenseNet-121) detecting 14 conditions on the NIH ChestX-ray14 dataset.
3. Rock vs Mine Prediction - machine learning (logistic regression) on sonar data, 78.6% test accuracy.
4. Data Driven India - SQL analysis of Indian census data, published on Medium.
5. Web development projects - React apps (to-do list, quiz app, blog with Firebase), a weather app and a CV website.

## Ask Saksham - personal AI agent (this website)
A RAG-based AI agent that answers visitors' questions about Saksham.
- Tech: Python, FastAPI, LangChain, Groq (GPT-OSS 120B), ChromaDB, FastEmbed, HTML/CSS/JavaScript.
- Two modes: "About Saksham" answers questions about Saksham, and "Ask Saksham (Astrologer)" explains Vedic astrology strictly from the 515-page book "Vedic Astrology: An Integrated Approach" by P.V.R. Narasimha Rao, citing chapter and page numbers.
- Astrologer mode uses hybrid search: BM25 keyword search plus embedding search, merged with Reciprocal Rank Fusion, over about 1,000 passages parsed from the PDF with chapter, section and page metadata.
- How it works: Markdown knowledge files are split by headings, turned into vector embeddings, stored in ChromaDB and retrieved with semantic search. The LLM uses tool calling to decide when to search the knowledge base, share contact details or save a message for Saksham. Answers stream back token by token, and guardrails keep it from inventing facts.
- Live demo: https://ask-saksham.onrender.com
- GitHub: https://github.com/ZeroiQsaksham/ask-saksham

## Chest X-Ray Multi-Label Diagnosis with DenseNet-121 (PyTorch)
- Goal: detect 14 thoracic conditions (such as cardiomegaly, effusion, edema, mass and pneumothorax) from a single frontal chest X-ray.
- Dataset: NIH ChestX-ray14 (about 112,000 X-ray images).
- Model: ImageNet-pretrained DenseNet-121 with a 14-output sigmoid head, because one X-ray can show several conditions at once (multi-label classification).
- Data leakage prevention: used the official NIH test list and a patient-grouped train/validation split with an automated leakage check, since one patient can have many X-rays.
- Class imbalance: binary cross-entropy with per-class positive weights (capped at 50), because rare conditions like hernia appear in only about 0.2% of images.
- Training: AdamW with a 10x higher learning rate for the new head than the pretrained backbone, OneCycle schedule, mixed precision and early stopping on validation macro ROC-AUC, on a free Kaggle GPU.
- Preprocessing: images resized once and cached in RAM; random crops, rotation and brightness/contrast jitter, but no horizontal flips (flipping would put the heart on the wrong side).
- Explainability: Grad-CAM heatmaps on the last dense block show which region of the X-ray drove each prediction.
- Status: the full training run is in progress; final test ROC-AUC results will be added when it finishes.
- GitHub: https://github.com/ZeroiQsaksham/chest-xray-densenet-pytorch

## Rock vs Mine Prediction (sonar data)
- Goal: classify whether an object is a rock or a mine from sonar signals.
- Dataset: 208 sonar readings with 60 numeric features each.
- Model: logistic regression with scikit-learn.
- Workflow: preprocessed and split the sonar data into training and test sets, trained in Google Colab.
- Results: 86.1% accuracy on training data and 78.6% accuracy on the held-out test data.
- GitHub: https://github.com/ZeroiQsaksham/M.L-Project-

## Data Driven India - SQL study of census data
- Wrote complex SQL queries on Indian census data to find patterns and trends in demographics, literacy and population statistics, uncovering significant correlations.
- Published as a Medium article: https://medium.com/@sachendrakumar090807/data-driven-india-a-sql-study-of-census-information-969030142024

## Web development projects
Saksham has also built several web projects:
- To-do list app: a React app (Create React App). GitHub: https://github.com/ZeroiQsaksham/To-do-list-
- Quiz app: a React app using Semantic UI React, SweetAlert2 pop-ups and Storybook for UI components, set up for deployment with GitHub Pages. GitHub: https://github.com/ZeroiQsaksham/quiz-app
- Blog: a React app using React Router for pages and Firebase as the backend. GitHub: https://github.com/ZeroiQsaksham/Blog
- Weather app (repository named "temperature"): an HTML, CSS and JavaScript app where you search a city and see its temperature, humidity and wind speed with weather icons. GitHub: https://github.com/ZeroiQsaksham/temperature
- Personal CV web page in HTML. GitHub: https://github.com/ZeroiQsaksham/cv
