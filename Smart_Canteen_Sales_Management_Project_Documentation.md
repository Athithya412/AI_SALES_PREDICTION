# SMART CANTEEN SALES MANAGEMENT AND FORECASTING SYSTEM

## CRUD-Based Web Application Development – Project Documentation

**Technology:** Python, Streamlit, SQLite, Pandas, NumPy, Scikit-learn

---

## 1. Project Overview

The **Smart Canteen Sales Management and Forecasting System** is a web-based application designed to help canteen staff or shop owners maintain daily item-wise sales records and analyze historical sales data.

The system provides:
- User authentication
- Shop selection
- Menu-item management
- Daily sales logging
- Sales history
- AI-based next-day sales forecasting

The application is implemented using **Streamlit** with **SQLite** as the database. The forecasting module uses **RandomForestRegressor** when sufficient historical data is available and uses an average-based prediction for smaller datasets.

## 2. Problem Statement

Canteens need to maintain daily sales records and understand sales patterns for better planning. Manual tracking of daily sales can make it difficult to manage historical records and estimate future sales.

This project provides a digital system for recording sales, viewing historical information, and predicting expected sales for a selected future date using previous sales data and contextual conditions.

## 3. Objectives

1. Provide a simple web interface for managing canteen shops and menu items.
2. Store daily item-wise sales records in a structured SQLite database.
3. Provide Create and Read operations for sales and menu records.
4. Support sales-history viewing for the selected shop.
5. Use date, day of week, month, exam/special-event status, weather, and review score as forecasting features.
6. Generate an estimated next-day or selected-date sales quantity.
7. Provide user login and registration with hashed passwords.
8. Extend the application to full CRUD compliance by adding Update and Delete operations.

## 4. Target Users

- Canteen Manager / Shop Owner
- Canteen Staff
- Administrator

## 5. Functional Requirements

### 5.1 User Authentication

- User registration with username, password, and role.
- User login using stored password hashes.
- Logout through the sidebar.
- Available roles: Shop Owner and Admin.

### 5.2 Shop Management

- A logged-in user can register a shop when no shop is associated with the account.
- The user can select one of their registered shops from the sidebar.

### 5.3 Menu Management

- Add a new menu item to the selected shop.
- Display menu items belonging to the selected shop.

### 5.4 Daily Sales Logging

The user can:
- Select a sales date.
- Mark whether the date is an exam day or special event.
- Select weather: Sunny, Rainy, or Cloudy.
- Enter customer review score from 1 to 5.
- Enter quantity sold for each available item.
- Save sales records to SQLite.

### 5.5 Sales History

The system retrieves historical sales records for the selected shop and displays:
- Date
- Item
- Quantity Sold
- Review Score

### 5.6 AI Forecasting

The user can:
- Select the forecast date.
- Specify whether the forecast date is an exam day.
- Select expected weather.
- Run the AI forecast.
- View predicted sales quantity for each menu item.

## 6. Technology Stack

| Layer / Purpose | Technology |
|---|---|
| Programming Language | Python |
| Web Application Framework | Streamlit |
| Database | SQLite |
| Data Processing | Pandas, NumPy |
| Machine Learning | Scikit-learn – RandomForestRegressor |
| Authentication | Python hashlib |
| Date Handling | Python datetime |

## 7. System Architecture

The current implementation uses a **Streamlit-based architecture**.

```text
                    USER
                      |
                      v
             STREAMLIT INTERFACE
                      |
                      v
             PYTHON APPLICATION
                 LOGIC
                      |
              +-------+-------+
              |               |
              v               v
        SQLITE DATABASE   AI FORECAST
                              |
                    +---------+---------+
                    |                   |
                  Pandas        Scikit-learn
                                      |
                                      v
                              SALES PREDICTION
```

## 8. Database Design

| Table | Important Fields | Purpose |
|---|---|---|
| users | id, username, password, role | Stores registered users and roles |
| shops | id, user_id, shop_name | Stores shops associated with users |
| items | id, shop_id, item_name | Stores menu items for each shop |
| sales_data | id, item_id, date, day_of_week, month, is_exam_day, weather, review_score, quantity_sold | Stores item-wise daily sales and forecasting features |

## 9. Sales Data Fields

| Field | Type / Example | Description |
|---|---|---|
| id | INTEGER | Auto-increment primary key |
| item_id | INTEGER | Identifies the menu item |
| date | TEXT / YYYY-MM-DD | Date of the sales record |
| day_of_week | TEXT | Monday to Sunday |
| month | INTEGER | Month number extracted from date |
| is_exam_day | INTEGER (0/1) | Indicates exam/special-event status |
| weather | TEXT | Sunny, Rainy, or Cloudy |
| review_score | INTEGER (1–5) | Customer review score |
| quantity_sold | INTEGER | Number of units sold |

## 10. CRUD Requirements

### Create
The user can add a new menu item and a new daily sales record.

### Read
The user can view menu items, historical sales records, and AI forecast results.

### Update
An existing sales record should be editable when incorrect information has been entered.

### Delete
An unwanted or incorrect sales record should be removable with a confirmation step.

### Current Implementation Status

| CRUD Operation | Status |
|---|---|
| Create | Implemented |
| Read | Implemented |
| Update | To be added |
| Delete | To be added |

**Important:** The supplied code currently contains Create and Read functionality. Update and Delete controls for sales history are not yet present and should be added for complete CRUD compliance.

## 11. AI Forecasting Method

The forecasting module uses historical sales data.

When at least **7 historical records** are available for an item and Scikit-learn is installed, the system trains a **RandomForestRegressor**.

The model uses:

| Feature | Representation |
|---|---|
| Day of week | Monday = 0 to Sunday = 6 |
| Month | 1–12 |
| Exam day | 0 or 1 |
| Weather | Sunny = 0, Rainy = 1, Cloudy = 2 |
| Review score | 1–5 |
| Target | Quantity sold |

The model uses `day_n`, `month`, `exam`, `weather_n`, and `review` to predict `quantity_sold`.

The model is created with 100 estimators and `random_state=42`.

## 12. Forecasting Fallback Method

When an item has fewer than 7 historical records, the system uses a simple average-based prediction.

```text
Average Sales = Total Historical Sales / Number of Records
```

If the forecast is marked as an exam day, the current implementation applies:

```text
Prediction = Average Sales × 1.3
```

This provides a fallback prediction for shops with limited historical data.

## 13. Application Workflow

```text
1. Open the Streamlit application
        ↓
2. Register or Login
        ↓
3. Register / Select Canteen Shop
        ↓
4. Add Menu Items
        ↓
5. Enter Daily Sales
        ↓
6. Store Records in SQLite
        ↓
7. View Sales History
        ↓
8. Select Forecast Date and Conditions
        ↓
9. Run AI Forecast
        ↓
10. View Predicted Sales
```

## 14. Validation and Error Handling

The current application contains:
- Username uniqueness using a UNIQUE database constraint.
- Password hashing before storage.
- Quantity input with a minimum value of 0.
- Review score restricted from 1 to 5.
- Invalid login credentials display an error message.
- Insufficient historical data handled using the fallback average method.

Additional validation can be added for:
- Empty item names
- Empty shop names
- Duplicate menu items
- Invalid dates
- Missing required fields

## 15. Testing Plan

| Test Case | Input / Action | Expected Result |
|---|---|---|
| Valid Login | Correct username and password | User enters application |
| Invalid Login | Incorrect credentials | Error message displayed |
| Register User | New username/password/role | Account created |
| Duplicate User | Existing username | Registration rejected |
| Register Shop | Valid shop name | Shop is saved |
| Add Item | Valid item name | Item is stored and displayed |
| Daily Log | Date, conditions and quantities | Sales records stored |
| History | Open History tab | Saved records displayed |
| AI Forecast | 7 or more records | Random Forest prediction generated |
| AI Forecast | Fewer than 7 records | Average-based prediction generated |
| Validation | Invalid numeric values | Input controls prevent invalid ranges |
| Update | Edit existing record | Updated value displayed |
| Delete | Delete existing record | Record removed after confirmation |

## 16. Current Implementation Gap

The supplied application is functional, but the following features need to be added for complete CRUD compliance:

### Update

```text
History
   ↓
Select Record
   ↓
Edit
   ↓
Change Quantity / Details
   ↓
Save
   ↓
Database Updated
```

### Delete

```text
History
   ↓
Select Record
   ↓
Delete
   ↓
Confirmation
   ↓
Database Record Removed
```

### Search and Filter

Add:
- Search by item name
- Filter by date
- Filter by item
- Filter by weather or event condition

### API Requirement

If the activity evaluation strictly requires REST APIs and Postman testing, an API layer should be added and tested separately.

## 17. Security and Quality Considerations

- Parameterized SQLite queries are used for user-provided values.
- Passwords are hashed before storage.
- Database files and sensitive information should not be committed to a public repository.
- Meaningful variable, function, table, and field names should be used.
- For production use, a password-hashing method designed specifically for password storage should be preferred over a simple SHA-256 digest.

## 18. Project Demonstration Sequence

1. Start the Streamlit application.
2. Register a user.
3. Login.
4. Register/select a canteen shop.
5. Add menu items.
6. Enter daily sales records.
7. Open History and show saved records.
8. Run AI Forecast.
9. Show predicted sales.
10. Explain the Random Forest and fallback prediction.
11. Demonstrate validation.
12. Demonstrate Update and Delete after those features are implemented.

## 19. Future Enhancements

- Complete Update and Delete functionality.
- Add sales charts and graphs.
- Improve forecasting evaluation using training and validation datasets.
- Add holidays and other relevant events as forecasting features.
- Export sales history to CSV or Excel.
- Add role-based permissions.
- Add a dedicated REST API if required.
- Improve forecasting with more historical data.

## 20. Conclusion

The **Smart Canteen Sales Management and Forecasting System** provides a practical digital solution for recording canteen sales and generating sales forecasts.

The current implementation uses **Streamlit, Python, SQLite, Pandas, NumPy, and Scikit-learn** to provide authentication, shop management, menu management, daily sales logging, sales history, and AI-based forecasting.

The main remaining requirement for complete CRUD compliance is the implementation and demonstration of **Update and Delete** operations. Search/filter and REST API functionality should also be added if they are required by the activity evaluation.

## 21. SOP Compliance Checklist

| Requirement | Current Status |
|---|---|
| Practical management application | Yes |
| User Interface | Yes – Streamlit |
| Application Logic | Yes – Python |
| Database | Yes – SQLite |
| Create | Yes |
| Read | Yes |
| Update | To be added |
| Delete | To be added |
| Validation | Partially implemented |
| Search / Filter | To be added |
| REST API | Not implemented |
| Postman Testing | Not implemented |
| Version Control | To be documented |
| Documentation | Completed |
| Working Demonstration | Major modules implemented |

---

**Project Name:** Smart Canteen Sales Management and Forecasting System

**Main Entity:** Daily Sales Record

**Core Features:** Authentication → Shop Management → Menu Management → Daily Sales → History → AI Forecast → CRUD
