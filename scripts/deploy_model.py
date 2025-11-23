#!/usr/bin/env python
"""
Deploy trained models to production.

Supports deployment to:
- Local Flask API server
- Docker container
- Cloud platforms (AWS, GCP, Azure)
- Model registry (MLflow, BentoML)

Usage:
    python scripts/deploy_model.py --local
    python scripts/deploy_model.py --docker --tag v1.0
    python scripts/deploy_model.py --validate --model lineup_optimizer
"""

import argparse
import logging
from pathlib import Path
from typing import Dict, Optional, List
import json
import pickle
import shutil
from datetime import datetime
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/deploy_model.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ModelDeployer:
    """Deploy trained models to production."""
    
    def __init__(
        self,
        model_dir: Path = Path('models'),
        deployment_dir: Path = Path('deployment')
    ):
        """
        Initialize deployer.
        
        Args:
            model_dir: Directory containing trained models
            deployment_dir: Deployment staging directory
        """
        self.model_dir = model_dir
        self.deployment_dir = deployment_dir
        self.deployment_dir.mkdir(parents=True, exist_ok=True)
    
    def validate_models(self) -> Dict[str, bool]:
        """
        Validate all trained models exist and are loadable.
        
        Returns:
            Dictionary mapping model names to validation status
        """
        logger.info("Validating models...")
        
        validation_results = {}
        required_models = ['lineup_optimizer', 'in_game_decider', 'pitching_manager']
        
        for model_name in required_models:
            model_path = self.model_dir / f'{model_name}_latest.pkl'
            scaler_path = self.model_dir / f'{model_name}_scaler_latest.pkl'
            
            try:
                # Check model file exists
                if not model_path.exists():
                    logger.error(f"Model file missing: {model_path}")
                    validation_results[model_name] = False
                    continue
                
                # Try loading model
                with open(model_path, 'rb') as f:
                    model = pickle.load(f)
                
                # Try loading scaler
                if scaler_path.exists():
                    with open(scaler_path, 'rb') as f:
                        scaler = pickle.load(f)
                    logger.info(f"✓ {model_name}: valid (model + scaler)")
                else:
                    logger.warning(f"⚠ {model_name}: valid model, missing scaler")
                
                validation_results[model_name] = True
            
            except Exception as e:
                logger.error(f"✗ {model_name}: {e}")
                validation_results[model_name] = False
        
        return validation_results
    
    def create_deployment_package(
        self,
        version: str = 'latest',
        include_docs: bool = True
    ) -> Path:
        """
        Create deployment package with all necessary files.
        
        Args:
            version: Version tag
            include_docs: Include documentation
        
        Returns:
            Path to deployment package
        """
        logger.info(f"Creating deployment package (version: {version})...")
        
        # Create versioned deployment directory
        package_dir = self.deployment_dir / f'baseball_manager_ai_{version}'
        
        if package_dir.exists():
            shutil.rmtree(package_dir)
        
        package_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        models_dir = package_dir / 'models'
        models_dir.mkdir(parents=True, exist_ok=True)
        
        config_dir = package_dir / 'config'
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy models
        logger.info("Copying models...")
        for model_file in self.model_dir.glob('*_latest.pkl'):
            shutil.copy(model_file, models_dir / model_file.name)
            logger.info(f"  ✓ {model_file.name}")
        
        for scaler_file in self.model_dir.glob('*_scaler_latest.pkl'):
            shutil.copy(scaler_file, models_dir / scaler_file.name)
            logger.info(f"  ✓ {scaler_file.name}")
        
        # Copy feature names
        features_file = self.model_dir / 'feature_names_latest.json'
        if features_file.exists():
            shutil.copy(features_file, models_dir / features_file.name)
            logger.info(f"  ✓ {features_file.name}")
        
        # Copy configurations
        logger.info("Copying configuration files...")
        for config_file in Path('config').glob('*.yaml'):
            shutil.copy(config_file, config_dir / config_file.name)
            logger.info(f"  ✓ {config_file.name}")
        
        # Create manifest
        manifest = {
            'version': version,
            'timestamp': datetime.now().isoformat(),
            'models': [f.stem for f in models_dir.glob('*_latest.pkl')],
            'configuration': list(config_dir.glob('*.yaml'))
        }
        
        manifest_path = package_dir / 'MANIFEST.json'
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"✓ Deployment package created: {package_dir}")
        
        return package_dir
    
    def generate_docker_files(self, package_dir: Path) -> None:
        """
        Generate Docker files for containerization.
        
        Args:
            package_dir: Deployment package directory
        """
        logger.info("Generating Docker files...")
        
        # Dockerfile
        dockerfile_content = '''FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create necessary directories
RUN mkdir -p logs cache

# Expose API port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "import requests; requests.get('http://localhost:5000/health')"

# Run API server
CMD ["python", "-m", "baseball_manager_ai.api.model_server"]
'''
        
        dockerfile_path = package_dir / 'Dockerfile'
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)
        logger.info(f"  ✓ Dockerfile")
        
        # .dockerignore
        dockerignore_content = '''__pycache__/
*.pyc
.git/
.gitignore
.env
logs/
cache/
*.log
.DS_Store
'''
        
        dockerignore_path = package_dir / '.dockerignore'
        with open(dockerignore_path, 'w') as f:
            f.write(dockerignore_content)
        logger.info(f"  ✓ .dockerignore")
        
        # docker-compose.yml
        compose_content = '''version: '3.8'

services:
  baseball-manager-api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: baseball-manager-api
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - MODEL_DIR=/app/models
    volumes:
      - ./logs:/app/logs
      - ./cache:/app/cache
    restart: unless-stopped
'''
        
        compose_path = package_dir / 'docker-compose.yml'
        with open(compose_path, 'w') as f:
            f.write(compose_content)
        logger.info(f"  ✓ docker-compose.yml")
    
    def build_docker_image(
        self,
        package_dir: Path,
        tag: str = 'latest'
    ) -> bool:
        """
        Build Docker image from deployment package.
        
        Args:
            package_dir: Deployment package directory
            tag: Docker image tag
        
        Returns:
            Success status
        """
        logger.info(f"Building Docker image: baseball-manager-ai:{tag}")
        
        try:
            result = subprocess.run(
                ['docker', 'build', '-t', f'baseball-manager-ai:{tag}', str(package_dir)],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                logger.info(f"✓ Docker image built successfully")
                return True
            else:
                logger.error(f"✗ Docker build failed: {result.stderr}")
                return False
        
        except Exception as e:
            logger.error(f"✗ Failed to build Docker image: {e}")
            return False
    
    def generate_api_config(self, package_dir: Path) -> None:
        """
        Generate API configuration file.
        
        Args:
            package_dir: Deployment package directory
        """
        logger.info("Generating API configuration...")
        
        api_config = {
            'version': '0.1.0',
            'title': 'Baseball Manager AI API',
            'description': 'AI-powered baseball manager decision assistant',
            'models': {
                'lineup_optimizer': {
                    'path': 'models/lineup_optimizer_latest.pkl',
                    'scaler_path': 'models/lineup_optimizer_scaler_latest.pkl',
                    'description': 'Optimizes batting order'
                },
                'in_game_decider': {
                    'path': 'models/in_game_decider_latest.pkl',
                    'scaler_path': 'models/in_game_decider_scaler_latest.pkl',
                    'description': 'Makes in-game tactical decisions'
                },
                'pitching_manager': {
                    'path': 'models/pitching_manager_latest.pkl',
                    'scaler_path': 'models/pitching_manager_scaler_latest.pkl',
                    'description': 'Manages pitcher changes and rotation'
                }
            },
            'api_endpoints': {
                '/health': 'Health check',
                '/predict/lineup': 'Get lineup recommendation',
                '/predict/decision': 'Get in-game decision recommendation',
                '/predict/pitching': 'Get pitching decision recommendation',
                '/simulate': 'Run game simulation'
            }
        }
        
        config_path = package_dir / 'API_CONFIG.json'
        with open(config_path, 'w') as f:
            json.dump(api_config, f, indent=2)
        
        logger.info(f"  ✓ API configuration: {config_path}")
    
    def create_deployment_checklist(self, package_dir: Path) -> None:
        """
        Create deployment checklist document.
        
        Args:
            package_dir: Deployment package directory
        """
        logger.info("Creating deployment checklist...")
        
        checklist = """# Deployment Checklist

## Pre-Deployment
- [ ] Models validated and tested
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] Configuration files updated
- [ ] Documentation current
- [ ] Version number updated

## Docker Deployment
- [ ] Docker image builds successfully
- [ ] Container starts without errors
- [ ] Health check endpoint responds
- [ ] API endpoints accessible
- [ ] Model inference working

## Cloud Deployment
- [ ] Cloud credentials configured
- [ ] Registry/repository created
- [ ] Image pushed to registry
- [ ] Cloud resources provisioned
- [ ] Environment variables set
- [ ] Monitoring configured

## Post-Deployment
- [ ] Verify API availability
- [ ] Test model predictions
- [ ] Monitor resource usage
- [ ] Check error logs
- [ ] Document any issues
- [ ] Schedule follow-up review

## Rollback Plan
- [ ] Keep previous version available
- [ ] Document rollback procedure
- [ ] Test rollback process
- [ ] Set rollback trigger criteria

## Monitoring
- [ ] API response time tracking
- [ ] Error rate monitoring
- [ ] Model prediction latency
- [ ] Resource utilization tracking
- [ ] Alert configuration complete
"""
        
        checklist_path = package_dir / 'DEPLOYMENT_CHECKLIST.md'
        with open(checklist_path, 'w') as f:
            f.write(checklist)
        
        logger.info(f"  ✓ Deployment checklist: {checklist_path}")
    
    def generate_readme(self, package_dir: Path) -> None:
        """
        Generate deployment README.
        
        Args:
            package_dir: Deployment package directory
        """
        logger.info("Generating README...")
        
        readme = """# Baseball Manager AI - Deployment Package

## Contents

- `models/` - Trained ML models and scalers
- `config/` - Configuration files
- `Dockerfile` - Container definition
- `docker-compose.yml` - Compose orchestration
- `MANIFEST.json` - Package contents
- `API_CONFIG.json` - API configuration
- `DEPLOYMENT_CHECKLIST.md` - Pre-deployment checks

## Quick Start

### Local Deployment
```bash
python -m baseball_manager_ai.api.model_server
```

### Docker Deployment
```bash
docker build -t baseball-manager-ai .
docker run -p 5000:5000 baseball-manager-ai
```

### Docker Compose
```bash
docker-compose up -d
```

## API Endpoints

- `GET /health` - Health check
- `POST /predict/lineup` - Lineup recommendation
- `POST /predict/decision` - In-game decision
- `POST /predict/pitching` - Pitching decision
- `POST /simulate` - Run simulation

## Configuration

Edit `config/` files to customize:
- Model hyperparameters
- API settings
- Logging configuration
- Data paths

## Monitoring

Check logs:
```bash
tail -f logs/api.log
```

## Support

For issues or questions, refer to main project documentation.
"""
        
        readme_path = package_dir / 'README.md'
        with open(readme_path, 'w') as f:
            f.write(readme)
        
        logger.info(f"  ✓ README: {readme_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Deploy trained models to production'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate models only'
    )
    
    parser.add_argument(
        '--package',
        action='store_true',
        help='Create deployment package'
    )
    
    parser.add_argument(
        '--docker',
        action='store_true',
        help='Generate Docker files and build image'
    )
    
    parser.add_argument(
        '--local',
        action='store_true',
        help='Deploy locally (start API server)'
    )
    
    parser.add_argument(
        '--model-dir',
        type=Path,
        default=Path('models'),
        help='Trained models directory'
    )
    
    parser.add_argument(
        '--deployment-dir',
        type=Path,
        default=Path('deployment'),
        help='Deployment staging directory'
    )
    
    parser.add_argument(
        '--tag',
        default='latest',
        help='Deployment/Docker tag'
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("BASEBALL MANAGER AI - MODEL DEPLOYER")
    logger.info("=" * 60)
    
    deployer = ModelDeployer(
        model_dir=args.model_dir,
        deployment_dir=args.deployment_dir
    )
    
    # Validate models
    logger.info("\n[1] Validating models...")
    validation_results = deployer.validate_models()
    
    all_valid = all(validation_results.values())
    if not all_valid:
        logger.error("Model validation failed!")
        for model, valid in validation_results.items():
            status = "✓" if valid else "✗"
            logger.info(f"  {status} {model}")
        return
    
    logger.info("✓ All models valid")
    
    if args.validate:
        logger.info("Validation mode - exiting")
        return
    
    # Create deployment package
    logger.info("\n[2] Creating deployment package...")
    package_dir = deployer.create_deployment_package(version=args.tag)
    
    # Generate configurations
    logger.info("\n[3] Generating deployment files...")
    deployer.generate_api_config(package_dir)
    deployer.create_deployment_checklist(package_dir)
    deployer.generate_readme(package_dir)
    
    # Docker deployment
    if args.docker or args.package:
        logger.info("\n[4] Generating Docker files...")
        deployer.generate_docker_files(package_dir)
        
        if args.docker:
            logger.info("\n[5] Building Docker image...")
            success = deployer.build_docker_image(package_dir, tag=args.tag)
            
            if success:
                logger.info(f"✓ Ready to deploy with: docker run -p 5000:5000 baseball-manager-ai:{args.tag}")
            else:
                logger.error("Docker build failed")
    
    # Local deployment
    if args.local:
        logger.info("\n[5] Starting local API server...")
        logger.info("Run: python -m baseball_manager_ai.api.model_server")
    
    logger.info("\n" + "=" * 60)
    logger.info("Deployment preparation complete!")
    logger.info(f"Package location: {package_dir}")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
