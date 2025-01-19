import PyPDF2
import re
import json
from datetime import datetime

def extract_academic_calendar(pdf_path):
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
        if "LIST OF HOLIDAYS" in line:
            is_holiday_section = True
            continue

        if is_holiday_section:
            if re.match(r'^\d+\.\s+[\w\s()\*]+?\s+\d{1,2}\s+[A-Za-z]{3}\s+\d{4}', line):
                parts = re.split(r'\s{2,}', line) # Split by multiple spaces
                if len(parts) >= 2:
                    event_name_part = parts[0].split('.', 1)[1].strip()
                    date_part = parts[-1].strip()
                    try:
                        holiday_date = datetime.strptime(date_part, '%d %b %Y').strftime('%Y-%m-%d')
                        holidays.append({"summary": f"Holiday - {event_name_part}",
                                        "start": {"date": holiday_date},
                                        "end": {"date": holiday_date}})
                    except ValueError:
                        print(f"Could not parse date for holiday: {line}")

        elif "SER." not in line and "EVENT" not in line and line and not re.match(r'^==Start of OCR for page \d+==$', line) and not re.match(r'^==End of OCR for page \d+==$', line) and "Updated on" not in line and "JIIT NOIDA" not in line and "ACADEMIC CALENDAR" not in line:
            date_match_odd = re.search(r'(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})', line)
            date_match_even = re.search(r'(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})\s*$', line) # Handle end of line for even semester

            if date_match_odd:
                event_name = line.split(date_match_odd.group(1))[0].strip()
                try:
                    event_date_str = date_match_odd.group(1)
                    event_date = datetime.strptime(event_date_str, '%d %b %Y').strftime('%Y-%m-%d')
                    events.append({"summary": event_name,
                                   "start": {"date": event_date},
                                   "end": {"date": event_date}})
                except ValueError:
                    print(f"Could not parse date for event (Odd): {line}")
            elif date_match_even:
                 parts = line.rsplit(date_match_even.group(1), 1)
                 if parts:
                     event_name = parts[0].strip()
                     try:
                         event_date_str = date_match_even.group(1)
                         event_date = datetime.strptime(event_date_str, '%d %b %Y').strftime('%Y-%m-%d')
                         events.append({"summary": event_name,
                                        "start": {"date": event_date},
                                        "end": {"date": event_date}})
                     except ValueError:
                         print(f"Could not parse date for event (Even): {line}")
            elif '–' in line or '-' in line:
                separator = '–' if '–' in line else '-'
                parts = line.split(separator)
                if len(parts) == 2:
                    event_name_part = parts[0].strip()
                    date_range_part = parts[1].strip()

                    date_matches = re.findall(r'(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})', date_range_part)
                    if len(date_matches) == 2:
                        try:
                            start_date_str = date_matches[0]
                            end_date_str = date_matches[1]
                            start_date = datetime.strptime(start_date_str, '%d %b %Y').strftime('%Y-%m-%d')
                            end_date = datetime.strptime(end_date_str, '%d %b %Y').strftime('%Y-%m-%d')
                            events.append({"summary": event_name_part,
                                           "start": {"date": start_date},
                                           "end": {"date": end_date}})
                        except ValueError:
                            print(f"Could not parse date range for event: {line}")

    combined_events = sorted(events + holidays, key=lambda x: x['start']['date'])

    return combined_events

if __name__ == "__main__":
    pdf_file_path = './data/Academic Calendar 2024-25.pdf' 
    calendar_data = extract_academic_calendar(pdf_file_path)

    print(json.dumps(calendar_data, indent=2))