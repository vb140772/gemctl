# Agentspace CLI - Complete Guide

A powerful CLI tool for managing Google Gemini Enterprise (formerly Google Cloud Agentspace) resources with a gcloud-style interface.

## Why This Tool Exists

Google Gemini Enterprise (formerly Google Cloud Agentspace) is a powerful AI platform for building search and conversational applications, but it lacks an official command-line interface. This CLI fills that gap by providing:

- **gcloud-style commands** for familiar developer experience
- **Complete resource management** (engines, data stores, documents)
- **Multiple authentication methods** (user credentials + service accounts)
- **Regional endpoint support** (global, us, eu)
- **Rich output formats** (table, JSON, YAML)
- **Automation-friendly** with comprehensive scripting support

## How It Works

The CLI uses the Google Cloud Discovery Engine REST API to interact with Agentspace resources. It supports two authentication methods:

1. **User Credentials** (default): Uses `gcloud auth print-access-token` for interactive use
2. **Service Account**: Uses Application Default Credentials (ADC) for automation

The tool automatically handles regional endpoints based on the `--location` parameter and provides comprehensive help at every command level.

## gemctl Wrapper

For users who want a simple `gemctl.sh` command without installing the full package, a wrapper script is available:

```bash
# Use gemctl.sh commands
gemctl.sh engines list
gemctl.sh engines describe ENGINE_ID
gemctl.sh data-stores list
```

This provides a simple way to use the CLI without installing it as a Python package.

## Table of Contents

