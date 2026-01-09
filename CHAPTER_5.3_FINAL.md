# Chapter 5.3 & 5.3.1 - Final Version (Interpretation A)

## 5.3 Description of the Dataset

The accuracy and usefulness of PortfoliAI depend directly on the quality and diversity of its training data. The system utilizes multiple datasets for different components:

**Primary Training Dataset for Survey Risk Model:**
The core training dataset for the investor risk profiling model is derived from a Kaggle investor survey dataset (`investors.csv`), containing 132 complete survey responses with 29 original features. This dataset captures self-reported investor preferences, demographics, and behavioral indicators through structured questionnaire responses.

**Supporting Datasets:**
1. **Customer Information Dataset** – demographic features such as age, financial goals, and monitoring behaviour (32,468 records). This dataset supports behavioral analysis and transaction-based risk modeling.

2. **Asset Information Dataset** – descriptive metadata about the instruments investors hold (836 asset records). Used for portfolio composition analysis and asset classification.

3. **Transaction Log Dataset** – over 388,000 entries capturing investor buying, selling, and holding patterns. This dataset enables behavioral risk profiling through transaction frequency, turnover ratios, and diversification metrics.

**Data Preprocessing Pipeline:**
The raw Kaggle survey dataset (`investors.csv`) underwent a comprehensive preprocessing pipeline to create the final training dataset (`survey_with_scores_and_archetypes.csv`). The preprocessing steps included:

1. **Data Cleaning**: Removal of duplicate entries, handling of missing values using mode/median imputation strategies, and validation of data types and ranges.

2. **Feature Engineering**: Transformation of categorical survey responses into numerical features:
   - Conversion of percentage ranges (e.g., "10% - 20%") to midpoint values
   - Mapping of time horizons (e.g., "3-5 years") to numeric years
   - Encoding of monitoring frequency to monthly frequency values
   - Creation of composite indices (e.g., `raw_index`) from multiple survey responses

3. **Categorical Encoding**: One-hot encoding of multi-class categorical variables:
   - Occupation types: `occupation_Salaried`, `occupation_Self-employed`, `occupation_Student`, `occupation_Others`
   - Investment avenues: `main_avenue_Equity`, `main_avenue_Mutual Funds`, `main_avenue_Bonds`, `main_avenue_Fixed Deposits`, `main_avenue_Gold / SGBs`, `main_avenue_PPF - Public Provident Fund`

4. **Target Variable Derivation**: Calculation of three target variables:
   - `survey_risk_score`: Continuous risk score (0-1 scale) derived from weighted survey responses
   - `survey_archetype`: Categorical classification (Conservative, Comfortable, Enthusiastic) based on risk score thresholds
   - `risk_raw`: Raw risk calculation value for reference

5. **Outlier Handling**: Clipping of extreme outliers beyond ±3 standard deviations using z-score analysis to prevent model bias from anomalous responses.

The final processed dataset (`survey_with_scores_and_archetypes.csv`) contains 132 samples with 28 columns: 22 engineered feature columns (inputs to the model), 3 target variables (outputs), and 3 metadata columns (timestamp, investment horizon, cluster assignment). This dataset serves as the primary training data for the Random Forest risk profiling model, achieving an R² score of 0.891 on the test set.

---

## 5.3.1 Training, Testing and Validation of the Dataset

The primary training dataset, `survey_with_scores_and_archetypes.csv`, was used to train the Random Forest risk profiling model. This dataset contains 132 samples with 28 columns, including 22 engineered feature columns and 3 target variables. Figure 5.1 presents a detailed overview of the dataset structure, including column organization, statistical summaries, and sample data.

**[SCREENSHOT PLACED HERE - Figure 5.1: Dataset Information for survey_with_scores_and_archetypes.csv]**

### Dataset Split Strategy

The dataset was split into training and testing sets using an 80/20 ratio, resulting in 105 training samples and 27 test samples. This split was performed using stratified sampling to ensure balanced representation of the three risk archetypes across both sets:

