#!/usr/bin/env python3
"""
Build and Deploy Script for MLOps Project
Automates Docker builds, Kubernetes deployments, and BentoML packaging
"""

import os
import sys
import subprocess
import argparse
import logging
from pathlib import Path
from typing import List, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DeploymentManager:
    """Manages deployment workflows"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.k8s_dir = self.project_root / "kubernetes"
        
    def run_command(self, cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run shell command"""
        logger.info(f"Running: {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=check,
                cwd=self.project_root
            )
            if result.stdout:
                logger.info(result.stdout)
            if result.stderr:
                logger.warning(result.stderr)
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {e}")
            if e.stdout:
                logger.error(f"Stdout: {e.stdout}")
            if e.stderr:
                logger.error(f"Stderr: {e.stderr}")
            raise
    
    def docker_build(self, image_name: str, dockerfile: str = "Dockerfile", tag: str = "latest"):
        """Build Docker image"""
        logger.info(f"Building Docker image: {image_name}:{tag}")
        
        cmd = [
            "docker", "build",
            "-f", dockerfile,
            "-t", f"{image_name}:{tag}",
            "."
        ]
        
        self.run_command(cmd)
        logger.info(f"✓ Image built: {image_name}:{tag}")
    
    def docker_push(self, image_name: str, tag: str = "latest", registry: Optional[str] = None):
        """Push Docker image to registry"""
        if registry:
            full_name = f"{registry}/{image_name}:{tag}"
            # Tag for registry
            self.run_command(["docker", "tag", f"{image_name}:{tag}", full_name])
            image_name = full_name
        else:
            full_name = f"{image_name}:{tag}"
        
        logger.info(f"Pushing image: {full_name}")
        self.run_command(["docker", "push", full_name])
        logger.info(f"✓ Image pushed: {full_name}")
    
    def build_all_images(self, push: bool = False, registry: Optional[str] = None):
        """Build all Docker images"""
        images = [
            ("mlops-predictive-maintenance", "Dockerfile"),
            ("mlops-api", "Dockerfile.api"),
            ("mlops-mlflow", "Dockerfile.mlflow"),
        ]
        
        for image_name, dockerfile in images:
            self.docker_build(image_name, dockerfile)
            if push:
                self.docker_push(image_name, registry=registry)
        
        logger.info("✓ All images built successfully")
    
    def k8s_apply(self, manifest: str):
        """Apply Kubernetes manifest"""
        manifest_path = self.k8s_dir / manifest
        
        if not manifest_path.exists():
            logger.error(f"Manifest not found: {manifest_path}")
            return False
        
        logger.info(f"Applying: {manifest}")
        self.run_command(["kubectl", "apply", "-f", str(manifest_path)])
        logger.info(f"✓ Applied: {manifest}")
        return True
    
    def k8s_delete(self, manifest: str):
        """Delete Kubernetes resources"""
        manifest_path = self.k8s_dir / manifest
        
        if not manifest_path.exists():
            logger.error(f"Manifest not found: {manifest_path}")
            return False
        
        logger.info(f"Deleting: {manifest}")
        self.run_command(["kubectl", "delete", "-f", str(manifest_path)])
        logger.info(f"✓ Deleted: {manifest}")
        return True
    
    def deploy_kubernetes(self):
        """Deploy all Kubernetes resources"""
        manifests = [
            "namespace.yaml",
            "persistent-volumes.yaml",
            "mlflow-deployment.yaml",
            "api-deployment.yaml",
            "katib-experiment.yaml"
        ]
        
        for manifest in manifests:
            self.k8s_apply(manifest)
        
        logger.info("✓ Kubernetes deployment complete")
        self.show_k8s_status()
    
    def show_k8s_status(self):
        """Show Kubernetes resource status"""
        logger.info("\n" + "="*60)
        logger.info("Kubernetes Status")
        logger.info("="*60)
        
        commands = [
            (["kubectl", "get", "pods", "-n", "kubeflow"], "Pods"),
            (["kubectl", "get", "svc", "-n", "kubeflow"], "Services"),
            (["kubectl", "get", "experiments", "-n", "kubeflow"], "Katib Experiments"),
        ]
        
        for cmd, title in commands:
            logger.info(f"\n{title}:")
            self.run_command(cmd, check=False)
    
    def save_model_to_bentoml(self):
        """Save model to BentoML store"""
        logger.info("Saving model to BentoML...")
        self.run_command([
            sys.executable,
            "src/deployment/bentoml_save.py",
            "--production"
        ])
        logger.info("✓ Model saved to BentoML")
    
    def build_bento(self):
        """Build BentoML package"""
        logger.info("Building Bento...")
        self.run_command(["bentoml", "build"])
        logger.info("✓ Bento built successfully")
        
        # List bentos
        logger.info("\nAvailable Bentos:")
        self.run_command(["bentoml", "list"])
    
    def containerize_bento(self, tag: str = "latest"):
        """Containerize BentoML service"""
        logger.info("Containerizing Bento...")
        
        # Get latest bento
        result = self.run_command(["bentoml", "list", "--output", "json"])
        # Parse and get latest
        
        self.run_command([
            "bentoml", "containerize",
            "predictive_maintenance:latest",
            "-t", f"mlops-bento:{tag}"
        ])
        logger.info(f"✓ Bento containerized: mlops-bento:{tag}")
    
    def serve_bento_local(self):
        """Serve BentoML locally"""
        logger.info("Starting BentoML server...")
        logger.info("Access at: http://localhost:3000")
        self.run_command([
            "bentoml", "serve",
            "predictive_maintenance:latest",
            "--production"
        ])
    
    def test_api(self, url: str = "http://localhost:8000"):
        """Test API endpoints"""
        logger.info(f"Testing API at {url}")
        
        tests = [
            (f"{url}/health", "Health Check"),
            (f"{url}/model/info", "Model Info"),
        ]
        
        for endpoint, name in tests:
            logger.info(f"\nTesting {name}: {endpoint}")
            try:
                import requests
                response = requests.get(endpoint, timeout=5)
                logger.info(f"Status: {response.status_code}")
                logger.info(f"Response: {response.json()}")
            except Exception as e:
                logger.error(f"Test failed: {e}")
    
    def cleanup(self):
        """Clean up deployments"""
        logger.info("Cleaning up Kubernetes resources...")
        
        manifests = [
            "katib-experiment.yaml",
            "api-deployment.yaml",
            "mlflow-deployment.yaml",
            "persistent-volumes.yaml",
        ]
        
        for manifest in manifests:
            self.k8s_delete(manifest)
        
        logger.info("✓ Cleanup complete")

