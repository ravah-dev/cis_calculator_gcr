# Testing The API
Testing your API is essential to ensure it behaves as expected. Here's how you can test your `POST /calculate` endpoint with a JSON payload.

---

## **Option 1: Using `curl` (Command Line)**

`curl` is a powerful command-line tool for making HTTP requests.

### Simple Example Test Command  
Assumes the API is performing some calculation on value1 and value 2 and returning a result.

```bash
curl -X POST http://127.0.0.1:8080/calculate \
-H "Content-Type: application/json" \
-d '{"value1": 42, "value2": 7}'
```

#### Explanation

- `-X POST`: Specifies a `POST` request.
- `http://127.0.0.1:8080/calculate`: The URL where your API is running locally.
- `-H "Content-Type: application/json"`: Sets the request header to indicate you're sending JSON.
- `-d '{"value1": 42, "value2": 7}'`: Sends the JSON payload as data.

#### Expected Response

```json
{
  "input": {
    "value1": 42,
    "value2": 7
  },
  "output": "calculated metrics"
}
```
  
### Example CURL to Test the CIS-Calculator  
This sends the content of a file to be processed, expects output to be a json formatted 'Results Collection'  

```bash
curl                                    # The base command to make HTTP requests
-X POST                                # Specifies that this is a POST request
-H "Content-Type: application/json"     # Sets the header to indicate JSON content
-d @test_farm_input.json               # Sends the contents of test_farm_input.json as the request body
http://localhost:8080/calculate        # The endpoint URL
```

This command is making a POST request to a local server running on port 8080, specifically to the `/calculate` endpoint. It's sending JSON data from a file named `test_farm_input.json` as the request body.  
  
Expected response is a JSON formatted "Results Collection"
  
---

### **Option 2: Using `httpie` (Command Line)**

`httpie` is a user-friendly alternative to `curl`.

#### Command

```bash
http POST http://127.0.0.1:8080/calculate value1=42 value2=7
```

#### Explanation

- `http POST`: Specifies a `POST` request.
- `value1=42 value2=7`: Automatically converted to JSON payload.

#### Install `httpie`

```bash
pip install httpie
```

---

### **Option 3: Using Postman (GUI)**

Postman is a popular GUI-based tool for API testing.

#### Steps

1. **Download and Install Postman**: [Get Postman](https://www.postman.com/downloads/).
2. **Create a New Request**:
   - Method: `POST`.
   - URL: `http://127.0.0.1:8080/calculate`.
3. **Set Headers**:
   - Key: `Content-Type`.
   - Value: `application/json`.
4. **Set Body**:
   - Select the `Raw` tab.
   - Choose `JSON` format.
   - Paste the payload:
     ```json
     {
       "value1": 42,
       "value2": 7
     }
     ```
5. **Send the Request**: Click "Send" and observe the response.

---

### **Option 4: Using Python Script**

If you're comfortable with Python, you can use the `requests` library.

#### Script

```python
import requests

url = "http://127.0.0.1:8080/calculate"
payload = {"value1": 42, "value2": 7}
headers = {"Content-Type": "application/json"}

response = requests.post(url, json=payload, headers=headers)

print(response.status_code)
print(response.json())
```

#### Install `requests`

```bash
pip install requests
```

#### Run the Script

```bash
python test_api.py
```

---

### **Option 5: Using a Browser Plugin**

You can use browser plugins like **Rest Client** for Chrome or Firefox.

#### Steps

1. Install a REST client plugin (e.g., [Advanced REST Client](https://install.advancedrestclient.com/)).
2. Set up the `POST` request as in Postman.
3. Send the request and observe the results.

---

### **Additional Notes**

1. Make sure your API is running locally (e.g., via `uvicorn`):
   ```bash
   uvicorn main:app --reload
   ```

2. Replace `http://127.0.0.1:8080` with your API's URL if hosted remotely.

Try any of these methods, and let me know if you need further assistance! 😊