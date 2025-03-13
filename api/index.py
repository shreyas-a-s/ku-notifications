import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template

app = Flask(__name__)

url = "https://exams.keralauniversity.ac.in/Login/check1"
tables_data = extract_tables(url)
final_variable = process_data(tables_data)
course_map = {
    "btech": "B.Tech",
    "mtech": "M.Tech",
    "ba": "B.A.",
    "bcom": "B.Com.",
}


def convert_course_string(course):
    if course.lower() in course_map:
        return course_map[course.lower()]

    return ""


def extract_tables(url, course=""):
    # Fetch webpage content
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve the page. Status code: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    # Find all <tr> elements that either contain the substring "course" or have a class of "tableHeading"
    matching_rows = [
        tr
        for tr in soup.find_all("tr")
        if any(course in td.text for td in tr.find_all("td"))
        or "tableHeading" in tr.get("class", [])
    ]

    return matching_rows


def extract_semester_num(description):
    number_map = {
        "first": 1,
        "second": 2,
        "third": 3,
        "fourth": 4,
        "fifth": 5,
        "sixth": 6,
        "seventh": 7,
        "eighth": 8,
        "ninth": 9,
    }

    words = description.lower().split()
    for word in words:
        if word in number_map:
            return number_map[word]  # Return first detected number

    return None  # No number found


def process_data(tables_data):
    final_variable = []
    current_published_date = None
    notifications = []

    for tr in tables_data:
        # Check if the row is a table heading (contains the published date)
        if "tableHeading" in tr.get("class", []):
            # If there is an existing group of notifications, save them
            if current_published_date:
                final_variable.append(
                    {
                        "published_date": current_published_date,
                        "published_year": current_published_year,
                        "notifications": notifications,
                    }
                )

            # Extract the published date from the first <td>
            published_date = tr.find("td").get_text(strip=True).split()[2]
            published_date = published_date[:-5]
            published_year = f"/{published_date[-2:]}"
            current_published_date = published_date
            current_published_year = published_year
            notifications = []  # Reset the notifications for the new published date
        else:
            # Process rows with notification data
            tds = tr.find_all("td")

            # For rows with just one <td> (description only)
            if len(tds) == 1:
                description = tds[0].get_text(strip=True)
                semester_num = extract_semester_num(description)
                notifications.append(
                    {
                        "description": description,
                        "semester_num": semester_num,
                        "pdf_link": None,
                    }
                )
            elif (
                len(tds) >= 2
            ):  # For rows with at least two <td> elements (description and pdf link)
                description = tds[1].get_text(strip=True)
                semester_num = extract_semester_num(description)
                link_tag = tds[2].find("a")  # Find <a> inside the last <td>
                pdf_link = link_tag["href"] if link_tag else None
                notifications.append(
                    {
                        "description": description,
                        "semester_num": semester_num,
                        "pdf_link": pdf_link,
                    }
                )

    # Don't forget to append the last set of notifications after the loop
    if current_published_date:
        final_variable.append(
            {"published_date": current_published_date, "notifications": notifications}
        )

    return final_variable


@app.route("/")
def index():
    return render_template(
        "table.html", data=final_variable, course=None, course_map=course_map
    )


@app.route("/course/<course>")
def show_course_notifications(course):
    course_string = convert_course_string(course)
    tables_data = extract_tables(url, course_string)
    final_variable = process_data(tables_data)
    return render_template(
        "table.html", data=final_variable, course=course, course_map=course_map
    )


if __name__ == "__main__":
    app.run()