- **Conservative**: 53.8% of total samples (71 samples)
- **Comfortable**: 28.8% of total samples (38 samples)  
- **Enthusiastic**: 17.4% of total samples (23 samples)

Stratified sampling ensures that each risk category maintains its proportional representation in both training and test sets, preventing class imbalance issues that could bias model performance metrics.

### Cross-Validation and Hyperparameter Tuning

Five-fold cross-validation was employed during model development to tune hyperparameters and prevent overfitting. The cross-validation process:

1. **Partitioned the training set** (105 samples) into 5 folds of approximately 21 samples each
2. **Trained the model** on 4 folds and validated on the remaining fold
3. **Repeated the process** 5 times, ensuring each sample was used for validation exactly once
4. **Averaged performance metrics** across all folds to obtain robust estimates of model performance
5. **Selected optimal hyperparameters** based on cross-validation performance before final model training

This approach ensures that the model's performance metrics (R² = 0.891, classification accuracy ≈ 85%) are reliable and not inflated by overfitting to the training data.

### Target Variable Statistics

The target variable `survey_risk_score` exhibits the following distribution characteristics:
- **Mean**: 0.2631
- **Standard Deviation**: 0.3503
- **Range**: 0.0000 to 1.0000
- **Median**: 0.0980

The distribution shows a right-skewed pattern, with most investors clustering in the lower risk range (Conservative archetype), while a smaller proportion exhibits higher risk tolerance (Enthusiastic archetype). This distribution reflects realistic investor behavior patterns, where risk-averse individuals typically outnumber risk-seeking investors in survey populations.

### Validation Approach

The test set (27 samples) was reserved exclusively for final model evaluation and was never used during training, cross-validation, or hyperparameter tuning. This strict separation ensures unbiased performance estimates. The model achieved:

- **Regression Performance**: R² = 0.891 on the test set, indicating that 89.1% of the variance in risk scores is explained by the model
- **Classification Performance**: Approximately 85% accuracy in predicting the three risk archetypes (Conservative, Comfortable, Enthusiastic)

These results demonstrate that the engineered features effectively capture the underlying patterns in investor risk preferences, enabling accurate risk profiling from survey responses alone.

---

## Notes for Integration:

1. **Figure Reference**: Replace "Figure 5.1" with your actual figure number in the document
2. **Screenshot Placement**: Insert the terminal output screenshot from `show_dataset_info.py` at the indicated location
3. **Consistency**: This version focuses exclusively on the Kaggle survey → processed dataset pipeline, keeping the narrative clean and focused
4. **Other Datasets**: Mention that `combined_investors_clean.csv` and `far_customers_features_enhanced.csv` support other models (transaction-based, meta-models) but are not used for the primary survey risk model training



The conceptual framework is built around five interconnected components that together enable the proposed AI-powered assistant:
1.	User Interface (UI): This is the primary access point through which users interact with the system. It allows users to register an account, complete an investor profiling questionnaire, input or sync investment data, and engage with the AI assistant via a chat interface. The UI is designed to be intuitive and accessible to ensure ease of use for individuals with minimal financial or technical experience.
2.	Investor Profiling Engine: This module utilizes a machine learning classification model trained on behavioral, demographic, and psychometric data to categorize users into distinct investor types—such as conservative, moderate, or aggressive. The profiling process is initiated via a survey that captures risk appetite, investment goals, and decision-making preferences. These profiles serve as the foundation for subsequent advice and guidance.
3.	Conversational AI (LLM Integration): At the heart of the assistant lies a large language model (LLM), such as GPT, which powers natural language interactions. This component interprets user queries, offers context-aware explanations, answers financial questions, and adjusts the tone and complexity of its responses based on the user’s profile and history. The goal is to simulate a personalized, empathetic, and always-available investment coach.
4.	Portfolio Tracking System: This system allows users to manually enter or optionally sync their investment portfolios. It integrates with financial APIs to fetch real-time asset prices, enabling the system to compute performance metrics such as gains/losses, asset allocation, and historical trends. This helps users track their progress and receive feedback based on live market data.
5.	Personalized Recommendation Engine: Based on the user's investor profile and portfolio data, this engine generates personalized suggestions. These may include strategies for diversification, rebalancing, risk management, and time-based goal planning. The recommendations evolve as the system collects more behavioral and market interaction data, allowing for continual refinement of advice.


