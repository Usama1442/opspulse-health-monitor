pipeline {
    agent any

    stages {
        stage('Install Dependencies') {
            steps {
                sh '''
                    python3 --version
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install -r requirements.txt
                    pip install -r requirements-dev.txt
                    pip install pytest
                '''
            }
        }

        stage('Lint Code') {
            steps {
                sh '''
                    . .venv/bin/activate
                    flake8 app.py tests/
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                    . .venv/bin/activate
                    pytest -v
                '''
            }
        }
    }
}
