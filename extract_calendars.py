import PyPDF2
import json
from datetime import datetime
import re

def parse_date(date_str):
    """Parse date string to YYYY-MM-DD format"""
    try:
        # Clean up the date string
        date_str = re.sub(r'\s+', ' ', date_str.strip())
        # Handle date ranges by taking the first date
        if '-' in date_str:
            date_str = date_str.split('-')[0].strip()
        date_obj = datetime.strptime(date_str, '%d %b %Y')
        return date_obj.strftime('%Y-%m-%d')
    except ValueError:
        return None

def clean_event_description(desc):
    """Clean and format event description"""
    # Remove multiple spaces
    desc = re.sub(r'\s+', ' ', desc.strip())
    # Remove leading numbers and dots
    desc = re.sub(r'^\d+\.\s*', '', desc)
    # Remove any trailing dashes and spaces
    desc = re.sub(r'\s*-\s*$', '', desc)
    return desc

def extract_events_from_pdf(pdf_path):
    """Extract events from the academic calendar PDF"""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()

    events = []
    
    # Split text into sections
    sections = text.split('\n')
    
    # Process each line
    for i, line in enumerate(sections):
        # Skip empty lines and headers
        if not line.strip() or 'SER.' in line or 'ACADEMIC CALENDAR' in line:
            continue

        # Look for dates in the line
        date_matches = re.findall(r'(\d{1,2}\s+[A-Za-z]+\s+\d{4}(?:\s*-\s*\d{1,2}\s+[A-Za-z]+\s+\d{4})?)', line)
        
        if date_matches:
            for date_str in date_matches:
                formatted_date = parse_date(date_str)
                if formatted_date:
                    # Get the event description
                    # Remove the date and any surrounding parentheses
                    event_desc = re.sub(r'\(\w+\)', '', line)  # Remove day abbreviations like (Mon)
                    event_desc = re.sub(date_str, '', event_desc)
                    event_desc = clean_event_description(event_desc)
                    
                    # Skip if description is empty or contains only special characters
                    if not event_desc or event_desc.isspace() or all(not c.isalnum() for c in event_desc):
                        continue
                        
                    # Handle special cases
                    if 'LIST OF HOLIDAYS' in event_desc:
                        continue
                        
                    # Try to combine with previous line if this line seems incomplete
                    if i > 0 and (event_desc.startswith('of') or event_desc.startswith('and') or event_desc.startswith('/')):
                        prev_line = clean_event_description(sections[i-1])
                        if not any(date in prev_line for date in date_matches):
                            event_desc = f"{prev_line} {event_desc}"
                    
                    event = {
                        "summary": event_desc,
                        "start": {"date": formatted_date},
                        "end": {"date": formatted_date}
                    }
                    events.append(event)

    # Process holidays section
    holidays_section = re.findall(r'LIST OF HOLIDAYS.*?(?=Student Vacation)', text, re.DOTALL)
    if holidays_section:
        holidays_text = holidays_section[0]
        holiday_matches = re.findall(r'(\d+)\.\s+(.*?)\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})\s*(?:\([A-Za-z]+\))?', holidays_text)
        
        for _, holiday_name, date_str in holiday_matches:
            formatted_date = parse_date(date_str)
            if formatted_date:
                event = {
                    "summary": clean_event_description(holiday_name),
                    "start": {"date": formatted_date},
                    "end": {"date": formatted_date}
                }
                events.append(event)

    # Sort events by start date
    events.sort(key=lambda x: datetime.strptime(x['start']['date'], '%Y-%m-%d'))
    
    # Remove duplicates while preserving order
    unique_events = []
    seen = set()
    for event in events:
        event_tuple = (event['summary'], event['start']['date'])
        if event_tuple not in seen and len(event['summary']) > 3:  # Minimum length check
            seen.add(event_tuple)
            unique_events.append(event)
    
    return unique_events

def save_to_json(events, output_file):
    """Save the events to a JSON file"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=2, ensure_ascii=False)

def main():
    pdf_path = "./data/Academic Calendar 2024-25.pdf"
    output_file = "academic_calendar_events.json"
    
    try:
        events = extract_events_from_pdf(pdf_path)
        save_to_json(events, output_file)
        print(f"Successfully extracted {len(events)} events and saved to {output_file}")
    except Exception as e:
        print(f"Error processing PDF: {e}")

if __name__ == "__main__":
    main()