BACHELOR OF SCIENCE INFORMATICS & COMPUTER SCIENCE
ICS PROJECT II PROPOSAL ORAL EXAMINATION SCORE SHEET
Student
Name(s)
Admission No.
Project Title
Main Components Weight Score
Introduction:
Problem Statement
5
Objectives:
Specific, Measurable, Attainable, Realistic,
Timely (SMART)
5
Literature Review:
Understands the area of study,
Existing/Related Applications
The Proposed Solution
10
Presentation skills 5
Dealing with questions 5 


1.2 Problem Statement
While the expansion of digital investment platforms in Kenya has significantly improved access to financial products, it has not equally translated into confident, informed investor participation. A large proportion of new and aspiring investors continue to face two major challenges that hinder their ability to make sound, goal-aligned decisions.
First is the issue of information overload. Many platforms offer extensive but static content—ranging from investment product descriptions to market analysis—without tailoring it to the user's level of experience or immediate needs. For novice investors in particular, this deluge of technical language and unstructured options can be disorienting(Guo et al., 2023). Instead of building clarity, it often reinforces a sense of inadequacy, leading many to disengage or rely on familiar but suboptimal options such as fixed deposits, SACCOs, or land.
Second, there is a misalignment between investor personality and investment decisions. Individual differences in financial goals, risk tolerance, and behavioral traits significantly influence investment success (Amponsah et al., 2025). However, most investment tools do not assess or accommodate these differences. As a result, users often receive generic advice that does not match their needs or mindset, leading to dissatisfaction, underperformance, or poor decision-making over time.
Together, these two challenges—cognitive overload and lack of behavioral personalization—undermine the potential benefits of democratized market access. These challenges point to a deeper issue: improved access alone is not sufficient. Many emerging investors are not simply seeking entry into financial markets—they require support systems that foster clarity, relevance, and trust. In a space crowded with jargon and generalized content, the absence of personalized, contextual guidance makes it difficult for users to develop the confidence and discipline required for long-term investing. Without tools that recognize individual differences and deliver knowledge in a structured, digestible manner, digital platforms risk reinforcing the very barriers they were meant to overcome.
General Objective
To develop a web-based investment assistant that uses machine learning to identify users’ investor profiles and employs conversational AI to deliver personalized, easy-to-understand guidance—empowering users to make confident, informed financial investment decisions in the financial markets.
1.3.1 Specific Objectives
1.	To analyze the current financial investment landscape in Kenya, including user behaviors, access challenges, and adoption of digital platforms.
2.	To evaluate existing investment tools and advisory platforms with a focus on their suitability for beginner investors.
3.	To identify gaps in personalization, user education, and engagement within these tools, particularly in addressing investor confidence and decision-making.
4.	To design and implement a web-based system that uses machine learning for investor profiling and conversational AI to provide personalized investment guidance tailored to individual user traits and needs.
5.	To assess the effectiveness of the developed system in improving user confidence, understanding, and participation in financial markets.
1.3.2 Research Questions
1.	What are the key characteristics and challenges of the current financial investment landscape in Kenya, particularly for beginner investors?
2.	How effective are existing investment tools and advisory platforms in supporting personalized decision-making for new or inexperienced investors?
3.	What are the major gaps in personalization, user education, and engagement within current digital investment platforms?
4.	How can a web-based system combining machine learning and conversational AI be designed to deliver personalized investment guidance tailored to individual investor profiles?
5.	To what extent does the proposed system improve user confidence, understanding, and participation in financial markets?



