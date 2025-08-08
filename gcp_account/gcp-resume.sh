#!/usr/bin/env bash
set -euo pipefail

# gcp-resume.sh
# Reverse "pause" actions: start VMs, activate Cloud SQL, resize GKE, restore Cloud Run, optionally Cloud Functions.
# Defaults to dry-run. Use --confirm to apply.
#
# Usage:
#   ./gcp-resume.sh --dry-run
#   ./gcp-resume.sh --confirm
#   ./gcp-resume.sh --confirm --aggressive
#
# Optional flags:
#   --project PROJECT_ID   (default: current gcloud project)
#   --node-count N        Number of nodes per GKE node pool (default: 3)
#   --dry-run             Show actions, no changes (default)
#   --confirm             Apply changes
#   --aggressive          Re-add public invoker IAM binding for HTTP Cloud Functions

PROJECT="provaichathistory"
DRY_RUN=true
CONFIRM=false
AGGRESSIVE=false
NODE_COUNT=3

usage() {
  cat <<EOF
gcp-resume.sh - Resume GCP compute services after pause

Options:
  --project PROJECT_ID   Set GCP project (default current gcloud project)
  --node-count N        Number of nodes per GKE node pool (default 3)
  --dry-run             Show actions only (default)
  --confirm             Apply changes
  --aggressive          Restore public invoker bindings to HTTP Cloud Functions
  -h, --help            Show this help

Examples:
  ./gcp-resume.sh --dry-run
  ./gcp-resume.sh --confirm --node-count 5
  ./gcp-resume.sh --confirm --aggressive
EOF
}

while [[ $# -gt 0 ]]; do
  case $1 in
    --project) PROJECT="$2"; shift 2;;
    --node-count) NODE_COUNT="$2"; shift 2;;
    --dry-run) DRY_RUN=true; shift;;
    --confirm) DRY_RUN=false; CONFIRM=true; shift;;
    --aggressive) AGGRESSIVE=true; shift;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown arg: $1"; usage; exit 1;;
  esac
done

if [[ -z "$PROJECT" ]]; then
  PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")
  if [[ -z "$PROJECT" ]]; then
    echo "No project set. Provide --project or run 'gcloud config set project PROJECT_ID'."
    exit 1
  fi
fi

echo "Project: $PROJECT"
if $DRY_RUN; then
  echo "Mode: DRY RUN (no changes will be made). Use --confirm to apply."
else
  echo "Mode: LIVE (changes will be applied)."
fi
if $AGGRESSIVE; then
  echo "Aggressive mode: will re-add public invoker IAM bindings to HTTP Cloud Functions."
fi

run_or_echo() {
  if $DRY_RUN; then
    echo "[DRY-RUN] $*"
  else
    echo "[RUN] $*"
    eval "$@"
  fi
}

# 1) Start all Compute Engine VMs
echo
echo "=== Compute Engine: Starting VMs ==="
ZONES=$(gcloud compute zones list --project="$PROJECT" --format="value(name)")
for z in $ZONES; do
  INSTANCES=$(gcloud compute instances list --project="$PROJECT" --zones="$z" --format="value(name)" || true)
  for inst in $INSTANCES; do
    echo "  Will start instance: $inst (zone: $z)"
    run_or_echo "gcloud compute instances start '$inst' --zone='$z' --project='$PROJECT' --quiet"
  done
done

# 2) Set Cloud SQL activation-policy=ALWAYS
echo
echo "=== Cloud SQL: Setting activation-policy=ALWAYS ==="
SQL_INSTANCES=$(gcloud sql instances list --project="$PROJECT" --format="value(name)" || true)
for s in $SQL_INSTANCES; do
  echo "  Will patch Cloud SQL instance: $s -> activation-policy=ALWAYS"
  run_or_echo "gcloud sql instances patch '$s' --activation-policy=ALWAYS --project='$PROJECT' --quiet"
done

