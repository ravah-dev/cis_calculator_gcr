# logging_info.md

---

## **Default Behavior**

By default, Python's `logging` library sends log messages to the standard output (`stdout`), which means:

1. **When Running Locally**:
   - Logs will appear in your terminal or command-line interface (where you run the application).

2. **When Running in a Docker Container**:
   - Logs are written to the container's `stdout`, which can be viewed using Docker commands like:

     ```bash
     docker logs <container_id>
     ```

   - Replace `<container_id>` with your container's ID or name.

---

### **Customizing the Logger Output**

If you want to redirect log messages to a file or another destination, you can configure a file handler in your logger setup. Here’s how:

#### Example: Add a File Handler

```python
import logging

# Logger setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),  # Sends logs to stdout (default)
        logging.FileHandler("app.log")  # Sends logs to a file named 'app.log'
    ]
)
logger = logging.getLogger(__name__)
```

---

### **Accessing Logs in Google Cloud Run**

When your container runs in **Google Cloud Run**, the logs are sent to **Cloud Logging** (formerly Stackdriver) by default. You can access them via the GCP Console:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Navigate to **Logging** → **Logs Explorer**.
3. Filter logs by your service name or specific log messages.

---

### **Key Notes**

- **Log Levels**:
  - Use levels like `INFO`, `WARNING`, `ERROR`, etc., to categorize logs.
  - These levels can help you filter logs in Cloud Logging or other monitoring tools.

- **Log Rotation**:
  - If writing to a file, consider setting up log rotation to avoid large log files. Use Python's `logging.handlers.RotatingFileHandler` for this purpose.

---

### Testing Logger Output

1. Run the application locally and verify that logs appear in the terminal.
2. If using a file handler, check the `app.log` file for log entries.
3. Deploy to your Docker container and use `docker logs` to inspect the logs.
4. In Cloud Run, validate that logs are reaching Cloud Logging.

Let me know if you’d like to customize your logger further or need help accessing the logs in your environment! 😊
