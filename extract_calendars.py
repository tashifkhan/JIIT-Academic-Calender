import PyPDF2
import re
import json
from datetime import datetime

def extract_calendar_data(pdf_path):
    events = []
    holidays = []

    with open(pdf_path, 'rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()

    lines = text.splitlines()
    is_holiday_section = False

    for i, line in enumerate(lines):
        line = line.strip()
        if "List of Holidays" in line:
            is_holiday_section = True
            continue
        elif is_holiday_section:
            if re.match(r'^\d+\.\s+([\w\s()\*]+?)\s+(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})', line):
                match = re.match(r'^\d+\.\s+([\w\s()\*]+?)\s+(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})', line)
                if match:
                    event_name = match.group(1).strip()
                    date_str = match.group(2).strip()
                    try:
                        holiday_date = datetime.strptime(date_str, '%d %b %Y').strftime('%Y-%m-%d')
                        holidays.append({"summary": f"Holiday - {event_name}",
                                        "start": {"date": holiday_date},
                                        "end": {"date": holiday_date}})
                    except ValueError:
                        print(f"Could not parse date for holiday: {line}")
            elif re.match(r'^\d+\.\s+([\w\s()\*]+?)\s+(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})\s*\(.+\)', line):
                 match = re.match(r'^\d+\.\s+([\w\s()\*]+?)\s+(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})\s*\(.+\)', line)
                 if match:
                    event_name = match.group(1).strip()
                    date_str = match.group(2).strip()
                    try:
                        holiday_date = datetime.strptime(date_str, '%d %b %Y').strftime('%Y-%m-%d')
                        holidays.append({"summary": f"Holiday - {event_name}",
                                        "start": {"date": holiday_date},
                                        "end": {"date": holiday_date}})
                    except ValueError:
                        print(f"Could not parse date for holiday: {line}")

        elif "SER." not in line and "Event" not in line and line and not re.match(r'^==Start of OCR for page \d+==$', line) and not re.match(r'^==End of OCR for page \d+==$', line) and "JIIT NOIDA" not in line and "ACADEMIC CALENDAR" not in line and "Only for First Year" not in line and "(EVEN SEMESTER" not in line and "Sr." not in line and "Date" not in line :
            # Handling Odd Semester PDF
            date_match = re.search(r'(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})', line)
            date_range_match = re.search(r'(\d{1,2}-\d{1,2}\s+[A-Za-z]{3}\s+\d{4})', line)

            if date_match:
                event_name_parts = line.split(date_match.group(1))[0].strip()
                # Sometimes event name has leading numbers or dots, remove them
                event_name = re.sub(r'^\d+\.\s*', '', event_name_parts).strip()
                try:
                    event_date_str = date_match.group(1)
                    event_date = datetime.strptime(event_date_str, '%d %b %Y').strftime('%Y-%m-%d')
                    events.append({"summary": event_name, "start": {"date": event_date}, "end": {"date": event_date}})
                except ValueError:
                    print(f"Could not parse date for event: {line}")
            elif date_range_match:
                 event_name = line.split(date_range_match.group(1))[0].strip()
                 date_parts = date_range_match.group(1).split('-')
                 start_month_year = date_parts[1].split(' ')[1:]
                 start_date_str = f"{date_parts[0]} {' '.join(start_month_year)}"
                 end_date_str = date_range_match.group(1).split(' ')[-3:]
                 end_date_str = ' '.join(end_date_str)

                 try:
                     start_date = datetime.strptime(start_date_str, '%d %b %Y').strftime('%Y-%m-%d')
                     end_date = datetime.strptime(end_date_str, '%d %b %Y').strftime('%Y-%m-%d')
                     events.append({"summary": event_name, "start": {"date": start_date}, "end": {"date": end_date}})
                 except ValueError:
                     print(f"Could not parse date range for event: {line}")

        elif "Sr." in line and "Event" in line and "Date" in line:
            # Skip the header line for the Even Semester table
            continue
        elif re.match(r'^\d+\s+[\w\s()]+?\s+\d{1,2}\s+[A-Za-z]{3}\s+\d{4}', line):
            # Handling Even Semester PDF
            parts = re.split(r'\s{2,}', line)
            if len(parts) >= 2:
                event_name = parts[1].strip()
                date_str = parts[-1].strip()
                try:
                    event_date = datetime.strptime(date_str, '%d %b %Y').strftime('%Y-%m-%d')
                    events.append({"summary": event_name, "start": {"date": event_date}, "end": {"date": event_date}})
                except ValueError:
                    print(f"Could not parse date for even semester event: {line}")
        elif re.match(r'^\d+\s+\(i\).+', line):
            # Handling Even Semester detailed events
            parts = re.split(r'\s{2,}', line)
            if len(parts) >= 2:
                event_label_and_name = parts[1].strip()
                date_str = parts[-1].strip()
                try:
                    event_date = datetime.strptime(date_str, '%d %b %Y').strftime('%Y-%m-%d')
                    events.append({"summary": event_label_and_name, "start": {"date": event_date}, "end": {"date": event_date}})
                except ValueError:
                    print(f"Could not parse date for detailed even semester event: {line}")

    combined_events = sorted(events + holidays, key=lambda x: x['start']['date'])
    return combined_events

if __name__ == "__main__":
    pdf_file_path = './data/Academic Calendar 2024-25.pdf'

    calendar_data = extract_calendar_data(pdf_file_path)

    print(json.dumps(calendar_data, indent=2))