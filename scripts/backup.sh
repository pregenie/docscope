#!/bin/bash
# DocScope Backup Script

set -e

# Configuration
BACKUP_DIR="/backup/docscope"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="docscope_backup_${TIMESTAMP}"
RETENTION_DAYS=30

# Database configuration
DB_HOST="${DOCSCOPE_DB_HOST:-localhost}"
DB_PORT="${DOCSCOPE_DB_PORT:-5432}"
DB_NAME="${DOCSCOPE_DB_NAME:-docscope}"
DB_USER="${DOCSCOPE_DB_USER:-docscope}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

create_backup_dir() {
    log_info "Creating backup directory..."
    mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}"
}

backup_database() {
    log_info "Backing up database..."
    
    pg_dump \
        -h ${DB_HOST} \
        -p ${DB_PORT} \
        -U ${DB_USER} \
        -d ${DB_NAME} \
        -f "${BACKUP_DIR}/${BACKUP_NAME}/database.sql" \
        --verbose \
        --no-owner \
        --no-acl
    
    # Compress the dump
    gzip "${BACKUP_DIR}/${BACKUP_NAME}/database.sql"
    
    log_info "Database backup completed"
}

backup_search_index() {
    log_info "Backing up search index..."
    
    INDEX_PATH="${DOCSCOPE_SEARCH_INDEX_PATH:-/data/index}"
    
    if [ -d "${INDEX_PATH}" ]; then
        tar -czf "${BACKUP_DIR}/${BACKUP_NAME}/search_index.tar.gz" \
            -C "$(dirname ${INDEX_PATH})" \
            "$(basename ${INDEX_PATH})"
        log_info "Search index backup completed"
    else
        log_warn "Search index not found at ${INDEX_PATH}"
    fi
}

backup_documents() {
    log_info "Backing up documents..."
    
    DOCS_PATH="${DOCSCOPE_DATA_DIR:-/data/documents}"
    
    if [ -d "${DOCS_PATH}" ]; then
        tar -czf "${BACKUP_DIR}/${BACKUP_NAME}/documents.tar.gz" \
            -C "$(dirname ${DOCS_PATH})" \
            "$(basename ${DOCS_PATH})"
        log_info "Documents backup completed"
    else
        log_warn "Documents directory not found at ${DOCS_PATH}"
    fi
}

backup_config() {
    log_info "Backing up configuration..."
    
    CONFIG_PATH="${DOCSCOPE_CONFIG_DIR:-/config}"
    
    if [ -d "${CONFIG_PATH}" ]; then
        tar -czf "${BACKUP_DIR}/${BACKUP_NAME}/config.tar.gz" \
            -C "$(dirname ${CONFIG_PATH})" \
            "$(basename ${CONFIG_PATH})" \
            --exclude='*.secret' \
            --exclude='*.key'
        log_info "Configuration backup completed"
    else
        log_warn "Config directory not found at ${CONFIG_PATH}"
    fi
}

backup_plugins() {
    log_info "Backing up plugins..."
    
    PLUGINS_PATH="${DOCSCOPE_PLUGINS_DIR:-/data/plugins}"
    
    if [ -d "${PLUGINS_PATH}" ]; then
        tar -czf "${BACKUP_DIR}/${BACKUP_NAME}/plugins.tar.gz" \
            -C "$(dirname ${PLUGINS_PATH})" \
            "$(basename ${PLUGINS_PATH})"
        log_info "Plugins backup completed"
    else
        log_warn "Plugins directory not found at ${PLUGINS_PATH}"
    fi
}

create_manifest() {
    log_info "Creating backup manifest..."
    
    cat > "${BACKUP_DIR}/${BACKUP_NAME}/manifest.json" <<EOF
{
    "timestamp": "${TIMESTAMP}",
    "version": "$(cat /app/VERSION 2>/dev/null || echo 'unknown')",
    "components": [
        "database",
        "search_index",
        "documents",
        "config",
        "plugins"
    ],
    "retention_days": ${RETENTION_DAYS}
}
EOF
}

compress_backup() {
    log_info "Compressing backup..."
    
    cd "${BACKUP_DIR}"
    tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}/"
    
    # Remove uncompressed directory
    rm -rf "${BACKUP_NAME}/"
    
    # Calculate size
    SIZE=$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)
    log_info "Backup size: ${SIZE}"
}

cleanup_old_backups() {
    log_info "Cleaning up old backups..."
    
    find "${BACKUP_DIR}" \
        -name "docscope_backup_*.tar.gz" \
        -type f \
        -mtime +${RETENTION_DAYS} \
        -delete
    
    log_info "Removed backups older than ${RETENTION_DAYS} days"
}

upload_to_s3() {
    if [ ! -z "${S3_BUCKET}" ]; then
        log_info "Uploading to S3..."
        aws s3 cp \
            "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" \
            "s3://${S3_BUCKET}/backups/${BACKUP_NAME}.tar.gz"
        log_info "Upload completed"
    fi
}

send_notification() {
    if [ ! -z "${SLACK_WEBHOOK_URL}" ]; then
        log_info "Sending notification..."
        
        curl -X POST "${SLACK_WEBHOOK_URL}" \
            -H 'Content-Type: application/json' \
            -d "{
                \"text\": \"DocScope backup completed\",
                \"attachments\": [{
                    \"color\": \"good\",
                    \"fields\": [
                        {\"title\": \"Backup Name\", \"value\": \"${BACKUP_NAME}\", \"short\": true},
                        {\"title\": \"Size\", \"value\": \"${SIZE}\", \"short\": true}
                    ]
                }]
            }"
    fi
}

# Main execution
main() {
    log_info "Starting DocScope backup..."
    
    create_backup_dir
    backup_database
    backup_search_index
    backup_documents
    backup_config
    backup_plugins
    create_manifest
    compress_backup
    cleanup_old_backups
    upload_to_s3
    send_notification
    
    log_info "Backup completed successfully!"
    log_info "Backup saved to: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
}

# Run if not sourced
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi