# CODEPIT_TECH-A-THON_2024

# Stock Market API

## Overview
A comprehensive API for real-time stock market data with predictive analytics. 

## Features
- Real-time stock data
- Historical stock data (daily, weekly, monthly, yearly)
- Stock price prediction
- User authentication and rate limiting

## Installation

1. **Clone the Repository:**

    ```sh
    git clone https://github.com/VijayarajParamasivam/CODEPIT_TECH-A-THON_2024.git
    cd <repository-directory>
    ```

2. **Create and Activate Virtual Environment:**

    ```sh
    python -m venv venv
    source venv/bin/activate  # For Windows: venv\Scripts\activate
    ```

3. **Install Dependencies:**

    ```sh
    pip install -r requirements.txt
    ```

## Running the API

1. **Start the API Server:**

    ```sh
    uvicorn app.main:app --reload --port 8001
    ```

2. **Access Documentation:**
   - Swagger UI: `http://127.0.0.1:8001/docs`

## Authentication

- **Register:** `POST /user/register`
- **Login + API key:** `POST /user/login`
- **Delete:** `DELETE /user/delete`

## Endpoints

### `GET /stocks/{symbol}/historical`
- **Description:** Retrieve historical stock data.(Needs API key)
- **Parameters:**
  - `symbol`: Stock ticker symbol (e.g., AAPL)
  - `start_date`: Optional start date (YYYY-MM-DD)
  - `end_date`: Optional end date (YYYY-MM-DD)
  - `frequency`: Data frequency (daily, weekly, monthly, yearly)
  - `format`: Response format (json, csv, xml)

### `GET /predict/{symbol}`
- **Description:** Predict future stock prices.(Needs API key)
- **Parameters:**
  - `symbol`: Stock ticker symbol
  - `periods`: Number of days to predict

## Rate Limiting

- Rate limit is set to 10 requests per day per user for predictions.
- Rate limit is set to 50 requests per day per user for current price and history data.

## Error Handling

- **401 Unauthorized:** Invalid or missing API key.
- **400 Bad Request:** Invalid input parameters.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

For any questions, please contact [vijayarj.p@gmail.com](mailto:vijayarj.p@gmail.com).
