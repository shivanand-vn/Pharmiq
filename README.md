# 💊 Pharmiq – Pharmaceutical Distribution Management System

Pharmiq is a **Python-based desktop application** designed to streamline pharmaceutical distribution operations.
Built using **CustomTkinter and MySQL**, it provides an efficient interface for managing inventory, billing, customers, payments, and reports.

---

## 🚀 Features

### 📊 Dashboard

* Real-time business insights
* Sales analytics and trends
* Low stock alerts
* Customer activity tracking

### 👥 Customer Management

* Add and manage customers
* Track purchase history

### 💊 Inventory Management

* Stock tracking
* Low stock alerts
* Category-based organization

### 🧾 Billing & Invoices

* Generate invoices
* Track paid, pending, partial payments
* Maintain invoice history

### 💳 Payments

* Record payments
* Track pending amounts

### 🔄 Returns

* Manage product returns

### 📈 Reports

* Generate and export reports

### 🔐 Authentication

* Secure login system
* Role-based access (Admin / User)

### 📧 Forgot Password (OTP via Email)

* OTP-based password reset
* Email delivery via Brevo SMTP
* Expiry and attempt limits

---

## 🛠️ Tech Stack

* **Frontend:** CustomTkinter
* **Backend:** Python
* **Database:** MySQL
* **Email:** Brevo SMTP
* **Security:** bcrypt

---

## 📁 Project Structure

```
pharmiq/
│── main.py
│── theme.py
│── ui_components.py
│── modules/
│   ├── dashboard.py
│   ├── inventory.py
│   ├── customers.py
│   ├── billing.py
│   ├── payments.py
│   └── reports.py
│── utils/
│   ├── db.py
│   ├── auth.py
│   ├── email_service.py
│── .env
│── .gitignore
│── requirements.txt
```

---

## ⚡ Performance

* Optimized UI rendering
* Efficient database queries
* Non-blocking email (threading)
* No unnecessary UI reloads

---

## 🧪 Testing Checklist

* Login works correctly
* Dashboard loads data properly
* Billing and payments function correctly
* Low stock alerts trigger
* Forgot password (OTP) works
* No UI lag

---

## 👨‍💻 Author

MCA Project – **Pharmiq**
Pharmaceutical Distribution Management System

---

## 📄 License

For educational and academic use only.
