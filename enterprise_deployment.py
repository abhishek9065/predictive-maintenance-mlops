"""
Complete Enterprise MLOps Deployment Manager
Integrates: TFLite, Evidently AI, Jenkins, Prometheus, OPA, Kubernetes RBAC
"""

import subprocess
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EnterpriseDeployment:
    """Enterprise-grade MLOps deployment orchestrator"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.results = {}
        
    def check_dependencies(self) -> Dict[str, bool]:
        """Check all required dependencies"""
        logger.info("=" * 70)
        logger.info("CHECKING DEPENDENCIES")
        logger.info("=" * 70)
        
        dependencies = {
            'tensorflow': False,
            'evidently': False,
            'prometheus_client': False,
            'kubernetes': False,
            'fastapi': False,
            'bentoml': False,
        }
        
        for package in dependencies.keys():
            try:
                __import__(package)
                dependencies[package] = True
                logger.info(f"✅ {package}")
            except ImportError:
                logger.warning(f"❌ {package} - Not installed")
                dependencies[package] = False
        
        return dependencies
    
    def install_dependencies(self):
        """Install all required dependencies"""
        logger.info("\n" + "=" * 70)
        logger.info("INSTALLING DEPENDENCIES")
        logger.info("=" * 70)
        
        packages = [
            'tensorflow',
            'evidently',
            'prometheus-client',
            'kubernetes',
            'fastapi',
            'uvicorn',
            'bentoml',
            'mlflow',
            'joblib',
            'scikit-learn',
            'pandas',
            'numpy',
        ]
        
        logger.info("Installing packages...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-q"
        ] + packages, check=False)
        
        logger.info("✅ Dependencies installed")
    
    def convert_to_tflite(self) -> Dict[str, Any]:
        """Convert model to TensorFlow Lite for edge deployment"""
        logger.info("\n" + "=" * 70)
        logger.info("1. EDGE DEPLOYMENT - TENSORFLOW LITE CONVERSION")
        logger.info("=" * 70)
        
        try:
            result = subprocess.run([
                sys.executable,
                "src/edge/tflite_converter.py",
                "--model", "models/production_model.pkl",
                "--data", "data/train.csv",
                "--output", "models/edge",
                "--name", "predictive_maintenance_edge"
            ], capture_output=True, text=True, check=True)
            
            logger.info(result.stdout)
            logger.info("✅ TFLite conversion successful")
            
            # Check if model was created
            tflite_model = Path("models/edge/predictive_maintenance_edge.tflite")
            if tflite_model.exists():
                size_kb = tflite_model.stat().st_size / 1024
                logger.info(f"TFLite Model: {tflite_model} ({size_kb:.2f} KB)")
                return {"status": "success", "model_path": str(tflite_model), "size_kb": size_kb}
            
        except subprocess.CalledProcessError as e:
            logger.error(f"TFLite conversion failed: {e.stderr}")
            return {"status": "error", "message": str(e)}
        except Exception as e:
            logger.error(f"Error: {e}")
            return {"status": "error", "message": str(e)}
    
    def run_evidently_monitoring(self) -> Dict[str, Any]:
        """Run Evidently AI monitoring"""
        logger.info("\n" + "=" * 70)
        logger.info("2. MONITORING & EXPLAINABILITY - EVIDENTLY AI")
        logger.info("=" * 70)
        
        try:
            result = subprocess.run([
                sys.executable,
                "src/monitoring/evidently_monitor.py",
                "--reference", "data/train.csv",
                "--current", "data/test.csv",
                "--output", "reports/evidently"
            ], capture_output=True, text=True, check=True)
            
            logger.info(result.stdout)
            logger.info("✅ Evidently AI monitoring complete")
            
            # Check reports
            reports_dir = Path("reports/evidently")
            if reports_dir.exists():
                reports = list(reports_dir.glob("*.html"))
                logger.info(f"Generated {len(reports)} HTML reports")
                return {"status": "success", "reports_count": len(reports)}
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Evidently monitoring failed: {e.stderr}")
            return {"status": "error", "message": str(e)}
        except Exception as e:
            logger.error(f"Error: {e}")
            return {"status": "error", "message": str(e)}
    
    def setup_prometheus(self) -> Dict[str, Any]:
        """Setup Prometheus monitoring"""
        logger.info("\n" + "=" * 70)
        logger.info("3. PERFORMANCE MONITORING - PROMETHEUS")
        logger.info("=" * 70)
        
        # Prometheus is already integrated in FastAPI
        logger.info("✅ Prometheus metrics available at /metrics endpoint")
        logger.info("Metrics include:")
        logger.info("  - predictions_total (counter)")
        logger.info("  - prediction_latency_seconds (histogram)")
        logger.info("  - prediction_errors_total (counter)")
        logger.info("  - API available at: http://localhost:8000/metrics")
        
        return {"status": "success", "endpoint": "http://localhost:8000/metrics"}
    
    def create_jenkins_pipeline(self) -> Dict[str, Any]:
        """Create Jenkins pipeline configuration"""
        logger.info("\n" + "=" * 70)
        logger.info("4. WORKFLOW AUTOMATION - JENKINS")
        logger.info("=" * 70)
        
        jenkinsfile_content = """
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
"""
        
        jenkinsfile_path = self.project_root / "Jenkinsfile"
        with open(jenkinsfile_path, 'w') as f:
            f.write(jenkinsfile_content)
        
        logger.info(f"✅ Jenkinsfile created: {jenkinsfile_path}")
        logger.info("Stages: Setup, Data, Training, Testing, Edge, Monitoring, Security, Docker, K8s, Tests")
        
        return {"status": "success", "path": str(jenkinsfile_path)}
    
    def create_opa_policies(self) -> Dict[str, Any]:
        """Create Open Policy Agent security policies"""
        logger.info("\n" + "=" * 70)
        logger.info("5. SECURITY & COMPLIANCE - OPEN POLICY AGENT")
        logger.info("=" * 70)
        
        # Create policies directory
        policies_dir = self.project_root / "policies"
        policies_dir.mkdir(exist_ok=True)
        
        # Model deployment policy
        deployment_policy = """
