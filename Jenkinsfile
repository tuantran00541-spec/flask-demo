pipeline {
    agent { label 'built-in' }

    options {
        disableConcurrentBuilds()
        skipDefaultCheckout()
    }

    environment {
        RELEASE_ROOT = '/opt/flask-demo'
    }

    stages {
        stage('Checkout') {
            steps {
                sh '''
                    if [ ! -w "$RELEASE_ROOT/releases" ] ||
                       [ "$(systemctl show -p WorkingDirectory --value flask-demo.service)" != "$RELEASE_ROOT/current" ]; then
                        echo "Prepare the release directory and install the current service unit (README step 2)." >&2
                        exit 1
                    fi
                '''
                checkout scm
            }
        }

        stage('Build') {
            steps {
                script {
                    env.RELEASE_DIR = sh(
                        script: 'mktemp -d "$RELEASE_ROOT/releases/release.XXXXXXXX"',
                        returnStdout: true
                    ).trim()
                }
                sh '''
                    cp app.py test_app.py requirements.txt "$RELEASE_DIR/"
                    cd "$RELEASE_DIR"
                    python3 -m venv venv
                    venv/bin/python -m pip install -r requirements.txt
                '''
            }
        }

        stage('Test') {
            steps {
                sh '''
                    rm -f -- "$WORKSPACE/report.xml"
                    cd "$RELEASE_DIR"
                    venv/bin/python -m pytest -v --junitxml="$WORKSPACE/report.xml"
                    venv/bin/python -m gunicorn --check-config app:app
                '''
            }
            post {
                always {
                    junit testResults: 'report.xml', allowEmptyResults: true
                }
            }
        }

        stage('Deploy') {
            steps {
                sh 'bash deploy/activate-release.sh "$RELEASE_DIR"'
            }
        }
    }

    post {
        cleanup {
            sh '''
                if [ -n "${RELEASE_DIR:-}" ] &&
                   [ "$(readlink "$RELEASE_ROOT/current")" != "$RELEASE_DIR" ]; then
                    find "$RELEASE_DIR" -depth -delete
                fi
            '''
        }
        success {
            echo 'Pipeline thành công! Ứng dụng đã được triển khai.'
        }
    }
}
