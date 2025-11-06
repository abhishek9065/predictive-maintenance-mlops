
pipeline {
    agent any
    
    environment {
        PYTHON_VERSION = '3.13'
        VENV_DIR = 'venv'
        MODEL_REGISTRY = 'models'
    }
    
    stages {
        stage('Setup') {
            steps {
                echo 'Setting up Python environment...'
                sh '''
                    python -m venv ${VENV_DIR}
                    . ${VENV_DIR}/bin/activate
                    pip install -r requirements.txt
                '''
            }
        }
        
        stage('Data Generation') {
            steps {
                echo 'Generating training data...'
                sh '''
                    . ${VENV_DIR}/bin/activate
                    python generate_sample_data.py --samples 2000
                '''
            }
        }
        
        stage('Model Training') {
            steps {
                echo 'Training models with Katib...'
                sh '''
                    . ${VENV_DIR}/bin/activate
                    python katib_tuning.py --model=random_forest --data_path=data
                    python katib_tuning.py --model=gradient_boosting --data_path=data
                '''
            }
        }
        
        stage('Model Testing') {
            steps {
                echo 'Running model tests...'
                sh '''
                    . ${VENV_DIR}/bin/activate
                    python test_advanced_components.py
                '''
            }
        }
        
        stage('Edge Deployment - TFLite') {
            steps {
                echo 'Converting to TensorFlow Lite...'
                sh '''
                    . ${VENV_DIR}/bin/activate
                    python src/edge/tflite_converter.py
                '''
            }
        }
        
        stage('Monitoring - Evidently') {
            steps {
                echo 'Running Evidently AI monitoring...'
                sh '''
                    . ${VENV_DIR}/bin/activate
                    python src/monitoring/evidently_monitor.py
                '''
            }
        }
        
        stage('Security Scan - OPA') {
            steps {
                echo 'Running security policy checks...'
                sh '''
                    # OPA policy validation
                    opa test policies/
                '''
            }
        }
        
        stage('Docker Build') {
            steps {
                echo 'Building Docker images...'
                sh '''
                    docker build -t mlops-api:${BUILD_NUMBER} -f Dockerfile.api .
                    docker build -t mlops-training:${BUILD_NUMBER} .
                '''
            }
        }
        
        stage('Kubernetes Deployment') {
            when {
                branch 'main'
            }
            steps {
                echo 'Deploying to Kubernetes...'
                sh '''
                    kubectl apply -f kubernetes/namespace.yaml
                    kubectl apply -f kubernetes/api-deployment.yaml
                    kubectl set image deployment/mlops-api mlops-api=mlops-api:${BUILD_NUMBER} -n kubeflow
                '''
            }
        }
        
        stage('Integration Tests') {
            steps {
                echo 'Running integration tests...'
                sh '''
                    . ${VENV_DIR}/bin/activate
                    python -m pytest tests/integration/
                '''
            }
        }
    }
    
    post {
        success {
            echo 'Pipeline completed successfully!'
            archiveArtifacts artifacts: 'models/**/*.pkl', allowEmptyArchive: false
            archiveArtifacts artifacts: 'models/edge/**/*.tflite', allowEmptyArchive: false
            archiveArtifacts artifacts: 'reports/**/*.html', allowEmptyArchive: false
        }
        failure {
            echo 'Pipeline failed!'
            emailext (
                subject: "Build Failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: "Build failed. Check console output for details.",
                to: "team@example.com"
            )
        }
        always {
            cleanWs()
        }
    }
}