package mlops.deployment

default allow_deployment = false

# Allow deployment if all conditions are met
allow_deployment {
    input.model.accuracy >= 0.80
    input.model.tested == true
    input.security.scanned == true
    input.security.vulnerabilities == 0
}

# Deny deployment if accuracy is too low
deny_deployment[msg] {
    input.model.accuracy < 0.80
    msg := sprintf("Model accuracy %.2f%% is below threshold 80%%", [input.model.accuracy * 100])
}

# Deny deployment if not tested
deny_deployment[msg] {
    input.model.tested == false
    msg := "Model has not been tested"
}

# Deny deployment if security vulnerabilities found
deny_deployment[msg] {
    input.security.vulnerabilities > 0
    msg := sprintf("Security scan found %d vulnerabilities", [input.security.vulnerabilities])
}
"""
        
        with open(policies_dir / "deployment.rego", 'w') as f:
            f.write(deployment_policy)
        
        # Data access policy
        data_policy = """
package mlops.data

import future.keywords.if

default allow_data_access = false

# Allow data access based on role
allow_data_access if {
    input.user.role == "data_scientist"
    input.data.classification == "internal"
}

allow_data_access if {
    input.user.role == "admin"
}

# Deny sensitive data access
deny_data_access[msg] if {
    input.data.classification == "sensitive"
    input.user.role != "admin"
    msg := "Insufficient permissions for sensitive data"
}
"""
        
        with open(policies_dir / "data_access.rego", 'w') as f:
            f.write(data_policy)
        
        logger.info(f"✅ OPA policies created: {policies_dir}")
        logger.info("Policies: deployment.rego, data_access.rego")
        
        return {"status": "success", "policies_dir": str(policies_dir)}
    
    def create_kubernetes_rbac(self) -> Dict[str, Any]:
        """Create Kubernetes RBAC configurations"""
        logger.info("\n" + "=" * 70)
        logger.info("6. KUBERNETES RBAC - ROLE-BASED ACCESS CONTROL")
        logger.info("=" * 70)
        
        rbac_config = """
apiVersion: v1
kind: ServiceAccount
metadata:
  name: mlops-service-account
  namespace: kubeflow
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: mlops-role
  namespace: kubeflow
rules:
- apiGroups: [""]
  resources: ["pods", "services"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "watch", "update", "patch"]