def main():
    parser = argparse.ArgumentParser(description="MLOps Deployment Manager")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Docker build
    docker_parser = subparsers.add_parser("docker", help="Build Docker images")
    docker_parser.add_argument("--push", action="store_true", help="Push images to registry")
    docker_parser.add_argument("--registry", type=str, help="Docker registry URL")
    
    # Kubernetes deploy
    k8s_parser = subparsers.add_parser("k8s", help="Deploy to Kubernetes")
    k8s_parser.add_argument("--cleanup", action="store_true", help="Clean up resources")
    
    # BentoML
    bento_parser = subparsers.add_parser("bento", help="BentoML operations")
    bento_parser.add_argument("--save", action="store_true", help="Save model to BentoML")
    bento_parser.add_argument("--build", action="store_true", help="Build Bento")
    bento_parser.add_argument("--containerize", action="store_true", help="Containerize Bento")
    bento_parser.add_argument("--serve", action="store_true", help="Serve Bento locally")
    
    # Test
    test_parser = subparsers.add_parser("test", help="Test API")
    test_parser.add_argument("--url", type=str, default="http://localhost:8000", help="API URL")
    
    # Full deployment
    full_parser = subparsers.add_parser("full", help="Full deployment workflow")
    full_parser.add_argument("--skip-docker", action="store_true", help="Skip Docker build")
    full_parser.add_argument("--skip-k8s", action="store_true", help="Skip Kubernetes deploy")
    
    args = parser.parse_args()
    
    manager = DeploymentManager()
    
    try:
        if args.command == "docker":
            manager.build_all_images(push=args.push, registry=args.registry)
        
        elif args.command == "k8s":
            if args.cleanup:
                manager.cleanup()
            else:
                manager.deploy_kubernetes()
        
        elif args.command == "bento":
            if args.save:
                manager.save_model_to_bentoml()
            if args.build:
                manager.build_bento()
            if args.containerize:
                manager.containerize_bento()
            if args.serve:
                manager.serve_bento_local()
        
        elif args.command == "test":
            manager.test_api(url=args.url)
        
        elif args.command == "full":
            logger.info("Starting full deployment workflow...")
            
            if not args.skip_docker:
                manager.build_all_images()
            
            if not args.skip_k8s:
                manager.deploy_kubernetes()
            
            logger.info("\n" + "="*60)
            logger.info("✓ Full deployment complete!")
            logger.info("="*60)
        
        else:
            parser.print_help()
    
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
