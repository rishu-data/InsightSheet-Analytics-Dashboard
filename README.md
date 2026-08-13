# InsightSheet — AI-Powered Business Analytics Platform

> Transform CSV and Excel business data into interactive dashboards, customer intelligence, automated insights, forecasting, and actionable business recommendations.

![Project Status](https://img.shields.io/badge/Status-Functional%20MVP-success)
![Python](https://img.shields.io/badge/Python-3.x-blue)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Analytics-150458)
![Reflex](https://img.shields.io/badge/Framework-Reflex-purple)
![GitHub](https://img.shields.io/badge/Version%20Control-GitHub-black)

---

## 📌 Project Overview

**InsightSheet** is a web-based business analytics application designed to help small businesses and non-technical users transform raw CSV and Excel data into meaningful business insights.

The application automatically processes uploaded sales and customer data and generates executive KPIs, revenue analytics, customer intelligence, RFM segmentation, automated business insights, forecasting and downloadable reports.

The goal is to reduce the manual effort required to analyze spreadsheet-based business data and convert raw information into clear, decision-ready insights.

---

## 🚀 Live Demo

👉 **[Launch InsightSheet](https://insightsheet-analytics-dashboard-neon-ring.reflex.run/)**

Upload your CSV or Excel business dataset and explore automated analytics, customer intelligence, RFM segmentation, forecasting, and actionable business recommendations.

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

**InsightSheet** addresses these problems by automating the analytics workflow from file upload to business recommendations.

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
- Revenue trends
- Customer concentration
- Key business alerts

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

> Historical revenue associated with inactive customers should not be interpreted as guaranteed future revenue loss.

---

# 🧠 RFM Customer Intelligence

InsightSheet includes **RFM (Recency, Frequency, Monetary) analysis** for customer segmentation.

### Recency

Measures how recently a customer made a purchase.

### Frequency

Measures how frequently a customer places orders.

### Monetary

Measures the total revenue generated by a customer.

RFM analysis helps identify different customer behavior patterns and prioritize retention and engagement activities.

Example segments can include:

- Champions
- Loyal Customers
- Potential Loyalists
- New Customers
- At Risk
- Cannot Lose Them
- Potentially Inactive

---

# 🤖 Automated Business Insights

InsightSheet converts analytical results into plain-English business insights.

Examples include:

- Revenue growth or decline alerts
- Top-performing product identification
- Declining product detection
- Customer concentration warnings
- Inactive customer alerts
- Customer retention opportunities
- Business recommendations

The insights are generated from the uploaded dataset rather than relying on fixed sample values.

---

# 📈 Forecasting

InsightSheet provides revenue forecasting capabilities to help users understand potential future performance and support business planning.

Forecast results should be interpreted together with the quality, volume, and historical coverage of the uploaded dataset.

---

# 📄 Reporting & Export

Users can generate and export analytical outputs through:

PDF reports
CSV exports
Excel exports

This allows users to share analytical findings with business stakeholders and maintain downloadable analytical records.

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
Reports & Exports
```

---

# 💡 Business Recommendations

InsightSheet converts analytical findings into actionable business recommendations, such as:

- Re-engage high-value inactive customers
- Investigate significant revenue declines
- Promote high-growth products
- Review declining product performance
- Monitor customer concentration risk
- Plan inventory and marketing around seasonal demand
- Prioritize customer retention opportunities

---

# 🛠️ Technology Stack

### Programming & Data Analytics

- Python
- Pandas

### Application Framework

- Reflex

### Version Control

- Git
- GitHub

---

# 🧪 Multi-Dataset Validation

InsightSheet has been tested with multiple datasets of different sizes and business characteristics to verify that analytics dynamically adapt to the uploaded data.

### Sample Business Sales Dataset

- Approximately $200K revenue
- 159 orders
- 12 customers
- Revenue and product analysis
- Customer concentration analysis
- Inactive customer detection
- Automated business recommendations

### Mobile Sales Dataset

- Approximately $769M revenue
- 3,835 orders
- 988 customers
- Revenue trend analysis
- Product performance analysis
- Customer inactivity analysis
- Automated recommendations

### Superstore Dataset

- Approximately $2.29M revenue
- 5,009 orders
- 793 customers
- 98.5% repeat customer rate
- Monthly sales analysis
- Product performance analysis
- Customer-level analysis
- Inactive customer detection
- Customer concentration analysis

### Validation Objective

The application was tested across multiple datasets to verify that KPIs, customer analytics, product analysis, alerts, and recommendations are dynamically calculated from the uploaded data rather than relying on fixed sample values.

---

# 🧹 Data Quality Handling

InsightSheet is designed to work with real-world business data and includes validation for common data-quality issues.

The application can identify and handle scenarios such as:

- Missing values
- Blank rows
- Missing or unreadable dates
- Inconsistent date information
- Numeric data processing
- Required business-column detection
- Dataset validation

Data-quality warnings are surfaced to help users understand potential limitations in their analysis.

---

# 📊 Analytics Modules

### Executive Analytics

- Total Revenue
- Total Orders
- Average Order Value
- Total Customers
- Repeat Customer Rate
- Revenue Trends

### Product Analytics

- Top Products
- Revenue Contribution
- Product Growth
- Declining Products
- Product Performance Trends

### Customer Analytics

- Top Customers
- Customer Revenue Contribution
- Repeat Purchasing Behavior
- Customer Concentration
- Inactive Customer Detection

### Customer Intelligence

- RFM Segmentation
- Recency Analysis
- Frequency Analysis
- Monetary Analysis
- Customer Retention Opportunities

### Forecasting & Reporting

- Revenue Forecasting
- PDF reports
- CSV reports
- Excel reports

---

# 📸 Screenshots

Application screenshots will be documented here to showcase the major analytics modules.

Recommended screenshots include:

1. Executive Dashboard
2. Revenue Analytics
3. Customer Intelligence
4. RFM Customer Segmentation
5. Automated Business Insights
6. Forecasting
7. Reports & Exports

> Screenshots will be added to the `assets/screenshots/` directory.

---

# 💼 Business Value

InsightSheet is designed to help businesses move from:

**Raw Data → Analysis → Insights → Action**

Instead of manually analyzing spreadsheets, users can upload their business data and quickly understand:

- Revenue performance
- Customer behavior
- Product performance
- Retention risks
- Growth opportunities
- Customer concentration
- Business recommendations

This makes the platform useful for business owners, analysts, sales teams, customer success teams, and management.

---

# ⚠️ Limitations

- Forecast quality depends on the amount and quality of historical data.
- Customer inactivity thresholds may need to be customized for different businesses.
- Automated recommendations should be reviewed within the actual business context.
- Analysis depends on the availability of appropriate business columns.
- Data-quality issues can affect analytical accuracy.

---

# 📌 Project Status

🟢 **Functional Analytics MVP**

InsightSheet currently supports:

- CSV and Excel data upload
- Data cleaning and validation
- Automatic column detection
- Executive KPI analysis
- Sales and revenue analytics
- Customer intelligence
- Inactive customer detection
- Customer concentration analysis
- RFM customer segmentation
- Automated business insights
- Revenue forecasting
- PDF reporting
- CSV and Excel exports

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
- SaaS subscription functionality
- Advanced customer retention modeling

---

# 🧠 Skills Demonstrated

This project demonstrates practical skills in:

- Business Analytics
- Data Analysis
- Data Cleaning
- Data Validation
- Exploratory Data Analysis
- Python
- Pandas
- Customer Analytics
- RFM Segmentation
- Revenue Analysis
- KPI Development
- Business Intelligence
- Data Visualization
- Automated Insight Generation
- Dashboard Development
- Business Problem Solving
- Git & GitHub
- Product Thinking

---

# ⚖️ Disclaimer

InsightSheet is developed as a portfolio and analytics demonstration project.

Automated insights, forecasts, and recommendations should be validated against the actual business context and underlying data before being used for operational or financial decisions.

---

# 👨‍💻 Author

**Rishu Singh**

B.Tech CSE (Data Science)  
Data Analytics | Business Intelligence | SQL | Power BI

**GitHub:** [@rishu-data](https://github.com/rishu-data)

**LinkedIn:** [Rishu Singh](https://www.linkedin.com/in/rishu-singh-51512b3b3)

---

⭐ If you find this project useful or interesting, consider giving the repository a star.


