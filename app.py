import json
import time
import random
import gzip
import csv
import os
from flask import Flask, request, jsonify, render_template
from seleniumwire import webdriver  # Import from seleniumwire
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service  # Import Service for Selenium 4
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)

def init_driver():
    """Initialize a headless Chrome browser with Selenium Wire."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    # Set a common user-agent to mimic real browsers
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    )
    
    # Use webdriver_manager to automatically manage ChromeDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def fetch_profile_metrics(driver, screen_name):
    """
    Navigate to the Twitter profile page, wait for network requests,
    and then intercept the GraphQL request by its unique endpoint identifier.
    """
    url = f"https://x.com/{screen_name}"
    print(f"\nNavigating to {url}")
    driver.get(url)
    
    # Wait for the page and XHR requests to load (random delay between 3 and 6 seconds)
    time.sleep(random.uniform(3, 6))
    
    target_request = None
    # Loop over network requests captured by Selenium Wire
    for request in driver.requests:
        # Ensure that the request URL corresponds to the current screen_name
        if request.response and "UserByScreenName" in request.url and screen_name.lower() in request.url.lower():
            target_request = request
            break

    if target_request:
        try:
            # Get the raw response body
            raw_body = target_request.response.body
            try:
                # First try decoding as utf-8 directly
                body = raw_body.decode('utf-8')
            except UnicodeDecodeError:
                # If that fails, decompress using gzip then decode
                body = gzip.decompress(raw_body).decode('utf-8')
                
            data = json.loads(body)
            # Depending on the structure, the metrics might be nested under:
            # data -> user -> result -> legacy   OR   data -> user -> legacy
            legacy = data.get("data", {}).get("user", {}).get("result", {}).get("legacy", {})
            if not legacy:
                legacy = data.get("data", {}).get("user", {}).get("legacy", {})
            
            metrics = {
                "username": screen_name,
                "followers_count": legacy.get("followers_count"),
                "friends_count": legacy.get("friends_count"),
                "listed_count": legacy.get("listed_count"),
                "location": legacy.get("location")
            }
            print(f"Metrics for {screen_name}: {metrics}")
            return metrics
        except Exception as e:
            print(f"Error parsing response for {screen_name}: {e}")
            return {"username": screen_name, "error": str(e)}
    else:
        print(f"No matching network request found for {screen_name}")
        return {"username": screen_name, "error": "No matching network request found"}

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Retrieve input from the form
        auth_token = request.form.get("auth_token").strip()
        ct0 = request.form.get("ct0").strip()
        profiles_input = request.form.get("profiles").strip()
        screen_names = [name.strip() for name in profiles_input.split(",") if name.strip()]
        
        # Provide a notice if too many profiles are given (you can adjust the limit here)
        if len(screen_names) > 500:
            return jsonify({"error": "Please do not enter more than 500 profiles at once."})
        
        driver = init_driver()
        # Visit base URL to allow cookie injection. Selenium only allows adding cookies on a loaded domain.
        driver.get("https://x.com")
        time.sleep(3)
        # Inject the session cookies into the browser. Domain must match.
        driver.add_cookie({"name": "auth_token", "value": auth_token, "domain": ".x.com"})
        driver.add_cookie({"name": "ct0", "value": ct0, "domain": ".x.com"})
        
        results = []
        total = len(screen_names)
        progress = 0
        
        # Scrape each profile
        for screen_name in screen_names:
            driver.requests.clear()
            metrics = fetch_profile_metrics(driver, screen_name)
            results.append(metrics)
            progress += 1
            print(f"Processed {progress}/{total} profiles")
            time.sleep(random.uniform(5, 10))  # Random delay between requests
        
        driver.quit()
        
        # Save results as CSV in the current folder
        csv_filename = "results.csv"
        with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["username", "followers_count", "friends_count", "listed_count", "location"])
            for result in results:
                writer.writerow([
                    result.get("username", ""),
                    result.get("followers_count", ""),
                    result.get("friends_count", ""),
                    result.get("listed_count", ""),
                    result.get("location", "")
                ])
        print(f"\nCSV file saved as {csv_filename}")
        
        # Include progress info in the response
        return jsonify({
            "progress": f"Processed {total}/{total} profiles.",
            "results": results
        })
    
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
