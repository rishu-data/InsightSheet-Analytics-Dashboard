# InsightSheet — AI-Powered Business Analytics Platform

> Transform CSV and Excel business data into interactive dashboards, customer intelligence, automated insights, forecasting, actionable business recommendations, user feedback, and Pro analytics capabilities.

![Project Status](https://img.shields.io/badge/Status-Functional%20MVP-success)
![Python](https://img.shields.io/badge/Python-3.x-blue)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Analytics-150458)
![Reflex](https://img.shields.io/badge/Framework-Reflex-purple)
![GitHub](https://img.shields.io/badge/Version%20Control-GitHub-black)

---

### 🚀 Live Demo

👉 **[Open InsightSheet Live Demo](https://insightsheet-analytics-dashboard-neon-ring.reflex.run/)**

> Explore the deployed InsightSheet application and experience the analytics dashboard, customer intelligence, RFM segmentation, forecasting, automated insights, reports, feedback system, and Pro upgrade flow.

---

## 📌 Project Overview

**InsightSheet** is a web-based business analytics application designed to help small businesses and non-technical users transform raw CSV and Excel data into meaningful business insights.

The application automatically processes uploaded sales and customer data and generates:

- Executive KPIs
- Revenue analytics
- Customer intelligence
- RFM segmentation
- Automated business insights
- Revenue forecasting
- Profitability analysis
- Data-quality analysis
- Downloadable reports
- Actionable business recommendations

InsightSheet also includes a **Review & Feedback system** and a **Free/Pro pricing structure** to support continuous product improvement and future SaaS monetization.

### 🎯 Goal

The goal is to reduce the manual effort required to analyze spreadsheet-based business data and convert raw information into clear, decision-ready insights.

---

## 💼 Business Problem

Small businesses often store their sales and customer information in spreadsheets but may not have dedicated data analysts or Business Intelligence infrastructure.

As a result, answering basic business questions can require significant manual work.

Examples include:

- How much revenue did we generate?
- Is revenue growing or declining?
- Which products generate the most revenue?
- Which customers contribute the most revenue?
- Which customers may be becoming inactive?
- How dependent is the business on a small number of customers?
- Which products are growing or declining?
- Which customer segments require attention?
- What actions should the business consider?

**InsightSheet addresses these problems by automating the analytics workflow from file upload to business recommendations.**

---

## 🎯 Project Objectives

- Automate sales and customer data analysis
- Reduce manual spreadsheet analysis
- Provide executive-level KPIs
- Identify revenue and product trends
- Analyze customer purchasing behavior
- Detect potentially inactive customers
- Segment customers using RFM analysis
- Generate plain-English business insights
- Provide forecasting capabilities
- Generate downloadable reports
- Make analytics accessible to non-technical users
- Collect user feedback for continuous product improvement
- Provide a foundation for SaaS-style monetization

---

# 🚀 Key Features

## 📂 Smart CSV & Excel Upload

- CSV and Excel file support
- User-friendly file upload workflow
- Automatic data processing
- Automatic column detection
- Blank-row handling
- Data validation
- Missing/unreadable date detection
- Support for real-world business datasets

---

## 📊 Executive Dashboard

Provides high-level business performance indicators including:

- Total Revenue
- Total Orders
- Average Order Value (AOV)
- Total Customers
- Repeat Customer Rate
- Revenue Trends
- Customer Concentration
- Key Business Alerts

The dashboard is designed to provide a quick executive overview before deeper analysis.

---

## 📈 Sales & Revenue Analytics

InsightSheet analyzes sales performance across time and business dimensions.

### Revenue Analysis

- Revenue over time
- Monthly revenue trends
- Peak and weakest months
- Revenue growth and decline
- Month-over-Month comparison
- Month-to-Date comparison

### Product Analysis

- Top products by revenue
- Product revenue contribution
- Fastest-growing products
- Declining products
- Product performance trends

### Customer Analysis

- Top customers by revenue
- Customer revenue contribution
- Order frequency
- Repeat purchase behavior
- Customer concentration risk

---

## 👥 Customer Intelligence

InsightSheet provides customer-level analytics to help identify retention opportunities and business risks.

### Customer Metrics

- Unique customers
- Repeat customers
- Repeat customer rate
- Customer revenue contribution
- Customer purchase frequency

### Inactive Customer Detection

Customers with no purchase activity for **60+ days** can be flagged as potentially inactive.

The application can identify:

- Number of inactive customers
- High-value inactive customers
- Historical revenue associated with potentially inactive customers
- Suggested re-engagement opportunities

> **Note:** Historical revenue associated with inactive customers should not be interpreted as guaranteed future revenue loss.

---

## 🧠 RFM Customer Intelligence

InsightSheet includes **RFM (Recency, Frequency, Monetary)** analysis for customer segmentation.

### Recency

Measures how recently a customer made a purchase.

### Frequency

Measures how frequently a customer places orders.

### Monetary

Measures the total revenue generated by a customer.

RFM analysis helps identify different customer behavior patterns and prioritize retention and engagement activities.

### Example Segments

- 🏆 Champions
- 💎 Loyal Customers
- 📈 Potential Loyalists
- 🆕 New Customers
- ⚠️ At Risk
- 🚨 Cannot Lose Them
- 💤 Potentially Inactive

---

## 🤖 Automated Business Insights

InsightSheet converts analytical results into plain-English business insights.

Examples include:

- Revenue growth or decline alerts
- Top-performing product identification
- Declining product detection
- Customer concentration warnings
- Inactive customer alerts
- Customer retention opportunities
- Business recommendations

> Insights are generated from the uploaded dataset rather than relying on fixed sample values.

---

## 📈 Forecasting

InsightSheet provides revenue forecasting capabilities to help users understand potential future performance and support business planning.

Forecast results should be interpreted together with:

- Data quality
- Dataset size
- Historical coverage
- Business seasonality

---

## 💰 Profitability Analysis

InsightSheet includes profitability-focused analytics to help users understand business performance beyond revenue.

The profitability module can support analysis such as:

- Revenue performance
- Profit performance
- Profitability trends
- Product profitability
- Customer profitability
- Performance comparison

---

## 📄 Reporting & Export

Users can generate and export analytical outputs through:

- PDF reports
- CSV exports
- Excel exports

This allows users to share insights with business stakeholders and maintain downloadable analytical records.

---

# ⭐ Review & Feedback System

InsightSheet includes an integrated **Review & Feedback** feature that allows users to share their experience with the platform.

### Feedback Features

Users can:

- ⭐ Give a 1–5 star rating
- Select a feedback category
- Submit written feedback
- Share suggestions
- Submit improvement ideas

### Feedback Categories

- Overall Experience
- Dashboard
- Analytics
- AI Insights
- RFM Analysis
- Forecasting
- Reports & Exports
- Data Upload
- Other

After submitting feedback, users receive a confirmation message.

The feedback system helps collect user opinions and identify areas for future product improvement.

---

# 💳 Pricing & Pro Upgrade

InsightSheet is designed around a simple **Free + Pro** model.

## 🆓 Free Plan

### ₹0

Includes:

- CSV / Excel upload
- Basic KPIs
- Basic dashboard
- Basic analytics
- Basic data-quality checks
- Limited reports

---

## 🚀 Pro Plan

### ₹199 / month

Includes:

- Advanced analytics
- RFM customer segmentation
- Sales forecasting
- Profitability analytics
- AI-powered insights
- Ask AI support
- PDF reports
- Excel reports
- Advanced dashboard analysis
- Higher usage limits

### Upgrade to Pro

The application includes an **"Upgrade to Pro — ₹199/month"** payment/upgrade button designed to connect with an external checkout or payment link.

Payment credentials and secret keys are kept outside the application source code.

> Payment processing is handled through the configured external checkout system rather than exposing payment secrets in the frontend.

---

# 🔄 Data Analytics Workflow

```text
CSV / Excel Upload
        ↓
File Validation
        ↓
Data Cleaning
        ↓
Column Detection
        ↓
Date & Numeric Processing
        ↓
Business KPI Calculation
        ↓
Sales & Revenue Analytics
        ↓
Customer Intelligence
        ↓
RFM Segmentation
        ↓
Automated Insights
        ↓
Forecasting
        ↓
Profitability Analysis
        ↓
Reports & Exports
        ↓
Business Recommendations
        ↓
User Feedback
        ↓
Product Improvement
```

---

# 💡 Business Recommendations

InsightSheet converts analytical findings into actionable business recommendations.

Based on the uploaded business data, the application can highlight opportunities and potential risks such as:

- 🔄 Re-engage high-value inactive customers
- 📉 Investigate significant revenue declines
- 🚀 Promote high-growth products
- ⚠️ Review declining product performance
- 👥 Monitor customer concentration risk
- 📦 Plan inventory around seasonal demand
- 📢 Optimize marketing around high-performing products
- ❤️ Prioritize customer retention opportunities
- 💰 Identify high-value customers and products
- 📊 Monitor important business KPIs and trends

The recommendations are generated from the analytical results of the uploaded dataset and should be reviewed within the actual business context.

---

# 🛠️ Technology Stack

### Programming & Data Analytics

- Python
- Pandas
- OpenPyXL

### Application Framework

- Reflex

### Visualization

- Plotly

### Reporting & Export

- ReportLab
- CSV
- Excel

### Version Control

- Git
- GitHub

---

# 🧪 Multi-Dataset Validation

InsightSheet has been tested using multiple datasets with different sizes and business characteristics to verify that the analytics dynamically adapt to uploaded data.

## 📊 Sample Business Sales Dataset

- Approximately **$200K revenue**
- **159 orders**
- **12 customers**
- Revenue and product analysis
- Customer concentration analysis
- Inactive customer detection
- Automated business recommendations

## 📱 Mobile Sales Dataset

- Approximately **$769M revenue**
- **3,835 orders**
- **988 customers**
- Revenue trend analysis
- Product performance analysis
- Customer inactivity analysis
- Automated recommendations

## 🛒 Superstore Dataset

- Approximately **$2.29M revenue**
- **5,009 orders**
- **793 customers**
- **98.5% repeat customer rate**
- Monthly sales analysis
- Product performance analysis
- Customer-level analysis
- Inactive customer detection
- Customer concentration analysis

### 🎯 Validation Objective

The application was tested across multiple datasets to verify that:

- KPIs are dynamically calculated
- Customer analytics adapt to uploaded data
- Product analytics are data-driven
- Alerts are generated from actual results
- Recommendations are based on analytical findings
- The application does not rely on fixed sample values

---

# 🧹 Data Quality Handling

InsightSheet is designed to work with real-world business datasets and includes validation for common data-quality issues.

The application can identify and handle scenarios such as:

- Missing values
- Blank rows
- Missing dates
- Unreadable dates
- Inconsistent date information
- Numeric data processing issues
- Missing required business columns
- Invalid or unsupported datasets
- General dataset validation

Data-quality warnings are surfaced to help users understand potential limitations in their analysis.

---

# 📊 Analytics Modules

| Module | Key Capabilities |
|---|---|
| 📊 Executive Analytics | Revenue, Orders, AOV, Customers, Repeat Rate, Trends |
| 📈 Sales Analytics | Revenue Trends, MoM Growth, Monthly Performance |
| 📦 Product Analytics | Top Products, Revenue Contribution, Growth, Decline |
| 👥 Customer Analytics | Top Customers, Revenue Contribution, Repeat Behavior |
| 🧠 Customer Intelligence | RFM, Recency, Frequency, Monetary |
| ⚠️ Retention Analytics | Inactive Customers, Retention Opportunities |
| 📈 Forecasting | Revenue Forecasting & Future Performance |
| 💰 Profitability | Profit, Product Profitability, Customer Profitability |
| 🤖 AI Insights | Automated Business Insights & Recommendations |
| 📄 Reporting | PDF, CSV & Excel Reports |
| ⭐ Feedback | Ratings, Categories & Written Feedback |
| 💳 Monetization | Free Plan, Pro Plan & Upgrade Flow |

---

# 📸 Screenshots

Application screenshots will be documented here to showcase the major analytics modules.

### Recommended Screenshots

1. Executive Dashboard
2. Revenue Analytics
3. Customer Intelligence
4. RFM Customer Segmentation
5. Automated Business Insights
6. Forecasting
7. Profitability Analysis
8. Review & Feedback
9. Pricing / Pro Upgrade

Screenshots will be stored inside:

assets/screenshots/
```text
assets/
└── screenshots/
    ├── executive-dashboard.png
    ├── revenue-analytics.png
    ├── customer-intelligence.png
    ├── rfm-analysis.png
    ├── automated-insights.png
    ├── forecasting.png
    ├── profitability.png
    ├── feedback.png
    └── pricing.png
```

---

# 💼 Business Value

InsightSheet is designed to help businesses move from:

```text
Raw Data
    ↓
Analysis
    ↓
Insights
    ↓
Recommendations
    ↓
Business Action
```
Instead of manually analyzing spreadsheets, users can upload their business data and quickly understand:
Revenue performance
Customer behavior
Product performance
Retention risks
Growth opportunities
Customer concentration
Business trends
Actionable recommendations
The addition of the Review & Feedback system and Free/Pro upgrade structure also provides a foundation for developing InsightSheet into a scalable analytics product.

---

# ⚠️ Limitations

- Forecast quality depends on the amount and quality of historical data.
- Customer inactivity thresholds may need to be customized for different businesses.
- Automated recommendations should be reviewed within the actual business context.
- Analysis depends on the availability of appropriate business columns.
- Data-quality issues can affect analytical accuracy.
- Forecasts should not be treated as guaranteed future results.
- Payment functionality depends on the configured external checkout/payment provider.

---

# 📌 Project Status

## 🟢 Functional Analytics MVP

InsightSheet currently supports:

- ✅ CSV and Excel data upload
- ✅ Data cleaning and validation
- ✅ Automatic column detection
- ✅ Executive KPI analysis
- ✅ Sales and revenue analytics
- ✅ Customer intelligence
- ✅ Inactive customer detection
- ✅ Customer concentration analysis
- ✅ RFM customer segmentation
- ✅ Automated business insights
- ✅ Revenue forecasting
- ✅ Profitability analysis
- ✅ PDF reporting
- ✅ CSV and Excel exports
- ✅ Review & Feedback system
- ✅ 1–5 star rating
- ✅ Free/Pro pricing structure
- ✅ Pro upgrade flow

The application has been validated using multiple datasets.

---

# 🔮 Future Scope

Potential future enhancements include:

- Customer Cohort Analysis
- Customer Lifetime Value (CLV)
- Advanced predictive analytics
- Custom business-defined KPIs
- User authentication
- Saved dashboards
- Multi-user workspaces
- Cloud database integration
- Full SaaS subscription management
- Verified payment processing
- Advanced customer retention modeling
- Admin feedback management dashboard
- AI-powered conversational analytics
- Custom report generation
- Real-time business monitoring

---

# 🧠 Skills Demonstrated

This project demonstrates practical skills in:

### 📊 Data Analytics

- Business Analytics
- Data Analysis
- Data Cleaning
- Data Validation
- Exploratory Data Analysis
- KPI Development
- Revenue Analysis
- Customer Analytics
- Product Analytics

### 👥 Customer Intelligence

- RFM Segmentation
- Recency Analysis
- Frequency Analysis
- Monetary Analysis
- Customer Retention Analysis
- Customer Concentration Analysis

### 📈 Business Intelligence

- Dashboard Development
- Business Reporting
- Data Visualization
- Automated Insights
- Business Recommendations
- Forecasting
- Profitability Analysis

### 💻 Programming & Tools

- Python
- Pandas
- OpenPyXL
- Plotly
- ReportLab
- Reflex
- Git
- GitHub

### 🚀 Product & SaaS

- Product Thinking
- SaaS Product Design
- Free/Pro Pricing Model
- Feedback System Design
- User Experience
- Monetization Flow

---

# ⚖️ Disclaimer

InsightSheet is developed as a portfolio and analytics demonstration project.

Automated insights, forecasts, recommendations, and business analytics should be validated against the actual business context and underlying data before being used for operational or financial decisions.

---

# 👨‍💻 Author

## Rishu Singh

**B.Tech CSE (Data Science)**

**Data Analytics | Business Intelligence | SQL | Power BI**

### Connect With Me

- GitHub: [@rishu-data](https://github.com/rishu-data)
- LinkedIn: [Rishu Singh](https://www.linkedin.com/in/rishu-singh-51512b3b3)

---

## ⭐ Support the Project

If you find **InsightSheet** useful or interesting, consider giving the repository a ⭐ **star**.

Your support helps improve the project and encourages further development.

