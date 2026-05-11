"""Create a Google Sheet with Chargebotic prospect list + call tracker."""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import json

SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
ROOT = os.path.join(os.path.dirname(__file__), '..', '..', '..')
CREDS_FILE = os.path.join(ROOT, 'credentials.json')
TOKEN_FILE = os.path.join(ROOT, 'token.json')


def get_creds():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())
    return creds


def main():
    creds = get_creds()
    sheets = build('sheets', 'v4', credentials=creds)

    # Create spreadsheet
    spreadsheet = sheets.spreadsheets().create(body={
        'properties': {'title': 'Chargebotic - Prospect Tracker'},
        'sheets': [
            {'properties': {'title': 'Priority 10', 'index': 0}},
            {'properties': {'title': 'Robot Makers (20)', 'index': 1}},
            {'properties': {'title': 'End Users (30)', 'index': 2}},
        ]
    }).execute()

    sheet_id = spreadsheet['spreadsheetId']
    sheet_url = spreadsheet['spreadsheetUrl']

    # Priority 10 - Call tracker
    priority_header = ['#', 'Company', 'Why Priority', 'Contact Found', 'Called?', 'Date Called', 'Response', 'Pain Point Mentioned', 'Interest Level (1-5)', 'Next Step', 'Notes']
    priority_data = [
        ['1', 'Bear Robotics', '4h charge / 12h shift = PAIN REEL', '', '', '', '', '', '', '', ''],
        ['2', 'UCSF Medical Center', 'Robots 24/7, right in SF', '', '', '', '', '', '', '', ''],
        ['3', 'Stanford Health Care', '30 min de SF', '', '', '', '', '', '', '', ''],
        ['4', 'Webcor Builders', 'GC local, robots sur chantier', '', '', '', '', '', '', '', ''],
        ['5', 'Locus Robotics', '350 sites, charging at scale', '', '', '', '', '', '', '', ''],
        ['6', 'DHL Supply Chain', '8000+ robots, charging = nightmare', '', '', '', '', '', '', '', ''],
        ['7', 'Relay Robotics', 'San Jose, hotels 24/7', '', '', '', '', '', '', '', ''],
        ['8', 'Knightscope', 'Mountain View, patrol 24/7', '', '', '', '', '', '', '', ''],
        ['9', 'Avidbots', '1000+ robots, downtime = lost $', '', '', '', '', '', '', '', ''],
        ['10', 'Starship Technologies', 'SF, sidewalk robots', '', '', '', '', '', '', '', ''],
    ]

    # Robot Makers
    makers_header = ['#', 'Company', 'Sector', 'Location', 'Website', 'Notes', 'Contacted?', 'Response']
    makers_data = [
        ['1', 'Bear Robotics', 'Restaurant robots', 'Redwood City, CA', 'bearrobotics.ai', 'Servi robot, 4h charge/12h shift', '', ''],
        ['2', 'Locus Robotics', 'Warehouse AMR', 'Wilmington, MA', 'locusrobotics.com', '350+ sites worldwide', '', ''],
        ['3', 'Knightscope', 'Security patrol', 'Mountain View, CA', 'knightscope.com', 'Public (KSCP), 24/7 outdoor', '', ''],
        ['4', 'Relay Robotics', 'Hotel delivery', 'San Jose, CA', 'relayrobotics.com', '1.5M+ deliveries', '', ''],
        ['5', 'Avidbots', 'Floor cleaning', 'Kitchener, ON', 'avidbots.com', '1000+ robots', '', ''],
        ['6', 'Brain Corp', 'Floor cleaning AI', 'San Diego, CA', 'braincorp.com', 'Powers Tennant robots', '', ''],
        ['7', 'Dusty Robotics', 'Construction', 'Mountain View, CA', 'dustyrobotics.com', 'FieldPrinter', '', ''],
        ['8', 'Nimble', 'Warehouse fulfillment', 'Bay Area, CA', 'nimble.ai', 'Autonomous fulfillment', '', ''],
        ['9', 'Canvas (Intrinsic)', 'Construction', 'SF, CA', 'canvas.build', 'Used by Webcor/Suffolk', '', ''],
        ['10', 'Built Robotics', 'Heavy equipment', 'SF, CA', 'builtrobotics.com', 'Autonomous bulldozers', '', ''],
        ['11', 'Burro', 'Agriculture', 'Philadelphia, PA', 'burro.ai', 'Self-driving farm carts', '', ''],
        ['12', 'Ambi Robotics', 'Warehouse sorting', 'Berkeley, CA', 'ambirobotics.com', 'AI parcel sorting', '', ''],
        ['13', 'Agility Robotics', 'Humanoid (Digit)', 'Corvallis, OR', 'agilityrobotics.com', 'Healthcare + logistics', '', ''],
        ['14', 'Starship Technologies', 'Last-mile delivery', 'SF, CA', 'starship.xyz', 'College campuses', '', ''],
        ['15', 'Serve Robotics', 'Last-mile delivery', 'LA, CA', 'serverobotics.com', 'Uber Eats delivery', '', ''],
        ['16', 'Nuro', 'Autonomous delivery', 'Mountain View, CA', 'nuro.ai', 'Grocery/food delivery', '', ''],
        ['17', 'Fetch Robotics (Zebra)', 'Warehouse AMR', 'San Jose, CA', 'fetchrobotics.com', 'Acquired by Zebra', '', ''],
        ['18', 'Seegrid', 'Warehouse AGV', 'Pittsburgh, PA', 'seegrid.com', 'Vision-guided vehicles', '', ''],
        ['19', '6 River Systems (Ocado)', 'Warehouse picking', 'Waltham, MA', '6river.com', 'Chuck robots', '', ''],
        ['20', 'Cobalt Robotics', 'Security indoor', 'SF, CA', 'cobaltrobotics.com', 'Office security robots', '', ''],
    ]

    # End Users
    users_header = ['#', 'Company', 'Robot Use', 'Location', 'Sector', 'Notes', 'Contacted?', 'Response']
    users_data = [
        ['21', 'DHL Supply Chain', '8000+ robots', 'US HQ Ohio', 'Logistics', '1000+ Boston Dynamics ordered', '', ''],
        ['22', 'Amazon Robotics', '1M+ robots', 'Global', 'Logistics', 'Biggest fleet in world', '', ''],
        ['23', 'GXO Logistics', 'AMRs at scale', 'Greenwich, CT', 'Logistics', 'Largest pure-play 3PL', '', ''],
        ['24', 'XPO Logistics', 'Robotic picking', 'Greenwich, CT', 'Logistics', '400+ warehouses', '', ''],
        ['25', 'GEODIS', '1000 Locus robots', 'US presence', 'Logistics', 'Major 3PL', '', ''],
        ['26', 'UPS', '127+ automated buildings', 'Atlanta, GA', 'Logistics', '24 more in 2026', '', ''],
        ['27', 'FedEx', 'Berkshire Grey robots', 'Memphis, TN', 'Logistics', 'Scoop robotic unloader', '', ''],
        ['28', 'Walmart', 'AMRs + floor cleaners', 'Bentonville, AR', 'Retail', 'Huge fleet stores + DCs', '', ''],
        ['29', 'Target', 'Warehouse automation', 'Minneapolis, MN', 'Retail', 'DC robots', '', ''],
        ['30', 'Shopify', 'Fulfillment robots', 'US operations', 'Retail', '6RS Chuck robots', '', ''],
        ['31', 'Marriott (RAR Hospitality)', 'Relay delivery', 'San Marcos, CA', 'Hospitality', 'Multiple hotels', '', ''],
        ['32', 'Aloft Hotels', 'Botlr delivery', 'Multiple US', 'Hospitality', 'Pioneer hotel robots', '', ''],
        ['33', 'Hilton Hotels', 'Connie concierge', 'Multiple US', 'Hospitality', 'IBM Watson powered', '', ''],
        ['34', 'Henn-na Hotel', 'Full robot staff', 'Japan/expanding', 'Hospitality', 'Most robotic hotel', '', ''],
        ['35', "Denny's", 'Bear Robotics Servi', 'Multiple US', 'Food Service', 'Robot servers', '', ''],
        ['36', "Chili's", 'Rita robot (Bear)', 'Multiple US', 'Food Service', 'Robot servers', '', ''],
        ['37', 'Kaiser Permanente', 'Pharmacy + delivery', 'Oakland, CA', 'Healthcare', 'Large hospital system', '', ''],
        ['38', 'Stanford Health Care', 'TUG delivery', 'Stanford, CA', 'Healthcare', 'Bay Area accessible', '', ''],
        ['39', 'UCSF Medical Center', 'Autonomous delivery', 'SF, CA', 'Healthcare', 'RIGHT IN SF', '', ''],
        ['40', 'Mayo Clinic', 'Multiple robot types', 'Rochester, MN', 'Healthcare', 'Innovation leader', '', ''],
        ['41', 'Cleveland Clinic', 'Surgical + delivery', 'Cleveland, OH', 'Healthcare', 'Top US hospital', '', ''],
        ['42', 'Kroger', 'Floor cleaning + fulfillment', 'Cincinnati, OH', 'Retail', 'Brain Corp floor robots', '', ''],
        ['43', "Sam's Club", 'Floor scrubbing', 'Bentonville, AR', 'Retail', 'Brain Corp powered', '', ''],
        ['44', "Lowe's", 'LoweBot (Fellow Robots)', 'Mooresville, NC', 'Retail', 'In-store navigation', '', ''],
        ['45', 'Simon Property Group', 'Security + cleaning', 'Indianapolis, IN', 'Retail', 'Largest US mall operator', '', ''],
        ['46', 'Webcor Builders', 'Canvas drywall robots', 'SF, CA', 'Construction', 'Bay Area GC', '', ''],
        ['47', 'Suffolk Construction', 'Canvas + Dusty', 'Boston, MA', 'Construction', 'Innovation-focused GC', '', ''],
        ['48', 'Bechtel', 'Construction robots', 'Reston, VA', 'Construction', 'Massive infra builder', '', ''],
        ['49', "Driscoll's", 'Berry picking robots', 'Watsonville, CA', 'Agriculture', 'Bay Area adjacent', '', ''],
        ['50', 'Taylor Farms', 'Autonomous processing', 'Salinas, CA', 'Agriculture', 'Largest fresh produce', '', ''],
    ]

    # Write all sheets
    sheets.spreadsheets().values().batchUpdate(spreadsheetId=sheet_id, body={
        'valueInputOption': 'RAW',
        'data': [
            {'range': 'Priority 10!A1', 'values': [priority_header] + priority_data},
            {'range': 'Robot Makers (20)!A1', 'values': [makers_header] + makers_data},
            {'range': 'End Users (30)!A1', 'values': [users_header] + users_data},
        ]
    }).execute()

    # Format headers bold + freeze first row
    sheet_ids = {s['properties']['title']: s['properties']['sheetId'] for s in spreadsheet['sheets']}
    requests = []
    for title, sid in sheet_ids.items():
        requests.append({
            'repeatCell': {
                'range': {'sheetId': sid, 'startRowIndex': 0, 'endRowIndex': 1},
                'cell': {'userEnteredFormat': {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}}},
                'fields': 'userEnteredFormat(textFormat,backgroundColor)'
            }
        })
        requests.append({
            'updateSheetProperties': {
                'properties': {'sheetId': sid, 'gridProperties': {'frozenRowCount': 1}},
                'fields': 'gridProperties.frozenRowCount'
            }
        })
        # Auto-resize columns
        requests.append({
            'autoResizeDimensions': {
                'dimensions': {'sheetId': sid, 'dimension': 'COLUMNS', 'startIndex': 0, 'endIndex': 15}
            }
        })

    sheets.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={'requests': requests}).execute()

    print(f"\nGoogle Sheet created!")
    print(f"URL: {sheet_url}")
    print(f"Sheet ID: {sheet_id}")


if __name__ == '__main__':
    main()
