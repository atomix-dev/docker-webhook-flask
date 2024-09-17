from flask import Flask, request, jsonify
import subprocess
import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Set up rate limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["8 per 5 minutes"]
)

DOCKER_PASSWORD = os.getenv('DOCKER_PASSWORD')

COMMAND = f"echo ${DOCKER_PASSWORD} | docker login --username squizy --password-stdin && docker rm bios-uin -f && docker pull squizy/bios-test:latest && docker run -d --rm --name bios-uin -p 8000:80 --env-file ./.env squizy/bios-test:latest"

@app.route('/webhook', methods=['POST'])
@limiter.limit("8 per 5 minutes")
def webhook():
    print('Webhook received')
    data = request.json
    print(data)

    if not data or 'push_data' not in data:
        print('No webhook payload')
        return jsonify({'error': 'Invalid webhook payload'}), 400

    if data['push_data'].get('tag') == 'latest':
        repository_name = data['repository']['repo_name']
        tag = data['push_data']['tag']
        print(f"New image pushed: {repository_name}:{tag}")

        try:
            # Execute the shell command
            result = subprocess.run(COMMAND, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"Deployment restarted successfully: {result.stdout.decode()}")
            return jsonify({'message': 'Deployment restarted'}), 200
        except subprocess.CalledProcessError as e:
            print(f"Error restarting deployment: {e.stderr.decode()}")
            return jsonify({'error': 'Failed to restart deployment'}), 500
    else:
        return jsonify({'error': 'Invalid webhook payload'}), 400

if __name__ == '__main__':
    app.run(port=3000, debug=True)
