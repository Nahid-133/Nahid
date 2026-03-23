
<div align="center">
.
# 🤖 Telegram Submission Bot

**An advanced, automated account management and submission bot built with Python & Aiogram.**

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Aiogram](https://img.shields.io/badge/Aiogram-3.x-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://aiogram.dev/)
[![License](https://img.shields.io/badge/License-MIT-success?style=for-the-badge)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)](https://github.com)

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=20&pause=1000&color=2CA5E0&center=true&vCenter=true&width=500&lines=Automated+JSON+Parsing;Secure+Data+Handling;Excel+Report+Generation;Admin+Dashboard" alt="Typing SVG" />

</div>

---
---
## 📖 Table of Contents
- [🚀 Features](#-features)
- [📖 Submission Manual](#-submission-manual)
- [💳 Payment Configuration](#-payment-configuration)
- [📊 Reporting & Analytics](#-reporting--analytics)
- [🛠 Tech Stack](#-tech-stack)
- [⚙️ Installation](#️-installation)

---

## 🚀 Features
- **⏰ Time-Gated Submission:** Strict adherence to submission windows (16:00 - 10:00).
- **📂 JSON Parsing:** Automatic validation and processing of bulk account files.
- **📊 Excel Export:** beautifully formatted `.xlsx` reports with custom styling (Openpyxl).
- **💰 Payment Integration:** Easy setup for local payment gateways (Bkash, Rocket).
- **🔐 Admin Panel:** Secure administrative controls and data export functionality.

---

## 📖 Submission Manual

### ⏰ Submission Window
The system is configured to accept files strictly within the following timeframe:

> **Start:** 16:00 (4:00 PM)  
> **End:** 10:00 (10:00 AM)  
> *Submissions outside this window will be automatically rejected.*

### 📁 How to Submit Files
Follow these steps to successfully submit your account data:

1.  **Navigate** to the bot menu and click the **`📁 Submit Files`** button.
2.  **Attach** your JSON file(s) during the active submission window.
3.  **Wait** for the confirmation message. The bot will parse the data and save the accounts automatically.

### 📝 File Format
Ensure your JSON file follows the schema below to avoid parsing errors.

```json
[
  {
    "username": "user1",
    "password": "pass1"
  },
  {
    "username": "user2",
    "password": "pass2"
  }
]
```
> ⚠️ **Note:** The file must be a valid JSON array containing objects with `username` and `password` keys.

---

## 💳 Payment Configuration

### Supported Methods
We currently support the following payment gateways:
- 📱 **Bkash**
- 🚀 **Rocket**

### Update Payment Info
To update your payment number, use the following command syntax:

`/pay [method] : [number]`

**Example Usage:**
```text
/pay bkash : 01712345678
/pay rocket : 01987654321
```

---

## 📊 Reporting & Analytics

Stay updated with your submission performance.
- Click the **`📊 My Reports`** button in the menu.
- The bot will display a detailed breakdown of your last **5 days** of activity.

---

## 🛠 Tech Stack

This project leverages modern Python technologies for high performance and reliability:

| Component | Technology |
| :--- | :--- |
| **Core Framework** | [Aiogram 3.x](https://aiogram.dev/) (Async Telegram Bot Framework) |
| **Database** | [SQLAlchemy](https://www.sqlalchemy.org/) (ORM) |
| **Data Processing** | [Pandas](https://pandas.pydata.org/) |
| **Excel Engine** | [Openpyxl](https://openpyxl.readthedocs.io/en/stable/) |
| **Language** | [Python 3.9+](https://www.python.org/) |

---

## ⚙️ Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/sinescode/instarcv.git
    cd instarcv
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    Create a `.env` file and add your bot token and database URL.
    ```env
    BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
    DATABASE_URL=sqlite:///db.sqlite3
    ```

5.  **Run the bot:**
    ```bash
    python main.py
    ```

---

<div align="center">

### ❓ Need Help?

If you encounter any issues or have questions, please contact the **Admin**.

Made with ❤️ and Python

</div>