Chapter three: Development Methodology
3.1 Introduction
This chapter details the methodological framework for developing the proposed AI-driven investment assistant. A mixed research paradigm will be adopted, combining exploratory analysis (to uncover latent investor behavioral patterns) with experimental modeling (to train predictive algorithms). The process begins with data acquisition (a Kaggle “Investor Behavior” survey) and thorough preprocessing, followed by feature engineering of demographic and psychometric predictors. Machine learning (ML) techniques are then applied to generate continuous investor profiles and scores. Model performance is validated using standard cross validation and error metrics. Concurrently, an Agile Scrum process guides the software development, culminating in a system architecture that integrates a React-based frontend, serverless back end, ML services in the cloud, and financial data APIs. Finally, we describe the expected deliverables: the trained ML model, a web application (PWA), documentation, testing suite, and usability logs. The final implementation refines this methodology through a hybrid survey-plus-behavioral modeling approach and deployment within a FastAPI/Supabase environment.

3.2 Research Paradigm
A mixed-method research paradigm will be adopted, combining exploratory and experimental approaches to support the understanding and prediction of investor behavior. The exploratory phase will address the lack of predefined labels in the dataset—such as “aggressive” or “conservative” investor types—through the use of unsupervised learning techniques like clustering. These methods are particularly effective for high-dimensional behavioral data and will be used to uncover latent structures or investor archetypes without relying on prior assumptions (Tumminello et al., 2011; Verbeeck et al., 2020). For instance, clustering algorithms will help identify groups of investors who exhibit similar patterns in preferences, investment habits, and financial objectives.
Concurrently, the experimental phase will involve the development and evaluation of supervised machine learning models, such as regression algorithms, to predict continuous investor attributes—including risk tolerance and personality trait scores—based on input features derived from survey responses. This will enable the generation of individualized investment insights.
By integrating data-driven pattern discovery (via exploratory clustering) with predictive modeling (via supervised learning), the approach will capture both novel and expected variations in investor behavior, resulting in a more robust and personalized profiling system.
3.2.1 Data Acquisition
The primary data source will be the publicly available "Investor Behavior on Investment Avenues" dataset from Kaggle (Investors, 2023). This dataset comprises over 1,000 individual responses, capturing a wide range of variables essential for investor profiling. It includes demographic data such as age, gender, income level, and education, as well as investment preferences, including chosen asset classes, risk appetite, and investment time horizons. Additionally, it covers behavioral attributes such as trading frequency, portfolio review cadence, and financial objectives. The dataset also incorporates self-reported psychological data, which can be mapped to the Big Five personality traits—openness, conscientiousness, extraversion, agreeableness, and neuroticism (Riar & Kumar, 2022b). This rich and multidimensional dataset will serve as the foundation for training machine learning models to uncover patterns and generate personalized investor profiles.
3.2.2 Data Preprocessing and feature engineering
To prepare the dataset for modelling, several cleaning and preparation steps will be applied to improve data quality and consistency. Unnecessary fields like timestamps will be removed. Missing values will be filled in using common techniques—such as the median for numbers and mode for categories. Categorical data like gender, education level, and occupation will be converted into numbers using one-hot or ordinal encoding, depending on the type of data. Numerical fields such as age, income, and investment frequency will be standardized using Z-score normalization so that they can be compared fairly. Outliers will be either removed or adjusted to prevent them from distorting the model. The dataset will also be checked for duplicates and errors to make sure it is clean and reliable.