# 3) Resize GKE node pools to $NODE_COUNT nodes
echo
echo "=== GKE: Resizing node pools to $NODE_COUNT nodes ==="
CLUSTERS=$(gcloud container clusters list --project="$PROJECT" --format="value(name,location)" || true)
if [[ -z "$CLUSTERS" ]]; then
  echo "  No GKE clusters found."
else
  echo "$CLUSTERS" | while read -r line; do
    cluster_name=$(echo $line | awk '{print $1}')
    location=$(echo $line | awk '{print $2}')
    echo "  Cluster: $cluster_name (location: $location)"
    NODE_POOLS=$(gcloud container node-pools list --cluster="$cluster_name" --project="$PROJECT" --zone="$location" --format="value(name)" 2>/dev/null || true)
    if [[ -z "$NODE_POOLS" ]]; then
      NODE_POOLS=$(gcloud container node-pools list --cluster="$cluster_name" --project="$PROJECT" --region="$location" --format="value(name)" 2>/dev/null || true)
    fi
    for np in $NODE_POOLS; do
      echo "    Will resize node pool $np -> $NODE_COUNT nodes"
      run_or_echo "gcloud container clusters resize '$cluster_name' --node-pool='$np' --num-nodes=$NODE_COUNT --project='$PROJECT' --zone='$location' --quiet || gcloud container clusters resize '$cluster_name' --node-pool='$np' --num-nodes=$NODE_COUNT --project='$PROJECT' --region='$location' --quiet"
    done
  done
fi

# 4) Remove Cloud Run max-instances=0 limit (set to unlimited)
echo
echo "=== Cloud Run: Removing max-instances=0 limit ==="
REGION=$(gcloud run services list --project="$PROJECT" --platform=managed --format="value(region)" --limit=1 2>/dev/null || echo "")
if [[ -z "$REGION" ]]; then
  echo "  No Cloud Run managed services found."
else
  SERVICES=$(gcloud run services list --project="$PROJECT" --platform=managed --region="$REGION" --format="value(metadata.name)" 2>/dev/null || true)
  for svc in $SERVICES; do
    echo "  Will update Cloud Run service $svc --max-instances=unlimited (region: $REGION)"
    run_or_echo "gcloud run services update '$svc' --project='$PROJECT' --platform=managed --region='$REGION' --max-instances=unlimited --quiet"
  done
fi

# 5) Cloud Functions: Re-add allUsers invoker binding if aggressive
echo
echo "=== Cloud Functions: Re-adding allUsers invoker binding (aggressive) ==="
if $AGGRESSIVE; then
  FUNCS=$(gcloud functions list --project="$PROJECT" --format="value(name,region)" || true)
  for fline in $FUNCS; do
    fname=$(echo $fline | awk '{print $1}')
    freg=$(echo $fline | awk '{print $2}')
    trigger_url=$(gcloud functions describe "$fname" --region="$freg" --project="$PROJECT" --format="value(httpsTrigger.url)" 2>/dev/null || echo "")
    if [[ -n "$trigger_url" ]]; then
      echo "  HTTP function: $fname (region: $freg) -> will add allUsers invoker binding"
      run_or_echo "gcloud functions add-iam-policy-binding '$fname' --region='$freg' --project='$PROJECT' --member='allUsers' --role='roles/cloudfunctions.invoker' --quiet"
    else
      echo "  Non-HTTP function: $fname (region: $freg) -> no invoker binding added"
    fi
  done
else
  echo "  Aggressive mode not enabled. No changes to Cloud Functions."
fi

echo
echo "=== Summary ==="
echo "- Started VMs, activated Cloud SQL, resized GKE node pools, restored Cloud Run services."
echo "- Cloud Functions invoker bindings restored only if --aggressive used."
if $DRY_RUN; then
  echo "DRY RUN only. Re-run with --confirm to apply changes."
else
  echo "Actions applied successfully."
fi

exit 0
