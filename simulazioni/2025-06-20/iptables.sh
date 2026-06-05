#nome e cognome: Giuriato Simone
#matricola: 


iptables -F
iptables -t nat -F

iptables -P INPUT DROP
iptables -P FORWARD DROP

iptables -A INPUT -i eth0 -p icmp -j ACCEPT
iptables -A INPUT -i eth1 -p icmp -j ACCEPT

iptables -A INPUT -p tcp --dport 22 -i eth1 -j ACCEPT

iptables -A FORWARD -i eth1 -o eth0 -j ACCEPT

iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

iptables -t nat -A PREROUTING -p tcp --dport 990 -i eth0 -j DNAT --to-destination 10.10.20.50:19990
iptables -A FORWARD -i eth0 -o eth1 -p tcp --dport 19990 -d 10.10.20.50 -j ACCEPT