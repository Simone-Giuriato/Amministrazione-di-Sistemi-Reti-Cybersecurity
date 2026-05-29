#!/bin/bash
set -e

PUBLIC_SUBNET=192.0.2.0/24
PUBLIC_GATEWAY=192.0.2.254
FIREWALL_PUBLIC_IP=192.0.2.5
CLIENT_IP=192.0.2.50

PRIVATE_SUBNET=172.16.0.0/24
PRIVATE_GATEWAY=172.16.0.254
FIREWALL_PRIVATE_IP=172.16.0.1
WEB_IP=172.16.0.30

IMAGE=fglmtt/admin

run() {
    local label=$1
    shift
    echo -n "${label}... "
    if output=$("$@" 2>&1); then
        echo "OK"
    else
        echo "FAILED"
        echo "$output"
        echo
        echo "To clean up partial state, run: ./down.sh"
        exit 1
    fi
}

set_default_route() {
    local container=$1
    local gateway=$2
    podman exec -u root "$container" ip route del default 2>/dev/null || true
    podman exec -u root "$container" ip route add default via "$gateway"
}

cat <<EOF
Topology:

  client (${CLIENT_IP})
    └─ external network (${PUBLIC_SUBNET}, gw ${PUBLIC_GATEWAY})
         └─ firewall  ${FIREWALL_PUBLIC_IP} | ${FIREWALL_PRIVATE_IP}
              └─ internal network (${PRIVATE_SUBNET}, gw ${PRIVATE_GATEWAY})
                   └─ web (${WEB_IP})

EOF

echo "Networks:"
run "  Creating external (${PUBLIC_SUBNET})" \
    podman network create external \
        --subnet "${PUBLIC_SUBNET}" \
        --gateway "${PUBLIC_GATEWAY}"
run "  Creating internal (${PRIVATE_SUBNET})" \
    podman network create internal \
        --subnet "${PRIVATE_SUBNET}" \
        --gateway "${PRIVATE_GATEWAY}"

echo
echo "Containers:"
run "  Starting firewall (${FIREWALL_PUBLIC_IP} | ${FIREWALL_PRIVATE_IP})" \
    podman run -d --name firewall --hostname firewall \
        --cap-add NET_ADMIN --cap-add NET_RAW \
        --sysctl net.ipv4.ip_forward=1 \
        --network external:ip="${FIREWALL_PUBLIC_IP}" \
        --network internal:ip="${FIREWALL_PRIVATE_IP}" \
        "${IMAGE}" sleep infinity

run "  Starting client (${CLIENT_IP})" \
    podman run -d --name client --hostname client \
        --cap-add NET_ADMIN --cap-add NET_RAW \
        --network external:ip="${CLIENT_IP}" \
        "${IMAGE}" sleep infinity
run "  Routing client default via ${FIREWALL_PUBLIC_IP}" \
    set_default_route client "${FIREWALL_PUBLIC_IP}"

run "  Starting web (${WEB_IP})" \
    podman run -d --name web --hostname web \
        --cap-add NET_ADMIN --cap-add NET_RAW \
        --network internal:ip="${WEB_IP}" \
        "${IMAGE}" sleep infinity
run "  Routing web default via ${FIREWALL_PRIVATE_IP}" \
    set_default_route web "${FIREWALL_PRIVATE_IP}"
