#!/bin/bash

set -e

echo "? Installing Google Chrome..."

# Download and install Google Chrome
wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm
sudo dnf install -y ./google-chrome-stable_current_x86_64.rpm
rm -f google-chrome-stable_current_x86_64.rpm

echo "? Google Chrome installed."
google-chrome --version

echo "? Detecting Chrome version..."
CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+\.\d+')
echo "? Detected Chrome version: $CHROME_VERSION"

echo "?? Downloading matching ChromeDriver..."
wget -q https://storage.googleapis.com/chrome-for-testing-public/$CHROME_VERSION/linux64/chromedriver-linux64.zip
unzip -q chromedriver-linux64.zip
chmod +x chromedriver-linux64/chromedriver
sudo mv chromedriver-linux64/chromedriver /usr/local/bin/chromedriver
rm -rf chromedriver-linux64 chromedriver-linux64.zip

echo "? ChromeDriver installed at /usr/local/bin/chromedriver"
chromedriver --version

echo "? Creating Selenium test script..."

cat <<EOF > selenium_test.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

options = Options()
options.binary_location = "/usr/bin/google-chrome"
options.add_argument('--headless')
options.add_argument('--disable-gpu')

service = Service("/usr/local/bin/chromedriver")
driver = webdriver.Chrome(service=service, options=options)

driver.get("https://www.google.com")
print("Page title:", driver.title)
driver.quit()
EOF

echo "? Running Selenium test..."
python3 selenium_test.py

echo "? Test complete!"
