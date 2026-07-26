"""
Demo device inventory - Secure Device Posture Tracker
-------------------------------------------------------
This is a hardcoded "seed" dataset representing a small organization's
devices. In a real product this would come from a database + an "add
device" form, but for the MVP we hardcode it so the interesting logic
(CVE lookup + AI prioritization) is the focus.

Mix of intentionally outdated and current software so the demo produces
real, varied CVE results.
"""

DEVICES = [
    {
        "id": 1,
        "name": "Front Desk PC",
        "os": "Windows 10",
        "os_version": "21H1",
        "software": ["Google Chrome 90", "Adobe Acrobat Reader DC 2020"],
    },
    {
        "id": 2,
        "name": "Manager Laptop",
        "os": "Windows 11",
        "os_version": "23H2",
        "software": ["Microsoft Edge 124", "Zoom 5.16"],
    },
    {
        "id": 3,
        "name": "Back Office Server",
        "os": "Windows Server 2016",
        "os_version": "1607",
        "software": ["OpenSSL 1.0.1", "Apache HTTP Server 2.4.29"],
    },
    {
        "id": 4,
        "name": "Reception iMac",
        "os": "macOS",
        "os_version": "10.14 Mojave",
        "software": ["Safari 12", "Microsoft Office 2016"],
    },
    {
        "id": 5,
        "name": "Warehouse Scanner Tablet",
        "os": "Android",
        "os_version": "9.0",
        "software": ["WebView 79"],
    },
    {
        "id": 6,
        "name": "Sales Laptop 2",
        "os": "Windows 11",
        "os_version": "24H2",
        "software": ["Google Chrome 126", "Slack 4.39"],
    },
    {
        "id": 7,
        "name": "Accounting Desktop",
        "os": "Windows 10",
        "os_version": "22H2",
        "software": ["Adobe Acrobat Reader DC 2024", "QuickBooks Desktop 2021"],
    },
    {
        "id": 8,
        "name": "IT Closet Router Admin PC",
        "os": "Windows 7",
        "os_version": "SP1",
        "software": ["Internet Explorer 11"],
    },
]


def get_device(device_id: int):
    return next((d for d in DEVICES if d["id"] == device_id), None)
