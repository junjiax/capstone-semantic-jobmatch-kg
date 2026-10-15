from google import genai

# 1. Khởi tạo client với API Key
client = genai.Client(api_key="AIzaSyCHr_ul5lww6uESVKWSwQihmfDhWd0NfcY")

# 2. Duyệt qua danh sách các model từ client.models
print("Các model hỗ trợ tạo nội dung:")
for m in client.models.list():
    if "generateContent" in m.supported_actions:
        print(f"- {m.name}")