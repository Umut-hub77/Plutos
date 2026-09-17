from google import genai

client = genai.Client(api_key="AQ.Ab8RN6IC00pUyFVy-84kJqBoH3JnxyHf5IJ2VE3IySRoGa48lg")

# Hesabının erişebildiği tüm modelleri listele
for model in client.models.list():
    print(model.name)