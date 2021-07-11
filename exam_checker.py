from selenium import webdriver
from selenium.webdriver.support.ui import Select
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import os
import time
from email.message import EmailMessage
import smtplib
from apscheduler.schedulers.blocking import BlockingScheduler


class DateChecker:
    def __init__(self):
        # self.browser = webdriver.Chrome()
        self.url = "http://securereg3.prometric.com/landing.aspx?prg=STEP2"
        self.location_book = {}
        self.list_of_locations = ["6002: Toronto - Cestar College",
                                  "5113: Toronto - Bloor Street East",
                                  "6015: Toronto - ON (Mississauga)",
                                  "5374: Hamilton, Ontario",
                                  "5361: London - First Street", ]
        self.list_of_locations_east = ["6019: Ottawa ON",
                                       "5259: Montreal - Pointe-Claire"]
        self.final = {}
        self.date_threshold = '2021-05-20'
        self.date_threshold_datetime = datetime.strptime(
            self.date_threshold, '%Y-%m-%d')

    def find_click(self, element_id):
        variable = browser.find_element_by_id(element_id)
        variable.click()

    def fill_out(self, element_id, data):
        variable = browser.find_element_by_id(element_id)
        variable.send_keys(data)

    def drop_down_selection(self, element_id, selection):
        variable = browser.find_element_by_id(element_id)
        var = Select(variable)
        var.select_by_visible_text(selection)

    def open_browser(self):
        global browser
        chrome_options = webdriver.ChromeOptions()
        chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        browser = webdriver.Chrome(executable_path=os.environ.get(
            "CHROMEDRIVER_PATH"), chrome_options=chrome_options)
        browser = webdriver.Chrome()
        browser.get(self.url)
        # browser.minimize_window()
        browser.implicitly_wait(20)

    def first_selections(self):
        # FIRST SELECTIONS
        print("Trying to log in...")
        self.drop_down_selection("masterPage_cphPageBody_ddlCountry", "CANADA")
        self.drop_down_selection(
            "masterPage_cphPageBody_ddlStateProvince", "Ontario")
        self.find_click("masterPage_cphPageBody_btnNext")
        # SECOND PAGE - SCHEDULE AN APPOINTMENT
        self.find_click("masterPage_cphPageBody_lnkSchedule2")

        # NEXT
        for _ in range(3):
            try:
                self.find_click("masterPage_cphPageBody_btnNext")
                time.sleep(1.5)
            except:
                pass

        # CONFIRM AGE
        self.find_click("masterPage_cphPageBody_chkParentalConsent")
        self.find_click("masterPage_cphPageBody_optConsent")
        # NEXT
        self.find_click("masterPage_cphPageBody_btnNext")
        # NEXT
        self.find_click("masterPage_cphPageBody_btnNext")
        # LOGIN
        self.fill_out("txtElig_ELIGIBILITY_NUMBER", "042205640")
        self.fill_out("txtElig_ISVALIDLASTNAME", "gok")

        # NEXT
        for _ in range(3):
            try:
                self.find_click("masterPage_cphPageBody_btnNext")
                time.sleep(1.5)
            except:
                pass

    def location_finder(self, location, zip_code):
        # ZIPCODE
        self.fill_out("txtSearch", zip_code)
        # SEARCH BUTTON
        self.find_click("btnSearch")
        # Location
        test_center = browser.find_element_by_partial_link_text(location)
        test_center.click()
        schedule = browser.find_element_by_partial_link_text(
            "Schedule an Appointment")
        schedule.click()
        # CONSENT
        self.find_click("masterPage_cphPageBody_optAgree")
        # NEXT
        self.find_click("masterPage_cphPageBody_btnNext")
        # DROP DOWN MONTH/YEAR
        self.drop_down_selection(
            "masterPage_cphPageBody_ddlMonthYear", "May 2021")
        # GO
        self.find_click("masterPage_cphPageBody_btnGo")
        parsed_page = BeautifulSoup(browser.page_source, "html.parser")
        return parsed_page

    def go_back(self):
        # GO BACK BUTTON
        for _ in range(2):
            self.find_click("masterPage_cphPageBody_btnBack")
            time.sleep(1)

    def close_locations(self):
        for item in self.list_of_locations:
            print(f"Looking at {item} calendar...")
            self.location_book[item.split(":")[1].strip(
            )] = self.location_finder(item, "M2R3S5")
            self.go_back()

    def far_locations(self):
        for item in self.list_of_locations_east:
            print(f"Looking at {item} calendar...")
            self.location_book[item.split(":")[1].strip(
            )] = self.location_finder(item, "ottowa")
            self.go_back()

    def check_available_dates(self):
        for key, value in self.location_book.items():
            print(f"Checking for {key}...")
            table_container = value.find_all("td", {"class": "calContainer"})
            table_container_length = len(table_container)
            cal_container = []
            for i in range(table_container_length):
                cal_item = table_container[i].find_all(
                    "td", {"class": "calActive"})
                if cal_item:
                    cal_container.append(cal_item)

            if cal_container:
                print(f"{key} has some available dates!")
                self.final[key] = []
                for x in range(len(cal_container)):
                    for y in cal_container[x]:
                        base4 = y
                    decoded = base4.decode()
                    # PARSE THE DATE
                    prev = decoded.split("id=")[1]
                    date = prev.split(" ")[0]
                    date = date[1:-1]
                    print(date)
                    # CONVERT IT TO DATE OBJECT
                    date_obj = datetime.strptime(date, '%Y-%m-%d')
                    print(date_obj)
                    # IF IT'S FARTHER THAN MAY 20TH, KEEP IT.
                    if date_obj >= self.date_threshold_datetime:
                        self.final[key].append(date_obj)

        print(self.final)
        browser.quit()

    def send_email(self, url, availability_info):
        msg = EmailMessage()
        recipients = ["tugrul.pinar@hotmail.com", "senagokk@gmail.com"]
        msg["Subject"] = "Test Centre is available!"
        msg["From"] = "tugrulpinar96@gmail.com"
        msg["Bcc"] = ",".join(recipients)
        msg.set_content(
            f"Hi,\n\nThere may be some seats available in {availability_info} ! Check out the link:\n{url}")

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:

                smtp.login("tugrulpinar96@gmail.com", "ynqajlbxnhawuvyl")
                smtp.send_message(msg)
                print("Email sent!")
        except Exception as e:
            print(str(e))
            print("Failed to send email")

    def decision_maker(self):

        to_be_emailed = []

        for key, val in self.final.items():
            if len(val) > 0:
                to_be_emailed.append(str(key) + " " + str(val))

        if to_be_emailed:
            print("Sending email...")
            self.send_email(self.url, to_be_emailed)

    def run(self):
        self.open_browser()
        self.first_selections()
        self.close_locations()
        self.far_locations()
        self.check_available_dates()
        self.decision_maker()

    def scheduler(self):
        sched = BlockingScheduler()
        sched.add_job(self.run, 'interval', hours=4)
        sched.start()


dc = DateChecker()
dc.scheduler()