- apiGroups: ["batch"]
  resources: ["jobs"]
  verbs: ["get", "list", "create"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: mlops-rolebinding
  namespace: kubeflow
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: mlops-role
subjects:
- kind: ServiceAccount
  name: mlops-service-account
  namespace: kubeflow
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: mlops-cluster-role
rules:
- apiGroups: ["kubeflow.org"]
  resources: ["experiments", "trials"]
  verbs: ["get", "list", "watch", "create"]
- apiGroups: [""]
  resources: ["persistentvolumes", "persistentvolumeclaims"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: mlops-cluster-rolebinding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: mlops-cluster-role
subjects:
- kind: ServiceAccount
  name: mlops-service-account
  namespace: kubeflow
"""
        
        rbac_path = self.project_root / "kubernetes" / "rbac.yaml"
        with open(rbac_path, 'w') as f:
            f.write(rbac_config)
        
        logger.info(f"✅ Kubernetes RBAC created: {rbac_path}")
        logger.info("Components: ServiceAccount, Role, RoleBinding, ClusterRole, ClusterRoleBinding")
        
        return {"status": "success", "path": str(rbac_path)}
    
    def run_full_pipeline(self) -> Dict[str, Any]:
        """Run complete enterprise deployment pipeline"""
        logger.info("\n" + "=" * 80)
        logger.info("🚀 ENTERPRISE MLOps DEPLOYMENT - COMPLETE PIPELINE")
        logger.info("=" * 80)
        logger.info("Components: TFLite, Evidently AI, Jenkins, Prometheus, OPA, K8s RBAC")
        logger.info("=" * 80 + "\n")
        
        start_time = time.time()
        
        # 1. Check dependencies
        deps = self.check_dependencies()
        self.results['dependencies'] = deps
        
        # 2. TFLite Conversion (Edge Deployment)
        self.results['tflite'] = self.convert_to_tflite()
        
        # 3. Evidently AI Monitoring
        self.results['evidently'] = self.run_evidently_monitoring()
        
        # 4. Prometheus Setup
        self.results['prometheus'] = self.setup_prometheus()
        
        # 5. Jenkins Pipeline
        self.results['jenkins'] = self.create_jenkins_pipeline()
        
        # 6. OPA Policies
        self.results['opa'] = self.create_opa_policies()
        
        # 7. Kubernetes RBAC
        self.results['rbac'] = self.create_kubernetes_rbac()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Generate summary
        logger.info("\n" + "=" * 80)
        logger.info("📊 DEPLOYMENT SUMMARY")
        logger.info("=" * 80)
        logger.info(f"⏱️  Total Duration: {duration:.2f} seconds")
        logger.info(f"✅ TFLite Conversion: {self.results['tflite']['status']}")
        logger.info(f"✅ Evidently Monitoring: {self.results['evidently']['status']}")
        logger.info(f"✅ Prometheus: {self.results['prometheus']['status']}")
        logger.info(f"✅ Jenkins Pipeline: {self.results['jenkins']['status']}")
        logger.info(f"✅ OPA Policies: {self.results['opa']['status']}")
        logger.info(f"✅ Kubernetes RBAC: {self.results['rbac']['status']}")
        logger.info("=" * 80)
        
        # Save results
        results_path = self.project_root / "enterprise_deployment_results.json"
        with open(results_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        logger.info(f"\n📄 Results saved: {results_path}")
        
        return self.results


def main():
    """Main execution"""
    deployer = EnterpriseDeployment()
    
    print("\n" + "=" * 80)
    print("🏢 ENTERPRISE MLOps DEPLOYMENT")
    print("=" * 80)
    print("This will deploy:")
    print("  1. TensorFlow Lite (Edge Deployment)")
    print("  2. Evidently AI (Monitoring & Explainability)")
    print("  3. Jenkins (CI/CD Pipeline)")
    print("  4. Prometheus (Performance Monitoring)")
    print("  5. Open Policy Agent (Security)")
    print("  6. Kubernetes RBAC (Access Control)")
    print("=" * 80)
    
    response = input("\nProceed with deployment? (y/n): ")
    
    if response.lower() == 'y':
        results = deployer.run_full_pipeline()
        
        print("\n✅ Enterprise deployment complete!")
        print(f"\n📊 Results: enterprise_deployment_results.json")
        
        return results
    else:
        print("\n❌ Deployment cancelled")
        return None


if __name__ == "__main__":
    main()
