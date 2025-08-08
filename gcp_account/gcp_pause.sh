#!/usr/bin/env bash
set -euo pipefail

# gcp-pause.sh
# Stops/runs safe pause actions across a project while preserving storage.
# Defaults to dry-run. Use --confirm to make changes.
#
# Usage:
#   ./gcp-pause.sh --dry-run
#   ./gcp-pause.sh --confirm
#   ./gcp-pause.sh --confirm --aggressive

PROJECT="provaichathistory"
DRY_RUN=true
CONFIRM=false
AGGRESSIVE=false
REGION=""   # optional; auto-detected for Cloud Run if not provided
QUIET_FLAGS=""

# Help
usage() {
  cat <<EOF
gcp-pause.sh - Pause compute resources while preserving storage

Options:
  --project PROJECT_ID    Set GCP project (default: current gcloud project)
  --region REGION         Region to use for Cloud Run (auto-detected)
  --dry-run               Show actions only (default)
  --confirm               Apply changes (required to take action)
  --aggressive            Also remove public invoker IAM bindings from Cloud Functions (non-destructive)
  -h, --help              Show this help

Examples:
  ./gcp-pause.sh --dry-run
  ./gcp-pause.sh --confirm
  ./gcp-pause.sh --confirm --aggressive
EOF
}

# Parse args
while [[ $# -gt 0 ]]; do
  case $1 in
    --project) PROJECT="$2"; shift 2;;
    --region) REGION="$2"; shift 2;;
    --dry-run) DRY_RUN=true; shift;;
    --confirm) DRY_RUN=false; CONFIRM=true; shift;;
    --aggressive) AGGRESSIVE=true; shift;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown arg: $1"; usage; exit 1;;
  esac
done

# If no project provided, use current gcloud project
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
  echo "Aggressive mode: will remove public invoker IAM bindings from HTTP Cloud Functions."
fi

# Helper to run or echo
run_or_echo() {
  if $DRY_RUN; then
    echo "[DRY-RUN] $*"
  else
    echo "[RUN] $*"
    eval "$@"
  fi
}

# 1) Stop all Compute Engine VMs
echo
echo "=== Compute Engine: Stopping VMs ==="
ZONES=$(gcloud compute zones list --project="$PROJECT" --format="value(name)")
if [[ -z "$ZONES" ]]; then
  echo "No zones found or compute API not enabled."
else
  for z in $ZONES; do
    INSTANCES=$(gcloud compute instances list --project="$PROJECT" --zones="$z" --format="value(name)" || true)
    if [[ -z "$INSTANCES" ]]; then
      echo "  zone=$z: no instances"
      continue
    fi
    for inst in $INSTANCES; do
      echo "  Will stop instance: $inst (zone: $z)"
      run_or_echo "gcloud compute instances stop '$inst' --zone='$z' --project='$PROJECT' --quiet"
    done
  done
fi

# 2) Stop Cloud SQL instances (set activation-policy=NEVER)
echo
echo "=== Cloud SQL: Setting activation-policy=NEVER ==="
SQL_INSTANCES=$(gcloud sql instances list --project="$PROJECT" --format="value(name)" || true)
if [[ -z "$SQL_INSTANCES" ]]; then
  echo "  No Cloud SQL instances found."
else
  for s in $SQL_INSTANCES; do
    echo "  Will patch Cloud SQL instance: $s -> activation-policy=NEVER"
    run_or_echo "gcloud sql instances patch '$s' --activation-policy=NEVER --project='$PROJECT' --quiet"
  done
fi

# 3) Scale GKE node pools to 0
echo
echo "=== GKE: Resizing node pools to 0 ==="
CLUSTERS=$(gcloud container clusters list --project="$PROJECT" --format="value(name,location)" || true)
if [[ -z "$CLUSTERS" ]]; then
  echo "  No GKE clusters found."
