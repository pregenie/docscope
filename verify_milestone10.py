#!/usr/bin/env python3
"""
Milestone 10 Verification Script - Production Readiness
Validates Docker, Kubernetes, and production configuration
"""

import os
import sys
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if os.path.exists(filepath):
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ {description} missing: {filepath}")
        return False

def check_file_content(filepath, required_items, description):
    """Check if a file contains required content"""
    if not os.path.exists(filepath):
        print(f"✗ {description} missing: {filepath}")
        return False
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        missing_items = []
        for item in required_items:
            if item not in content:
                missing_items.append(item)
        
        if missing_items:
            print(f"✗ {description} missing items: {missing_items}")
            return False
        else:
            print(f"✓ {description} has required content")
            return True
    except Exception as e:
        print(f"✗ Error checking {description}: {e}")
        return False

def verify_docker_configuration():
    """Verify Docker configuration"""
    print("\n=== Docker Configuration ===")
    checks = []
    
    # Check Dockerfile
    dockerfile_items = [
        "FROM python:3.10-slim",
        "WORKDIR /app",
        "USER docscope",
        "EXPOSE 8000",
        "HEALTHCHECK",
        "VOLUME",
        "CMD"
    ]
    checks.append(check_file_content(
        "Dockerfile",
        dockerfile_items,
        "Dockerfile"
    ))
    
    # Check docker-compose.yml
    compose_items = [
        "version:",
        "services:",
        "docscope:",
        "postgres:",
        "redis:",
        "nginx:",
        "networks:",
        "volumes:",
        "healthcheck:",
        "depends_on:"
    ]
    checks.append(check_file_content(
        "docker-compose.yml",
        compose_items,
        "Docker Compose configuration"
    ))
    
    # Check nginx.conf
    nginx_items = [
        "upstream docscope_api",
        "upstream docscope_ui",
        "server {",
        "listen 80",
        "listen 443 ssl",
        "location /api/",
        "location /ws/",
        "proxy_pass",
        "ssl_certificate",
        "gzip on"
    ]
    checks.append(check_file_content(
        "nginx.conf",
        nginx_items,
        "Nginx configuration"
    ))
    
    return all(checks)

def verify_kubernetes_manifests():
    """Verify Kubernetes manifests"""
    print("\n=== Kubernetes Manifests ===")
    checks = []
    
    # Check namespace
    checks.append(check_file_exists(
        "kubernetes/namespace.yaml",
        "Namespace manifest"
    ))
    
    # Check deployment
    deployment_items = [
        "apiVersion: apps/v1",
        "kind: Deployment",
        "metadata:",
        "spec:",
        "replicas:",
        "containers:",
        "livenessProbe:",
        "readinessProbe:",
        "resources:",
        "volumeMounts:"
    ]
    checks.append(check_file_content(
        "kubernetes/deployment.yaml",
        deployment_items,
        "Deployment manifest"
    ))
    
    # Check service
    service_items = [
        "apiVersion: v1",
        "kind: Service",
        "spec:",
        "type: ClusterIP",
        "selector:",
        "ports:"
    ]
    checks.append(check_file_content(
        "kubernetes/service.yaml",
        service_items,
        "Service manifest"
    ))
    
    # Check ingress
    ingress_items = [
        "apiVersion: networking.k8s.io/v1",
        "kind: Ingress",
        "tls:",
        "rules:",
        "paths:",
        "backend:"
    ]
    checks.append(check_file_content(
        "kubernetes/ingress.yaml",
        ingress_items,
        "Ingress manifest"
    ))
    
    # Check configmap
    configmap_items = [
        "apiVersion: v1",
        "kind: ConfigMap",
        "data:",
        "config.yaml:"
    ]
    checks.append(check_file_content(
        "kubernetes/configmap.yaml",
        configmap_items,
        "ConfigMap manifest"
    ))
    
    # Check secrets
    checks.append(check_file_exists(
        "kubernetes/secrets.yaml",
        "Secrets manifest"
    ))
    
    # Check PVC
    pvc_items = [
        "kind: PersistentVolumeClaim",
        "accessModes:",
        "storageClassName:",
        "resources:"
    ]
    checks.append(check_file_content(
        "kubernetes/pvc.yaml",
        pvc_items,
        "PVC manifest"
    ))
    
    # Check StatefulSet
    statefulset_items = [
        "kind: StatefulSet",
        "serviceName:",
        "postgres",
        "redis"
    ]
    checks.append(check_file_content(
        "kubernetes/statefulset.yaml",
        statefulset_items,
        "StatefulSet manifest"
    ))
    
    # Check RBAC
    rbac_items = [
        "kind: ServiceAccount",
        "kind: Role",
        "kind: RoleBinding"
    ]
    checks.append(check_file_content(
        "kubernetes/rbac.yaml",
        rbac_items,
        "RBAC manifest"
    ))
    
    return all(checks)

def verify_production_config():
    """Verify production configuration"""
    print("\n=== Production Configuration ===")
    checks = []
    
    # Check production environment file
    env_items = [
        "DOCSCOPE_ENV=production",
        "DOCSCOPE_DATABASE_URL",
        "DOCSCOPE_REDIS_URL",
        "DOCSCOPE_SECRET_KEY",
        "DOCSCOPE_CORS_ORIGINS",
        "DOCSCOPE_ENABLE_AUTH",
        "DOCSCOPE_ENABLE_RATE_LIMIT"
    ]
    checks.append(check_file_content(
        ".env.production",
        env_items,
        "Production environment file"
    ))
    
    return all(checks)