- [Quick Reference](#quick-reference)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Command Reference](#command-reference)
- [Authentication](#authentication)
- [Usage Examples](#usage-examples)
- [Deployment Guide](#deployment-guide)
- [Migration Guide](#migration-guide)
- [Troubleshooting](#troubleshooting)
- [Advanced Topics](#advanced-topics)

---

## Quick Reference

### Basic Commands

```bash
# After installation, you can run:
gemctl.sh engines list
gemctl.sh engines list --location us

# Or if running from source:
python -m gemctl engines list

# Or with gemctl wrapper (after installing):
gemctl.sh engines list
gemctl.sh engines list --location us

# Describe engine
gemctl.sh engines describe ENGINE_ID
gemctl.sh engines describe ENGINE_ID --location us

# Export full configuration
gemctl.sh engines describe ENGINE_ID --full > config.json

# Create search engine
gemctl.sh engines create ENGINE_ID "Display Name" DATASTORE_ID1 DATASTORE_ID2

# Delete engine
gemctl.sh engines delete ENGINE_ID

# List data stores
gemctl.sh data-stores list

# Describe data store
gemctl.sh data-stores describe DATASTORE_ID

# Create data store from GCS bucket
gemctl.sh data-stores create-from-gcs STORE_ID "Store Name" gs://bucket/path/*

# List documents in a data store
gemctl.sh data-stores list-documents DATASTORE_ID

# Delete data store
gemctl.sh data-stores delete DATASTORE_ID
```

### Common Options (ALL OPTIONAL!)

| Option | Description | Default |
|--------|-------------|---------|
| `--project-id` | GCP project ID | From gcloud config or $GOOGLE_CLOUD_PROJECT |
| `--location` | Region (global, us, eu) | From $AGENTSPACE_LOCATION or `us` |
| `--format` | Output format (table, json, yaml) | `table` |
| `--collection` | Collection ID | `default_collection` |
| `--use-service-account` | Use ADC instead of user credentials | User credentials |

### Setting Defaults

```bash
# Using gcloud config
gcloud config set project bluefield-dev

# Using environment variables
export GOOGLE_CLOUD_PROJECT=bluefield-dev
export AGENTSPACE_LOCATION=us

# Now run without flags
python gemctl.py engines list
```

### Authentication

```bash
# User credentials (default)
gcloud auth login
python gemctl.py engines list --project-id my-project

# Service account
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
python gemctl.py engines list --project-id my-project --use-service-account
```

### Help Commands

```bash
python gemctl.py --help                    # Main help
python gemctl.py engines --help            # Engines help
python gemctl.py engines list --help       # Command help
```

---

## Installation

### Option 1: Install from Source (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd gemctl

# Install in development mode
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### Option 2: Install Dependencies Only

```bash
pip install -r requirements.txt
```

### Option 3: Install gemctl Wrapper (For Simple gemctl Command)

```bash
# First install the CLI dependencies
pip install -r requirements.txt

# Then run the gemctl wrapper
./gemctl.sh

# This will:
# 1. Backup your existing gemctl CLI to gemctl-real
# 2. Install the wrapper as gemctl
# 3. Allow you to use: gemctl.sh engines list
```

**Note:** The gemctl wrapper requires the gemctl CLI to be installed first. Make sure to install dependencies before installing the wrapper.

### Dependencies
- `google-auth>=2.23.0`
- `google-auth-httplib2>=0.1.1`
- `requests>=2.31.0`
- `click>=8.1.0`

### Development Dependencies
- `pytest>=7.0.0` - Testing framework
- `black>=23.0.0` - Code formatting
- `flake8>=6.0.0` - Linting
- `mypy>=1.0.0` - Type checking

---

## Quick Start

### 1. Set up authentication

```bash
# Option A: User credentials (default)
gcloud auth login

# Option B: Service account
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

### 2. List engines (AI apps)

```bash
# With explicit flags
python gemctl.py engines list \
  --project-id bluefield-dev \
  --location us

# With service account
python gemctl.py engines list \
  --project-id bluefield-dev \
  --location us \
  --use-service-account

# Or with defaults (if configured)
python gemctl.py engines list
```

### 3. Describe a specific engine

```bash
python gemctl.py engines describe agentspace-demo-np \
  --project-id bluefield-dev \
  --location us
```

### 4. Export full configuration

```bash
python gemctl.py engines describe agentspace-demo-np \
  --project-id bluefield-dev \
  --location us \
  --full > engine-config.json
```

---

## Command Reference

### Command Structure

```
python gemctl.py <RESOURCE> <COMMAND> [OPTIONS]
```

Similar to gcloud: `gcloud compute instances list`

### Available Resources

- **`engines`** - Manage Agentspace engines (AI apps)
- **`data-stores`** - Manage data stores

---

### Engines Commands

#### `engines list` - List all engines

**Syntax:**
```bash
python scripts/agentspace.py engines list \
  [--project-id PROJECT_ID] \
  [--location LOCATION] \
  [--collection COLLECTION_ID] \
  [--format FORMAT]
```

**Options:**
- `--project-id` (optional): Google Cloud project ID (defaults to gcloud config or $GOOGLE_CLOUD_PROJECT)
- `--location` (optional): Location (defaults to $AGENTSPACE_LOCATION or `us`)
- `--collection` (default: `default_collection`): Collection ID
- `--format` (default: `table`): Output format (table, json, yaml)

**Examples:**
```bash
# Table format (default) - uses defaults for project-id and location
python scripts/agentspace.py engines list

# With explicit flags
python scripts/agentspace.py engines list --project-id bluefield-dev --location us

# JSON format
python scripts/agentspace.py engines list --project-id bluefield-dev --location us --format json

# Different collection
python scripts/agentspace.py engines list --project-id bluefield-dev --location us --collection my-collection
```

**Output (table):**
```
====================================================================================================
NAME                                                         DISPLAY NAME                   TYPE      
====================================================================================================
agentspace-demo-np                                           agentspace-demo-np             SEARCH    

Total: 1 engine(s)
```

---

#### `engines describe` - Describe a specific engine

**Syntax:**
```bash
python scripts/agentspace.py engines describe ENGINE_ID \
  [--project-id PROJECT_ID] \
  [--location LOCATION] \
  [--collection COLLECTION_ID] \
  [--format FORMAT] \
  [--full]
```

**Options:**
- `ENGINE_ID` (required): Engine ID or full resource name
- `--full`: Include complete configuration with all data store details

**Examples:**
```bash
# Basic describe (uses defaults)
python scripts/agentspace.py engines describe agentspace-demo-np

# With explicit flags
python scripts/agentspace.py engines describe agentspace-demo-np \
  --project-id bluefield-dev \
  --location us

# JSON format
python scripts/agentspace.py engines describe agentspace-demo-np \
  --project-id bluefield-dev \
  --location us \
  --format json

# Full configuration (for deployment)
python scripts/agentspace.py engines describe agentspace-demo-np \
  --project-id bluefield-dev \
  --location us \
  --full > engine-config.json
```

**Output (human-readable):**
```
================================================================================
Engine: agentspace-demo-np
================================================================================
Name: projects/838086266858/locations/us/collections/default_collection/engines/agentspace-demo-np
Solution Type: SOLUTION_TYPE_SEARCH
Industry Vertical: GENERIC
App Type: APP_TYPE_INTRANET

Common Config:
  companyName: Blue Cross Blue Shield

Search Config:
  Search Tier: SEARCH_TIER_ENTERPRISE
  Search Add-ons: SEARCH_ADD_ON_LLM

Data Stores (3):
  - agentspace-demo-gcs-datastore
  - test_1758213702567
  - logo_1758296148237

Features (7/14 enabled):
  ✓ people-search-org-chart
  ✓ agent-gallery
  ✓ personalization-memory
  ✓ model-selector
  ✓ no-code-agent-builder
  ✓ prompt-gallery
  ✓ disable-onedrive-upload
```

---

#### `engines create` - Create a search engine

**Syntax:**
```bash
python gemctl.py engines create ENGINE_ID DISPLAY_NAME [DATA_STORE_IDS...] \
  [--project-id PROJECT_ID] \
  [--location LOCATION] \
  [--collection COLLECTION_ID] \
  [--search-tier TIER] \
  [--use-service-account] \
  [--format FORMAT]
```

**Arguments:**
- `ENGINE_ID` (required): Unique ID for the engine
- `DISPLAY_NAME` (required): Display name for the engine
- `DATA_STORE_IDS` (optional): One or more data store IDs to connect

**Options:**
- `--search-tier` (default: `SEARCH_TIER_STANDARD`): Search tier (`SEARCH_TIER_STANDARD`, `SEARCH_TIER_ENTERPRISE`)

**Examples:**
```bash
# Create engine with data stores
python gemctl.py engines create my-engine "My Search Engine" datastore1 datastore2

# Create engine without data stores
python gemctl.py engines create my-engine "My Search Engine"

# Create enterprise tier engine
python gemctl.py engines create my-engine "My Search Engine" datastore1 --search-tier=SEARCH_TIER_ENTERPRISE

# With service account
python gemctl.py engines create my-engine "My Search Engine" datastore1 --use-service-account
```

**Required Permissions:**
- `discoveryengine.engines.create`

---

#### `engines delete` - Delete a search engine

**Syntax:**
```bash
python gemctl.py engines delete ENGINE_ID \
  [--project-id PROJECT_ID] \
  [--location LOCATION] \
  [--collection COLLECTION_ID] \
  [--use-service-account] \
  [--force] \
  [--format FORMAT]
```

**Arguments:**
- `ENGINE_ID` (required): Engine ID or full resource name

**Options:**
- `--force`: Skip confirmation prompt

**Examples:**
```bash
# Delete with confirmation
python gemctl.py engines delete my-engine

# Delete without confirmation
python gemctl.py engines delete my-engine --force

# With service account
python gemctl.py engines delete my-engine --use-service-account
```

**Required Permissions:**
- `discoveryengine.engines.delete`

---

### Data Stores Commands

#### `data-stores list` - List all data stores

**Syntax:**
```bash
python scripts/agentspace.py data-stores list \
  [--project-id PROJECT_ID] \
  [--location LOCATION] \
  [--format FORMAT]
```

**Examples:**
```bash
# Table format (uses defaults)
python scripts/agentspace.py data-stores list

# With explicit flags
python scripts/agentspace.py data-stores list --project-id bluefield-dev --location us

# JSON format
python scripts/agentspace.py data-stores list --project-id bluefield-dev --location us --format json
```

---

#### `data-stores describe` - Describe a specific data store

**Syntax:**
```bash
python scripts/agentspace.py data-stores describe DATA_STORE_ID \
  [--project-id PROJECT_ID] \
  [--location LOCATION] \
  [--collection COLLECTION_ID] \
  [--format FORMAT]
```

**Examples:**
```bash
# Human-readable format (uses defaults)
python scripts/agentspace.py data-stores describe agentspace-demo-gcs-datastore

# With explicit flags
python scripts/agentspace.py data-stores describe agentspace-demo-gcs-datastore \
  --project-id bluefield-dev \
  --location us

# JSON format
python scripts/agentspace.py data-stores describe agentspace-demo-gcs-datastore \
  --project-id bluefield-dev \
  --location us \
  --format json
```

---

#### `data-stores create-from-gcs` - Create data store from GCS bucket

**Syntax:**
```bash
python scripts/agentspace.py data-stores create-from-gcs DATA_STORE_ID DISPLAY_NAME GCS_URI \
  [--data-schema SCHEMA] \
  [--reconciliation-mode MODE] \
  [--format FORMAT]
```

**Arguments:**
- `DATA_STORE_ID` (required): Unique ID for the data store
- `DISPLAY_NAME` (required): Display name for the data store
- `GCS_URI` (required): GCS URI (e.g., `gs://bucket-name/path/*`)

**Options:**
- `--data-schema` (default: `content`): Data schema type (`content`, `custom`, `csv`, `document`)
- `--reconciliation-mode` (default: `INCREMENTAL`): Import mode (`INCREMENTAL`, `FULL`)

**Examples:**
```bash
# Create data store from PDF files
python scripts/agentspace.py data-stores create-from-gcs my-docs "My Documents" gs://my-bucket/docs/*.pdf

# Create data store from CSV file
python scripts/agentspace.py data-stores create-from-gcs my-data "My Data" gs://my-bucket/data.csv --data-schema=csv

# Create with full reconciliation mode
python scripts/agentspace.py data-stores create-from-gcs my-store "My Store" gs://my-bucket/* --reconciliation-mode=FULL
```

**Required Permissions:**
- `discoveryengine.dataStores.create`
- `discoveryengine.documents.import`
- `storage.objects.list` (for the GCS bucket)

---

#### `data-stores list-documents` - List documents in a data store

**Syntax:**
```bash
python scripts/agentspace.py data-stores list-documents DATA_STORE_ID \
  [--branch BRANCH] \
  [--format FORMAT]
```

**Arguments:**
- `DATA_STORE_ID` (required): Data store ID or full resource name

**Options:**
- `--branch` (default: `default_branch`): Branch name
- `--format` (default: `table`): Output format (table, json)

**Examples:**
```bash
# List documents in table format
python scripts/agentspace.py data-stores list-documents my-datastore

# List documents in JSON format
python scripts/agentspace.py data-stores list-documents my-datastore --format json

# List documents from a specific branch
python scripts/agentspace.py data-stores list-documents my-datastore --branch my-branch
```

**Output (table):**
```
====================================================================================================
Documents in Data Store: agentspace-demo-gcs-datastore
Branch: default_branch
====================================================================================================
ID                                       URI                                                Index Time               
----------------------------------------------------------------------------------------------------
2467dfadb37a342f97743e2c2542f1a4         gs://agentspace-demo-bucket-np/CPC_192255_00237... 09/11/2025, 05:01:39 PM  
4f354155ef0fbaf64591dd8fffb9bee7         gs://agentspace-demo-bucket-np/CI-Earnings Call... 09/11/2025, 02:40:22 PM  

Total: 4 document(s)
```

**Required Permissions:**
- `discoveryengine.documents.list`

---

#### `data-stores delete` - Delete a data store

**Syntax:**
```bash
python gemctl.py data-stores delete DATA_STORE_ID \
  [--project-id PROJECT_ID] \
  [--location LOCATION] \
  [--collection COLLECTION_ID] \
  [--use-service-account] \
  [--force] \
  [--format FORMAT]
```

**Arguments:**
- `DATA_STORE_ID` (required): Data store ID or full resource name

**Options:**
- `--force`: Skip confirmation prompt

**Examples:**
```bash
# Delete with confirmation
python gemctl.py data-stores delete my-datastore

# Delete without confirmation
python gemctl.py data-stores delete my-datastore --force

# With service account
python gemctl.py data-stores delete my-datastore --use-service-account
```

**Required Permissions:**
- `discoveryengine.dataStores.delete`

---

## Authentication

The CLI supports two authentication methods:

### Method 1: User Credentials (Default)
Uses `gcloud auth print-access-token` - best for interactive use and development.

```bash
# Login with your Google account
gcloud auth login

# Use CLI (no additional flags needed)
python gemctl.py engines list --project-id my-project
```

### Method 2: Service Account (Recommended for automation)
Uses Application Default Credentials (ADC) - best for CI/CD and automated scripts.

```bash
# Option A: Service account key file
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
python gemctl.py engines list --project-id my-project --use-service-account

# Option B: Application default credentials
gcloud auth application-default login
python gemctl.py engines list --project-id my-project --use-service-account
```

### Authentication Flags

| Flag | Description | Use Case |
|------|-------------|----------|
| (default) | Uses `gcloud auth print-access-token` | Interactive use, development |
| `--use-service-account` | Uses Application Default Credentials | CI/CD, automation, scripts |

### Project and Location Configuration

**Project ID** (in order of precedence):
1. `--project-id` flag
2. `GOOGLE_CLOUD_PROJECT` or `GCLOUD_PROJECT` environment variable  
3. `gcloud config set project PROJECT_ID`

**Location** (in order of precedence):
1. `--location` flag
2. `AGENTSPACE_LOCATION` or `GCLOUD_LOCATION` environment variable
3. Default: `"us"`

```bash
# Set defaults for convenience
export GOOGLE_CLOUD_PROJECT=my-project
export AGENTSPACE_LOCATION=us-central1

# Now run without flags
python gemctl.py engines list
```

### Required IAM Permissions

The authenticated account needs:

**For Read Operations:**
- `discoveryengine.collections.list`
- `discoveryengine.engines.list`
- `discoveryengine.engines.get`
- `discoveryengine.dataStores.list`
- `discoveryengine.dataStores.get`
- `discoveryengine.documents.list`

**For Create Operations (data-stores create-from-gcs):**
- `discoveryengine.dataStores.create`
- `discoveryengine.documents.import`
- `storage.objects.list` (for GCS bucket access)

**Predefined Roles:**
- `roles/discoveryengine.viewer` (for read-only operations)
- `roles/discoveryengine.admin` (for full access including create operations)

### Grant Permissions

```bash
# Grant viewer role to service account
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member='serviceAccount:SERVICE_ACCOUNT_EMAIL' \
  --role='roles/discoveryengine.viewer'
```

### Enable API

The Discovery Engine API must be enabled in:
1. The target project (where resources are)
2. The service account's home project (if using cross-project access)

```bash
# Enable API
gcloud services enable discoveryengine.googleapis.com --project=PROJECT_ID

# Verify API is enabled
gcloud services list --enabled --project=PROJECT_ID | grep discoveryengine
```

---

## Usage Examples

### 1. List All Resources

```bash
# List engines (uses defaults)
python gemctl.py engines list

# List data stores (uses defaults)
python gemctl.py data-stores list

# With explicit flags
python gemctl.py engines list --project-id my-project --location us
python gemctl.py data-stores list --project-id my-project --location us

# With service account
python gemctl.py engines list --project-id my-project --location us --use-service-account
```

### 2. Export Configuration for Deployment

```bash
# Export full engine configuration (uses defaults)
python gemctl.py engines describe my-engine --full > engine-config.json

# With explicit flags
python gemctl.py engines describe my-engine \
  --project-id my-project \
  --location us \
  --full > engine-config.json

# With service account
python gemctl.py engines describe my-engine \
  --project-id my-project \
  --location us \
  --use-service-account \
  --full > engine-config.json
```

The exported configuration includes:
- ✅ Engine settings (search tier, solution type, company name)
- ✅ All 14 feature flags (agent gallery, model selector, etc.)
- ✅ Data store configurations
- ✅ Document processing configs (chunking, parsing, OCR)
- ✅ JSON schemas for each data store
- ✅ ACL settings
- ✅ Billing/size information

### 3. Automation/Scripting

```bash
# Get JSON output for parsing (uses defaults)
ENGINE_COUNT=$(python gemctl.py engines list \
  --format json 2>/dev/null | jq 'length')

echo "Found $ENGINE_COUNT engines"

# List all engine names
python gemctl.py engines list \
  --format json | jq -r '.[].displayName'

# With explicit flags
python gemctl.py engines list \
  --project-id my-project \
  --location us \
  --format json | jq -r '.[].displayName'

# With service account
python gemctl.py engines list \
  --project-id my-project \
  --location us \
  --use-service-account \
  --format json | jq -r '.[].displayName'
```

### 4. Backup All Engines

```bash
# Get all engine configurations (uses defaults)
for engine in $(python gemctl.py engines list \
  --format json 2>/dev/null | jq -r '.[].name | split("/") | .[-1]'); do
  python gemctl.py engines describe "$engine" \
    --full > "backup-${engine}.json"
done

# With explicit flags
for engine in $(python gemctl.py engines list \
  --project-id my-project \
  --location us \
  --format json 2>/dev/null | jq -r '.[].name | split("/") | .[-1]'); do
  python gemctl.py engines describe "$engine" \
    --project-id my-project \
    --location us \
    --full > "backup-${engine}.json"
done

# With service account
for engine in $(python gemctl.py engines list \
  --project-id my-project \
  --location us \
  --use-service-account \
  --format json 2>/dev/null | jq -r '.[].name | split("/") | .[-1]'); do
  python gemctl.py engines describe "$engine" \
    --project-id my-project \
    --location us \
    --use-service-account \
    --full > "backup-${engine}.json"
done
```

### 5. Check Multiple Locations

```bash
# Check global location
python gemctl.py engines list --project-id my-project --location global

# Check US region
python gemctl.py engines list --project-id my-project --location us

# Check EU region
python gemctl.py engines list --project-id my-project --location eu

# With service account
python gemctl.py engines list --project-id my-project --location us --use-service-account
```

**Note:** The CLI automatically uses the correct regional endpoint:
- `global` → `https://discoveryengine.googleapis.com/v1`
- `us` → `https://us-discoveryengine.googleapis.com/v1` (default)
- `eu` → `https://eu-discoveryengine.googleapis.com/v1`

---

## Deployment Guide

### Exported Configuration Details

When you export an engine configuration with `--full`, you get complete deployment-ready details:

#### Engine Configuration
- Display name, solution type, industry vertical
- Search tier (STANDARD/ENTERPRISE) & search add-ons
- Company name, app type
- **14+ Feature Flags:**
  - `agent-gallery`, `model-selector`, `prompt-gallery`
  - `personalization-memory`, `people-search-org-chart`
  - `no-code-agent-builder`
  - Upload controls (Google Drive, OneDrive)
  - `session-sharing`, `bi-directional-audio`
  - `notebook-lm`, image/video generation controls

#### Data Store Configuration (for each)
- Display name, creation time, industry vertical
- Content configuration, solution types
- **Document Processing:**
  - Chunking config (layout-based, chunk size)
  - Parsing config (digital, layout, OCR)
  - Table & image annotation settings
- **JSON Schema** (field definitions, validation rules)
- **ACL settings** (if enabled)
- **Billing information** (data size, last update)

### Deployment Steps

#### Step 1: Export from Source Environment

```bash
export GOOGLE_APPLICATION_CREDENTIALS="configs/source-project-creds.json"

python scripts/agentspace.py engines describe my-engine \
  --project-id source-project \
  --location us \
  --full > configs/engine-prod-template.json
```

#### Step 2: Review Configuration

```bash
# View configuration
cat configs/engine-prod-template.json | python3 -m json.tool | less

# Get summary
python3 << 'EOF'
import json
with open("configs/engine-prod-template.json") as f:
    config = json.load(f)

print("Engine:", config['engine']['displayName'])
print("Search Tier:", config['engine']['searchEngineConfig']['searchTier'])
print("Data Stores:", len(config['data_stores']))
print("Features Enabled:", sum(1 for v in config['engine']['features'].values() if 'ON' in v))
EOF
```

#### Step 3: Modify for Target Environment

Edit the configuration file:
1. Change project ID references
2. Update display name if needed
3. Adjust feature flags for different requirements
4. Update company name if different
5. Modify data store configurations as needed

#### Step 4: Deploy

The exported configuration can be used with:
- **Google Cloud Console**: Manual creation using the settings
- **Terraform**: Create IaC based on configuration
- **gcloud CLI**: Use gcloud commands with parameters
- **REST API**: POST configuration to Discovery Engine API

### Example Terraform Template

```hcl
# Based on exported configuration
resource "google_discovery_engine_search_engine" "prod_engine" {
  engine_id        = "my-engine-prod"
  collection_id    = "default_collection"
  location         = var.location
  display_name     = "Production Engine"
  
  solution_type    = "SOLUTION_TYPE_SEARCH"
  industry_vertical = "GENERIC"
  search_tier      = "SEARCH_TIER_ENTERPRISE"
  search_add_ons   = ["SEARCH_ADD_ON_LLM"]
  company_name     = "My Company"
  
  data_store_ids   = [
    google_discovery_engine_data_store.primary.data_store_id,
  ]
}
```

---

## Migration Guide

If you're migrating from the old argparse-based CLI:

### Command Mapping

| Old Command | New Command |
|-------------|-------------|
| `list_agentspace_apps.py --project-id ID --location us` | `scripts/agentspace.py engines list --project-id ID --location us` |
| `list_agentspace_apps.py --get-engine ENGINE` | `scripts/agentspace.py engines describe ENGINE --project-id ID --location us` |
| `list_agentspace_apps.py --get-engine ENGINE --output-file FILE` | `scripts/agentspace.py engines describe ENGINE --full > FILE` |
| `list_agentspace_apps.py --get-all-engines` | Loop over `engines list` results |

### Key Changes

1. **Command Structure**: Changed from flat to hierarchical (resource + action)
2. **Output Files**: Use shell redirection (`>`) instead of `--output-file`
3. **Default Format**: Changed from "text" to "table"
4. **Batch Operations**: Manual iteration instead of `--get-all-engines`

---

## Troubleshooting

### API Not Enabled (403 Error)

**Symptom:** 
```
Error: 403 Client Error: Forbidden
Message: Discovery Engine API has not been used in project...
```

**Solution:**
```bash
# Enable API in target project
gcloud services enable discoveryengine.googleapis.com --project=PROJECT_ID

# If using cross-project service account, enable in SA's home project too
gcloud services enable discoveryengine.googleapis.com --project=SA_PROJECT_ID

# Wait 1-2 minutes for propagation
```

### Permission Denied

**Symptom:** `Permission 'discoveryengine.*.list' denied`

**Solution:**
```bash
# Grant permissions to service account
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member='serviceAccount:SA_EMAIL' \
  --role='roles/discoveryengine.viewer'

# Wait 30-60 seconds for IAM propagation
```

### No Resources Found

**Symptom:** All counts are 0, but API is enabled

**Possible reasons:**
- Resources exist in a different location (try `--location us` or `--location eu`)
- Resources exist in a different project
- No AI apps have been created yet (this is normal!)

### Authentication Errors

**Symptom:** `DefaultCredentialsError: Your default credentials were not found`

**Solution:**
```bash
# Set up credentials
gcloud auth application-default login

# Or use service account
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
```

### Incorrect Regional Endpoint

**Symptom:** `400 Client Error: Incorrect API endpoint used`

**Solution:** Resources in regional locations (us, eu) require the correct `--location` flag. The CLI handles regional endpoints automatically, but you must specify the correct location:

```bash
# If resources are in 'us' region
python scripts/agentspace.py engines list --project-id PROJECT_ID --location us
```

---

## Advanced Topics

### Regional Endpoints

The CLI automatically uses the correct regional endpoint based on `--location`:

| Location | API Endpoint |
|----------|-------------|
| `global` | `https://discoveryengine.googleapis.com/v1` |
| `us`, `us-central1` | `https://us-discoveryengine.googleapis.com/v1` (default) |
| `eu`, `eu-west1` | `https://eu-discoveryengine.googleapis.com/v1` |

### Cross-Project Access

When using a service account from one project to access resources in another:

1. Enable Discovery Engine API in **both** projects
2. Grant IAM permissions in the target project
3. Wait for permissions to propagate (30-60 seconds)

### Output Formats

#### Table (default)
- Human-readable
- Columnar display
- Summary statistics
- Best for terminal viewing

#### JSON
- Machine-readable
- Complete data structure
- Suitable for automation
- Can be parsed with `jq`

#### YAML
- Similar to table (can be enhanced)
- Good for configuration files

---

## Help Commands

Get help at any level:

```bash
# Main help
python gemctl.py --help

# Resource help
python gemctl.py engines --help
python gemctl.py data-stores --help

# Command help
python gemctl.py engines list --help
python gemctl.py engines describe --help
python gemctl.py engines create --help
python gemctl.py engines delete --help
python gemctl.py data-stores list --help
python gemctl.py data-stores describe --help
python gemctl.py data-stores create-from-gcs --help
python gemctl.py data-stores list-documents --help
python gemctl.py data-stores delete --help
```

---

## API Reference

This tool uses the [Google Cloud Discovery Engine REST API](https://cloud.google.com/generative-ai-app-builder/docs/reference/rest).

Key endpoints:
- `GET /v1/{parent}/collections` - List collections
- `GET /v1/{parent}/engines` - List engines
- `GET /v1/{engine}` - Get engine details
- `GET /v1/{parent}/dataStores` - List data stores
- `GET /v1/{dataStore}` - Get data store details
- `GET /v1/{dataStore}/schemas/{schema}` - Get schema

---

## Development

### Project Structure

```
gemctl/
├── gemctl/                 # Main package
│   ├── __init__.py        # Package initialization
│   ├── __main__.py        # Entry point for python -m gemctl
│   └── cli.py             # Main CLI implementation
├── tests/                 # Test suite
│   ├── __init__.py
│   └── test_cli.py        # Basic CLI tests
├── gemctl.sh              # gemctl wrapper script
├── install-gemctl-wrapper.sh    # Installation script
├── uninstall-gemctl-wrapper.sh  # Uninstallation script
├── pyproject.toml          # Modern Python packaging
├── requirements.txt       # Dependencies
├── Makefile              # Development tasks
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

### Development Commands

```bash
# Install in development mode
make install-dev

# Run tests
make test

# Format code
make format

# Run linting
make lint

# Clean build artifacts
make clean

# Build package
make build

# Run CLI
make run
```

### gemctl Wrapper Development

```bash
# Run gemctl wrapper for testing
./gemctl.sh

# Test gemctl.sh commands
gemctl.sh engines list --help
gemctl.sh data-stores list --help

# Uninstall wrapper
./uninstall-gemctl-wrapper.sh
```

### Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=gemctl

# Run specific test
pytest tests/test_cli.py::TestCLI::test_help_command
```

---

## Contributing

### Adding New Commands

The CLI uses Click's group/command structure:

```python
@cli.group()
def new_resource():
    """Manage new resource type."""
    pass

@new_resource.command('list')
@project_option
@location_option
def new_resource_list(project_id, location):
    """List new resources."""
    # Implementation
```

### Testing

Test all commands before committing:

```bash
# Test help
python gemctl.py --help
python gemctl.py engines --help

# Test list commands
python gemctl.py engines list --project-id TEST_PROJECT --location us
python gemctl.py data-stores list --project-id TEST_PROJECT --location us

# Test describe commands
python gemctl.py engines describe ENGINE_ID --project-id TEST_PROJECT --location us
python gemctl.py data-stores describe DS_ID --project-id TEST_PROJECT --location us

# Test create commands
python gemctl.py engines create test-engine "Test Engine" --project-id TEST_PROJECT --location us
python gemctl.py data-stores create-from-gcs test-store "Test Store" gs://test-bucket/* --project-id TEST_PROJECT --location us

# Test JSON output
python gemctl.py engines list --project-id TEST_PROJECT --location us --format json

# Test service account authentication
python gemctl.py engines list --project-id TEST_PROJECT --location us --use-service-account
```

---

## License

[Add your license information here]

---

## Support

For questions or issues:
1. Check this README for documentation
2. Use `--help` at any command level
3. Review error messages carefully (they often contain solutions)
4. Check Google Cloud Console to verify resources exist
5. Verify IAM permissions and API enablement

---

## Version History

- **v1.0.0** - Initial Click-based CLI with gcloud-style commands
  - `engines list`, `engines describe`, `engines create`, `engines delete`
  - `data-stores list`, `data-stores describe`, `data-stores create-from-gcs`, `data-stores list-documents`, `data-stores delete`
  - Regional endpoint support
  - Table, JSON, and YAML output formats
  - User credentials and service account authentication
  - Comprehensive help system with authentication guidance


