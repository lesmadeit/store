# import ngrok python sdk

import time
from pyngrok import ngrok
ngrok.set_auth_token("2rLZ0aaglgI9E6HZOOWEaZaPmEr_5NMfh31hTs2YEN64Va7W")

# Establish connectivity
listener = ngrok.connect(8000)

# Output ngrok url to console
print(f"Ingress established at {listener.public_url}")

# Keep the listener alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Closing listener")