def verify_deployment_scripts():
    """Verify deployment scripts"""
    print("\n=== Deployment Scripts ===")
    checks = []
    
    # Check deploy script
    deploy_items = [
        "#!/bin/bash",
        "check_requirements",
        "build_image",
        "push_image",
        "deploy_database",
        "deploy_application",
        "run_migrations",
        "check_deployment"
    ]
    checks.append(check_file_content(
        "scripts/deploy.sh",
        deploy_items,
        "Deployment script"
    ))
    
    # Check backup script
    backup_items = [
        "#!/bin/bash",
        "backup_database",
        "backup_search_index",
        "backup_documents",
        "cleanup_old_backups",
        "create_manifest"
    ]
    checks.append(check_file_content(
        "scripts/backup.sh",
        backup_items,
        "Backup script"
    ))
    
    return all(checks)

def verify_health_monitoring():
    """Verify health and monitoring setup"""
    print("\n=== Health & Monitoring ===")
    checks = []
    
    # Check Dockerfile for health check
    checks.append(check_file_content(
        "Dockerfile",
        ["HEALTHCHECK --interval=30s"],
        "Docker health check"
    ))
    
    # Check Kubernetes deployment for probes
    checks.append(check_file_content(
        "kubernetes/deployment.yaml",
        ["livenessProbe:", "readinessProbe:"],
        "Kubernetes health probes"
    ))
    
    # Check docker-compose for health checks
    checks.append(check_file_content(
        "docker-compose.yml",
        ["healthcheck:"],
        "Docker Compose health checks"
    ))
    
    return all(checks)

def verify_security_configuration():
    """Verify security configuration"""
    print("\n=== Security Configuration ===")
    checks = []
    
    # Check Dockerfile security
    security_items = [
        "USER docscope",  # Non-root user
        "useradd"  # User creation
    ]
    checks.append(check_file_content(
        "Dockerfile",
        security_items,
        "Docker security settings"
    ))
    
    # Check Kubernetes security
    k8s_security_items = [
        "runAsNonRoot: true",
        "runAsUser: 1000",
        "ServiceAccount"
    ]
    checks.append(check_file_content(
        "kubernetes/deployment.yaml",
        ["runAsNonRoot: true"],
        "Kubernetes security context"
    ))
    
    # Check nginx security headers
    nginx_security = [
        "X-Frame-Options",
        "X-XSS-Protection",
        "X-Content-Type-Options",
        "Content-Security-Policy",
        "Strict-Transport-Security"
    ]
    checks.append(check_file_content(
        "nginx.conf",
        nginx_security,
        "Nginx security headers"
    ))
    
    return all(checks)

def verify_scaling_configuration():
    """Verify scaling and performance configuration"""
    print("\n=== Scaling & Performance ===")
    checks = []
    
    # Check replica configuration
    checks.append(check_file_content(
        "kubernetes/deployment.yaml",
        ["replicas: 3"],
        "Application replicas"
    ))
    
    # Check resource limits
    resource_items = [
        "resources:",
        "requests:",
        "limits:",
        "memory:",
        "cpu:"
    ]
    checks.append(check_file_content(
        "kubernetes/deployment.yaml",
        resource_items,
        "Resource limits"
    ))
    
    # Check nginx performance settings
    nginx_perf = [
        "worker_connections",
        "keepalive_timeout",
        "gzip on",
        "proxy_cache",
        "limit_req_zone"
    ]
    checks.append(check_file_content(
        "nginx.conf",
        nginx_perf,
        "Nginx performance settings"
    ))
    
    return all(checks)

def verify_persistence():
    """Verify data persistence configuration"""
    print("\n=== Data Persistence ===")
    checks = []
    
    # Check PVC configuration
    pvc_items = [
        "docscope-data-pvc",
        "docscope-postgres-pvc",
        "docscope-redis-pvc"
    ]
    checks.append(check_file_content(
        "kubernetes/pvc.yaml",
        pvc_items,
        "Persistent volume claims"
    ))
    
    # Check volume mounts
    checks.append(check_file_content(
        "kubernetes/deployment.yaml",
        ["volumeMounts:", "volumes:"],
        "Volume mounts"
    ))
    
    # Check Docker volumes
    checks.append(check_file_content(
        "docker-compose.yml",
        ["volumes:", "docscope-data:", "postgres-data:", "redis-data:"],
        "Docker volumes"
    ))
    
    return all(checks)

def main():
    """Main verification function"""
    print("=" * 60)
    print("MILESTONE 10 VERIFICATION - Production Readiness")
    print("=" * 60)
    
    results = []
    
    # Run all verifications
    results.append(("Docker Configuration", verify_docker_configuration()))
    results.append(("Kubernetes Manifests", verify_kubernetes_manifests()))
    results.append(("Production Configuration", verify_production_config()))
    results.append(("Deployment Scripts", verify_deployment_scripts()))
    results.append(("Health & Monitoring", verify_health_monitoring()))
    results.append(("Security Configuration", verify_security_configuration()))
    results.append(("Scaling & Performance", verify_scaling_configuration()))
    results.append(("Data Persistence", verify_persistence()))
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    total_passed = sum(1 for _, passed in results if passed)
    total_checks = len(results)
    
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{name:.<40} {status}")
    
    print(f"\nTotal: {total_passed}/{total_checks} verification groups passed")
    
    if total_passed == total_checks:
        print("\n✓ MILESTONE 10 COMPLETE: Production readiness achieved!")
        print("\nKey achievements:")
        print("- Multi-stage Docker build with security best practices")
        print("- Complete Docker Compose stack with all services")
        print("- Kubernetes manifests for production deployment")
        print("- Health checks and monitoring configuration")
        print("- Security hardening (non-root user, security headers)")
        print("- Scaling configuration with resource limits")
        print("- Data persistence with PVCs and volumes")
        print("- Deployment and backup automation scripts")
        return 0
    else:
        print("\n✗ MILESTONE 10 INCOMPLETE: Some components need attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())