After cleaning, extra features will be created to help the model better understand investor behavior and personality. These will include Big Five personality scores—Openness, Conscientiousness, Extraversion, Agreeableness, and Neuroticism—based on answers from the survey. These traits are known to affect how people make financial decisions (Jiang et al., 2024). Probabilities for each of the seven investor types—such as Risk-Averse, Cautious Planner, Passive Saver, Balanced Strategist, Opportunist, Growth Seeker, and Speculative Trader—will be calculated using clustering algorithms like k-means or Gaussian Mixture Models (GMM). These models will group similar patterns in the data and assign each user a probability score for how closely they match each profile
In the first version of the model, the focus will be on basic behavioral features that are simple to calculate. These include the contribution rate (how often and how much someone invests), review cadence (how often they check their portfolio), and time horizon (how long they plan to invest). A basic risk preference score will also be included based on whether someone prefers high-risk investments like stocks or safer ones like bonds. These features are useful for understanding different types of investors and predicting their behavior (Tumminello et al., 2011). Together, these features will create a detailed input for the machine learning models. More advanced features—such as how users describe their investment goals, how they prefer to receive information (charts, text, dashboards), or how diversified their investment preferences are—can be added later to improve the system’s accuracy and personalization.
3.2.3 Deriving Continuous Risk Score and Archetype Profile
Since the dataset does not contain predefined investor risk categories, a novel metric will be introduced to represent investor temperament. Each investor will be assigned a continuous risk score ranging from 0 to 1, where 0 indicates very conservative investment behavior and 1 represents a highly aggressive investment style. To derive this score and additional user profile features, a multi-step unsupervised learning pipeline will be applied.
The first step will involve determining the appropriate number of investor archetypes based on behavioral clustering. Guided by literature and expert input, the number of clusters will be fixed at seven. Gaussian Mixture Models (GMM) will then be employed to cluster investors using their behavioral responses. This approach provides posterior probabilities of belonging to each cluster (soft labels), allowing each investor to be associated probabilistically with multiple archetypes (Liu & Li, 2025). The GMM-derived risk score will be calculated as a weighted average of cluster-assigned risk levels.
In parallel, Principal Component Analysis (PCA) will be applied to the engineered feature space to extract dominant behavioral patterns. The first principal component—capturing the greatest variance—will be scaled to a 0–1 range and interpreted as an alternative risk metric (Greenacre et al., 2022).
To select the most representative risk score, both the GMM and PCA-derived metrics will be evaluated based on their correlation with independent behavioral signals such as equity allocation preferences and investment monitoring frequency. The method demonstrating stronger alignment with these signals will be selected as the final risk scoring approach (Jain & Kesari, 2020).
Following risk score selection, each GMM cluster will be characterized by analyzing centroid values and average behaviors across features. This will support the assignment of meaningful archetype labels (e.g., “Risk-Averse,” “Cautious Growth,” “Opportunist”) to improve interpretability.
3.2.4 Model Training
Once pseudo-labels have been generated from the unsupervised learning phase, a supervised regression model will be trained to replicate these outputs for new users. The objective will be to enable real-time inference from short survey inputs without requiring re-clustering. The training process will involve predicting four types of outputs:
1.	Continuous Risk Score: The final GMM- or PCA-derived score will serve as the regression target (Liu & Li, 2025; Greenacre et al., 2022).
2.	Archetype Probabilities: GMM posterior probabilities for each of the seven clusters will be treated as multi-output regression targets.
3.	Behavioral Metrics: Additional outputs will include continuous predictions for investment time horizon, contribution rate, and portfolio review frequency.
4.	Big Five Personality Scores: Although not available in the original dataset, these scores will be collected from new users via a short embedded BFI questionnaire. Future versions of the system may use these labeled entries to learn a mapping from behavioral profiles to psychological traits—supporting transfer learning across datasets.
The model architecture will consist of a RandomForestRegressor embedded in a MultiOutputRegressor wrapper from scikit-learn. Grid search will be applied for hyperparameter optimization, improving the generalization capability of the model. This hybrid pipeline—beginning with unsupervised clustering and followed by supervised regression—will ensure scalability and personalization while preserving model interpretability. While the initial modeling pipeline explored PCA and Gaussian Mixture Models for latent archetype discovery, the finalized approach adopted in Chapter 5 uses supervised Random Forest models for both survey-based and transaction-based predictions, fused through a meta-risk composer. This shift improved interpretability, deployment simplicity, and alignment with advisor-validated personas.

