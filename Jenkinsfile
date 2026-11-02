pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build') {
            steps {
                sh 'python3 -m venv venv'
                sh 'venv/bin/pip install -r requirements.txt'
            }
        }

        stage('Test') {
            steps {
                sh 'venv/bin/pytest -v --junitxml=report.xml'
            }
        }

        stage('Deploy') {
            steps {
                sh 'sudo systemctl restart flask-demo'
                sh 'sleep 3 && curl -fsS http://localhost:5000/health'
            }
        }
    }

    post {
        always {
            junit 'report.xml'
        }
        success {
            echo 'Pipeline thành công! Ứng dụng đã được triển khai.'
        }
        failure {
            echo 'Pipeline thất bại! Không triển khai bản lỗi.'
        }
    }
}
