from playwright.sync_api import sync_playwright
import os
from pathlib import Path

# Create screenshots directory if it doesn't exist
screenshots_dir = Path("docs/screenshots")
screenshots_dir.mkdir(parents=True, exist_ok=True)

def capture_screenshots():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch()
        page = browser.new_page()
        
        # Set viewport size
        page.set_viewport_size({"width": 1280, "height": 800})
        
        # Navigate to admin login
        page.goto("http://localhost:8000/admin/")
        page.screenshot(path=str(screenshots_dir / "01_admin_login.png"))
        
        # Login
        page.fill("#id_username", "josh")
        page.fill("#id_password", "joshjosh")
        page.click("input[type=submit]")
        
        # Wait for login to complete
        page.wait_for_selector("#user-tools")
        
        # Capture Option Groups list
        page.goto("http://localhost:8000/admin/sync_option/optiongroup/")
        page.screenshot(path=str(screenshots_dir / "02_option_groups.png"))
        
        # Capture Options list with filters
        page.goto("http://localhost:8000/admin/sync_option/option/")
        page.screenshot(path=str(screenshots_dir / "03_options_list.png"))
        
        # Capture Option Relations list
        page.goto("http://localhost:8000/admin/sync_option/optionrelation/")
        page.screenshot(path=str(screenshots_dir / "04_option_relations.png"))
        
        # Capture detailed views
        # Option Group detail
        page.goto("http://localhost:8000/admin/sync_option/optiongroup/1/change/")
        page.screenshot(path=str(screenshots_dir / "05_option_group_detail.png"))
        
        # Option detail
        page.goto("http://localhost:8000/admin/sync_option/option/1/change/")
        page.screenshot(path=str(screenshots_dir / "06_option_detail.png"))
        
        # Option Relation detail
        page.goto("http://localhost:8000/admin/sync_option/optionrelation/1/change/")
        page.screenshot(path=str(screenshots_dir / "07_option_relation_detail.png"))
        
        browser.close()

if __name__ == "__main__":
    capture_screenshots() 