3.2.5 Model Validation and Testing
To ensure reliability, the model is validated using k-fold cross-validation. This approach checks whether the model performs consistently across different subsets of the data. In addition to statistical validation, functional testing is conducted by integrating the model into a chatbot environment. This allows simulation of real-world interactions where the system provides investment advice based on the predicted risk score.
3.3 Software Development Methodology/Approach
An Agile Scrum-inspired methodology was adopted to guide the iterative development of the AI-powered investment assistant. Although the project was developed individually, Agile principles—such as modular design, short development cycles, continuous integration, and iterative refinement—were applied to maintain clarity, adaptability, and steady progress. Each development sprint focused on a specific subsystem, beginning with sprint planning, followed by implementation, internal testing, and review.
Early sprints focused on data preprocessing, feature engineering, and model experimentation, including baseline clustering and supervised learning pipelines. As requirements became clearer, later sprints shifted toward system integration, introducing the backend service layer, real-time analytics, and conversational AI interactions.
During development, the system architecture evolved beyond the initial Firebase-based prototype to a more robust FastAPI and Supabase stack. This transition enabled reliable authentication, relational data modeling, model hosting, and real-time interactions with external APIs. Dedicated backend endpoints were created for profiling, portfolio analytics, and chatbot responses, while the frontend was implemented using lightweight HTML, CSS, and JavaScript to maintain simplicity and compatibility across devices.
Throughout the process, unit tests, Postman-driven integration tests, and exploratory scenario testing ensured that each module—authentication, profiling, analytics, and conversational logic—functioned correctly both independently and as part of the complete system. The Agile approach enabled continuous refinement, resulting in a scalable and modular architecture aligned with the project’s objectives.

3.4 System Analysis and Design
A component-based system design is employed to decompose the application into interdependent yet modular subsystems. UML diagrams are used to visualize system behavior, data relationships, and user interactions.
3.4.1 Use Case Diagram
A use case diagram will be developed to outline the key functionalities of the system. The primary actors will include the end-user and a system administrator. The diagram will capture all critical user interactions, including registration and login, completion of a risk profiling questionnaire, visualization of results, chatbot communication for investment advice, and manual entry of portfolio data. These use cases will form the backbone of the system’s functional requirements.
3.4.2 Class Diagram
A class diagram will define the logical structure of the system through several key classes. These will include User for managing authentication and demographic details, ProfileService for processing survey inputs, MLService for interacting with deployed predictive models, and PortfolioService for storing and retrieving investment records. Additional classes such as ChatSession and RecommendationEngine will handle conversation management and the generation of tailored advice, respectively. These classes will work in coordination to ensure modularity and reusability.
3.4.3 Entity Relationship Diagram (ERD)
The ERD will represent the NoSQL schema used in Firebase Firestore. Core collections will include users, risk assessments, portfolios, and chat sessions, each storing relevant documents indexed by unique user identifiers. This schema will ensure fast retrieval, scalability, and support for asynchronous data queries. Relationships among collections will be implemented through references to user IDs, enabling structured data linkage.

3.4.4 Database Schema
The database schema will define how data is stored in Firestore documents. The users collection will contain fields such as uid, email, and created_at. The risk_assessments collection will store numerical risk scores and archetype probabilities. The portfolios collection will manage user-entered asset data including names, quantities, and timestamps. The chat_sessions collection will capture conversation logs, preserving message content and time information. This document-based schema will be optimized for real-time updates and mobile accessibility.
3.4.5 System Architecture
The system architecture will follow a multi-layered model. The presentation layer will be implemented using React.js and Next.js to build a responsive and dynamic frontend. The logic layer will consist of Firebase Cloud Functions that handle key computations, form processing, and API integrations. Machine learning models will be hosted in the cloud to deliver risk profiling services. The data layer will rely on Firestore for data persistence, while external APIs such as Finnhub will provide market data for portfolio tracking. A client-side caching layer using browser storage will ensure offline availability and improved responsiveness.

