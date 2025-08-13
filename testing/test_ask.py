import requests

# Paste your valid Firebase ID token here (from frontend)
firebase_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjJiN2JhZmIyZjEwY2FlMmIxZjA3ZjM4MTZjNTQyMmJlY2NhNWMyMjMiLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoiVGVzdGluZyIsImlzcyI6Imh0dHBzOi8vc2VjdXJldG9rZW4uZ29vZ2xlLmNvbS9wcm92ZW5hbmNlYWktZmlyZWJhc2UiLCJhdWQiOiJwcm92ZW5hbmNlYWktZmlyZWJhc2UiLCJhdXRoX3RpbWUiOjE3NTE5OTY0MTMsInVzZXJfaWQiOiJ6MkFVNTZ3MHdoWm9yMllUZ3RIWGY2UU5oQ1EyIiwic3ViIjoiejJBVTU2dzB3aFpvcjJZVGd0SFhmNlFOaENRMiIsImlhdCI6MTc1NTA5Njg1NCwiZXhwIjoxNzU1MTAwNDU0LCJlbWFpbCI6InRlc3Rpbmd1c2VyQHRlc3QuY29tIiwiZW1haWxfdmVyaWZpZWQiOmZhbHNlLCJmaXJlYmFzZSI6eyJpZGVudGl0aWVzIjp7ImVtYWlsIjpbInRlc3Rpbmd1c2VyQHRlc3QuY29tIl19LCJzaWduX2luX3Byb3ZpZGVyIjoicGFzc3dvcmQifX0.xX2pu42snhBsOhOpHhuijWRrdku094Ke4fFRBX4g8p3eTsuiXb5daQ-SV09pnpNFBY6bNRGTdC7NZzcL8rOEgmyw49B6kfY4obmZN1hObcK4r8qcY-Kq3hxeYF-KcMGSMt-FdOlvuiTImdko9mQsZ-3GmGXvK7kAZ93H-TqZb14aLR0TRuV3UAeu3TQhuk_FsCaVGuQFG4fnF9I27_XT7O4KX4Xku1dFGtppJWLBwqGWwpQpsLsAEJ4HRKaCVCCBwKDIbbtCTMTN2kf3zVHyeNfmfDtSQ5Gpx4WCXYbGcs6iDGEj4iKXOXLbJEGLtN-jHdieU-go9WT8p_O6VW478g"

headers = {
    "Authorization": f"Bearer {firebase_token}",
    "Content-Type": "application/json"
}

data = {
    "message": "Hello from test script!",
    "context": "",
    "chat_id": "Test",
    "chat_subject": "Test"
}

response = requests.post("http://localhost:3000/ask", json=data, headers=headers)

print("Status Code:", response.status_code)
print("Response JSON:", response.json())