else
  echo "$CLUSTERS" | while read -r line; do
    # line format: name location
    cluster_name=$(echo $line | awk '{print $1}')
    location=$(echo $line | awk '{print $2}')
    echo "  Cluster: $cluster_name (location: $location)"
    NODE_POOLS=$(gcloud container node-pools list --cluster="$cluster_name" --project="$PROJECT" --zone="$location" --format="value(name)" 2>/dev/null || true)
    if [[ -z "$NODE_POOLS" ]]; then
      # try regional API (if zone not correct)
      NODE_POOLS=$(gcloud container node-pools list --cluster="$cluster_name" --project="$PROJECT" --region="$location" --format="value(name)" 2>/dev/null || true)
    fi
    if [[ -z "$NODE_POOLS" ]]; then
      echo "    No node pools found or cluster location handling required."
      continue
    fi
    for np in $NODE_POOLS; do
      echo "    Will resize node pool $np -> 0 nodes"
      # Use resize (zone/regional) attempt; prefer cluster-level location variable
      # If it fails for zone vs region mismatch, user can re-run with region set manually.
      run_or_echo "gcloud container clusters resize '$cluster_name' --node-pool='$np' --num-nodes=0 --project='$PROJECT' --zone='$location' --quiet || gcloud container clusters resize '$cluster_name' --node-pool='$np' --num-nodes=0 --project='$PROJECT' --region='$location' --quiet"
    done
  done
fi

# 4) Cloud Run: set max-instances=0 for managed services
echo
echo "=== Cloud Run: Setting max-instances=0 ==="
# detect region if not provided (take first region used by services)
if [[ -z "$REGION" ]]; then
  REGION=$(gcloud run services list --project="$PROJECT" --platform=managed --format="value(region)" --limit=1 2>/dev/null || echo "")
fi
if [[ -z "$REGION" ]]; then
  echo "  No Cloud Run managed services found or region unknown."
else
  SERVICES=$(gcloud run services list --project="$PROJECT" --platform=managed --region="$REGION" --format="value(metadata.name)" 2>/dev/null || true)
  if [[ -z "$SERVICES" ]]; then
    echo "  No Cloud Run services found in region $REGION."
  else
    for svc in $SERVICES; do
      echo "  Will set Cloud Run service $svc --max-instances=0 (region: $REGION)"
      run_or_echo "gcloud run services update '$svc' --project='$PROJECT' --platform=managed --region='$REGION' --max-instances=0 --quiet"
    done
  fi
fi

# 5) Cloud Functions: remove allUsers invoker binding for HTTP functions (aggressive, reversible)
echo
echo "=== Cloud Functions: HTTP invoker binding removal (aggressive optional) ==="
if $AGGRESSIVE; then
  FUNCS=$(gcloud functions list --project="$PROJECT" --format="value(name,region)" || true)
  if [[ -z "$FUNCS" ]]; then
    echo "  No Cloud Functions found."
  else
    echo "$FUNCS" | while read -r fline; do
      fname=$(echo $fline | awk '{print $1}')
      freg=$(echo $fline | awk '{print $2}')
      # Check if function is HTTP-triggered by querying its httpsTrigger
      trigger_type=$(gcloud functions describe "$fname" --region="$freg" --project="$PROJECT" --format="value(httpsTrigger.url)" 2>/dev/null || echo "")
      if [[ -n "$trigger_type" ]]; then
        echo "  HTTP function: $fname (region: $freg) -> will remove allUsers invoker binding if present"
        # Remove binding for allUsers (reversible by re-adding)
        run_or_echo "gcloud functions remove-iam-policy-binding '$fname' --region='$freg' --project='$PROJECT' --member='allUsers' --role='roles/cloudfunctions.invoker' --quiet || true"
      else
        echo "  Non-HTTP or background function: $fname (region: $freg) -> no automatic action taken"
      fi
    done
  fi
else
  echo "  Aggressive mode not enabled. No changes to Cloud Functions."
fi

# Summary and tips
echo
echo "=== Summary ==="
echo "- Stopped / paused compute resources (VMs, Cloud SQL, GKE, Cloud Run) in project: $PROJECT"
echo "- Storage (Persistent Disks, Cloud Storage, snapshots) NOT deleted by this script."
echo "- Cloud Functions: not modified unless you used --aggressive."
echo
if $DRY_RUN; then
  echo "DRY RUN only. Re-run with --confirm to apply changes."
else
  echo "Actions applied. Monitor console or run 'gcloud compute instances list', 'gcloud sql instances list', 'gcloud container clusters list', and 'gcloud run services list' to confirm."
fi

exit 0