3.4.6 Wireframes
Wireframes will be created to guide frontend development and define user experience. The main screens will include the onboarding interface, profiling questionnaire, risk score dashboard, portfolio entry module, and chatbot panel. These wireframes will serve as blueprints for UI design and help ensure consistency in layout and navigation across the application.

3.5 System Development Tools and Techniques
The development of the AI-driven investment assistant prototype will utilize a combination of modern web and machine learning technologies suitable for student-led academic projects. The frontend of the application will be developed using React.js, supported by Next.js to enable fast routing and server-side rendering where needed. These frameworks will allow the creation of a responsive, modular user interface optimized for both desktop and mobile environments.
The backend services will be managed using Firebase, a cloud-based platform offering user authentication, NoSQL database storage (Firestore), and hosting capabilities. Firebase will simplify deployment and reduce infrastructure complexity, making it a suitable choice for a student project with limited resources.
For machine learning tasks, the project will employ Python and libraries such as scikit-learn, Pandas, and NumPy. These tools will be used to preprocess data, train and evaluate regression models, and deploy the final predictive model. The trained model will be exported and deployed as a cloud function, accessible via a simple REST API. This will allow the React frontend to send user responses to the model and receive real-time predictions.
To provide market-related data for portfolio tracking, the Finnhub API will be integrated. This free API will supply up-to-date financial information, including stock prices and company data. Due to API limitations and for improved performance, basic caching techniques using browser local storage will be implemented to reduce the frequency of API requests.
In order to support offline access and enhance mobile usability, the web application will be designed as a Progressive Web App (PWA). This will ensure that essential features remain accessible even when internet connectivity is limited.
Design and modeling will be supported using Figma for wireframing and interface planning, while Lucidchart or equivalent tools will be used to create use case diagrams, class diagrams, and entity-relationship models.
Altogether, the selected tools and techniques will ensure that the system is lightweight, cost-effective, and functional, aligning with the objectives and constraints of a final-year academic project.
3.6 System Deliverables
The final year project will result in a functional prototype of an AI-assisted investment advisor tailored for beginner and intermediate investors. As a student project, the deliverables will focus on demonstrating core functionalities, technical feasibility, and proof of concept, rather than a production-level system.
The main deliverable will be a working web-based prototype, accessible through modern browsers, that enables users to create accounts, complete a risk profiling questionnaire, and receive feedback in the form of a dynamic risk score and categorized investor type. The application will also include a simple interface for entering and viewing personal investment portfolio data.
A conversational interface will be integrated into the system to simulate investment advice through a chatbot. This chatbot will draw from predefined response templates and basic logic linked to the user’s risk profile. The chatbot will not rely on real-time AI generation during the demonstration phase but will be designed with a modular structure to allow future integration with large language models.
The project will deliver a basic machine learning model, developed using Python and scikit-learn, capable of predicting a continuous risk tolerance score based on survey input. The model will be trained on a sample dataset and deployed to a cloud platform such as Firebase or Streamlit for integration into the prototype.
In addition, the project will include technical documentation outlining the system architecture, model training process, and implementation details. This documentation will support future development or academic evaluation. Wireframes, UML diagrams, and dataset descriptions will also be provided to illustrate the design and analytical approach taken during development.
The system will be hosted using free-tier cloud services, such as Firebase Hosting, to enable online access for demonstration purposes. A user guide and test cases will be prepared to validate core features, ensuring that the prototype meets the project objectives and can be evaluated effectively by academic supervisors.
Overall, the deliverables will demonstrate the feasibility of using AI-powered tools to support beginner investors and lay the foundation for future development beyond the scope of the academic project.


