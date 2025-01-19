import PyPDF2
import json
import re
from datetime import datetime

def extract_calendar_data(pdf_path):
    """Extracts events and holidays from the provided PDF and formats them into JSON.
    Args:
        pdf_path (str): The path to the PDF file.
    Returns:
        str: A JSON string containing the extracted data.
    """
    events = []
    holidays = []
    in_holiday_section = False
    event_section_started = False

    with open(pdf_path, 'rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        for page in reader.pages:
            text = page.extract_text()
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                
                if "LIST OF HOLIDAYS" in line:
                  in_holiday_section = True
                  event_section_started = False
                  continue
                  
                if in_holiday_section:
                    holiday_match = re.match(r'([\w\s]+)\s+(\d{1,2}\s+\w{3}\s+\d{4})\s*.*', line)
                    if holiday_match:
                        name = holiday_match.group(1).strip()
                        date_str = holiday_match.group(2)
                        try:
                            date = datetime.strptime(date_str, '%d %b %Y').strftime('%Y-%m-%d')
                            holidays.append({"summary": f"Holiday - {name}", "start": {"date": date}, "end": {"date": date}})
                        except ValueError:
                            print(f"Could not parse date: {date_str}")
                    continue

                if "Registration / Reporting" in line:
                  event_section_started=True
                  continue
                
                if event_section_started:
                    date_match = re.findall(r'(\d{1,2}(?:-\d{1,2})?\s+\w{3}\s+\d{4})', line)
                    if date_match:
                        event_name = line.split(date_match[0])[0].strip()
                        for date_str in date_match:
                            if '-' in date_str:
                                try:
                                    start_date_str, end_date_str = date_str.split('-')
                                    start_date = datetime.strptime(start_date_str.strip(), '%d %b %Y').strftime('%Y-%m-%d')
                                    end_date = datetime.strptime(end_date_str.strip(), '%d %b %Y').strftime('%Y-%m-%d')
                                    current_date = start_date
                                    while current_date <= end_date:
                                        events.append({"summary": event_name, "start": {"date": current_date}, "end": {"date": current_date}})
                                        date_object = datetime.strptime(current_date, '%Y-%m-%d')
                                        date_object = date_object.replace(day=date_object.day + 1)
                                        current_date = datetime.strftime(date_object, '%Y-%m-%d')
                                except ValueError as e:
                                    print(f"Could not parse date: {date_str}: {e}")
                            else:
                                try:
                                    date = datetime.strptime(date_str.strip(), '%d %b %Y').strftime('%Y-%m-%d')
                                    events.append({"summary": event_name, "start": {"date": date}, "end": {"date": date}})
                                except ValueError as e:
                                    print(f"Could not parse date: {date_str}: {e}")


    
    all_events = holidays + events
    return json.dumps(all_events, indent=4)


if __name__ == '__main__':
    pdf_file_path = './data/Academic Calendar 2024-25.pdf'
    json_output = extract_calendar_data(pdf_file_path)
    all_events = json.loads(json_output)
    all_events.sort(key=lambda item: item["start"]["date"])
    sorted_json_output = json.dumps(all_events, indent=4)

    print(sorted_json_output)
    with open('calendar.json', 'w') as outfile:
        outfile.write(sorted_json_output)