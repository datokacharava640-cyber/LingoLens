import requests
from config import API_ENDPOINT, API_SECRET_KEY


def send_data_to_server(payload_data: dict):
  """სერვერთან უსაფრთხო კომუნიკაცია API Key-ის გამოყენებით."""
  headers = {
      "X-API-Key": API_SECRET_KEY,
      "Content-Type": "application/json",
  }

  try:
    response = requests.post(
        API_ENDPOINT, json=payload_data, headers=headers, timeout=5
    )
    if response.status_code == 200:
      return {"success": True, "data": response.json()}
    else:
      return {
          "success": False,
          "error": f"Server error status code: {response.status_code}",
      }
  except requests.exceptions.RequestException as e:
    return {"success": False, "error": str(e)}


def check_server_health():
  """სერვერის მუშაობის (Health Check) შემოწმება."""
  try:
    response = requests.get("http://37.27.255.1:8000/", timeout=3)
    return response.status_code == 200
  except:
    return False
