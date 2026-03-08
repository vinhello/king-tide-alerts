#!/bin/bash
# Allowlist-based outbound firewall.
# Blocks everything except domains this project and Claude Code need.
# Called from setup-container.sh after container creation.

set -e

echo "🔒 Initialising firewall..."

# Require root
if [ "$EUID" -ne 0 ]; then
  echo "Re-running with sudo..."
  exec sudo bash "$0" "$@"
fi

# Flush existing rules
iptables -F OUTPUT 2>/dev/null || true
iptables -P OUTPUT ACCEPT  # reset to permissive while we build rules

# Allow loopback
iptables -A OUTPUT -o lo -j ACCEPT

# Allow already-established connections
iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow DNS (required to resolve domain names)
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT

# Resolve and allowlist specific domains
ALLOWED_DOMAINS=(
  # Claude Code
  "api.anthropic.com"          # Claude API
  "statsig.anthropic.com"      # Claude Code telemetry
  "sentry.io"                  # Claude Code error reporting

  # Package registries
  "registry.npmjs.org"         # npm packages
  "npmjs.org"
  "pypi.org"                   # pip packages
  "files.pythonhosted.org"     # pip package downloads

  # GitHub
  "github.com"                 # git + gh CLI
  "api.github.com"
  "objects.githubusercontent.com"
  "raw.githubusercontent.com"
  "ghcr.io"                    # GitHub Container Registry

  # Project APIs
  "tidesandcurrents.noaa.gov"  # NOAA tide predictions
  "api.resend.com"             # Resend email API
  "api.twilio.com"             # Twilio SMS API
  "api.stripe.com"             # Stripe payments API
  "js.stripe.com"              # Stripe JS SDK
)

for domain in "${ALLOWED_DOMAINS[@]}"; do
  echo -n "  Resolving $domain... "
  IPS=$(dig +short "$domain" 2>/dev/null | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' || true)
  if [ -n "$IPS" ]; then
    for ip in $IPS; do
      iptables -A OUTPUT -d "$ip" -j ACCEPT
    done
    echo "✓ ($(echo $IPS | wc -w) IPs)"
  else
    echo "⚠ could not resolve (skipping)"
  fi
done

# Block everything else
iptables -P OUTPUT DROP

echo "✅ Firewall active. All other outbound traffic blocked."
