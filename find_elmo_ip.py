import socket
import netifaces
import threading
import time

CONTEXT = {
    "scanning_robots": False,
    "robot_model": ""
}


def callback(robot_name, robot_address):
    """Callback function called when a robot is found"""
    print(f"Found robot: {robot_name} at {robot_address}")


def scan_robots(cb, models=[]):
    def scan_robots_runnable():
        # 1. Keep a persistent set of IPs we have already found
        found_ips = set()

        while CONTEXT["scanning_robots"]:
            try:
                # Get all interface IPs
                interfaces = netifaces.interfaces()
                allips = []
                for i in interfaces:
                    try:
                        addr = netifaces.ifaddresses(i)[netifaces.AF_INET][0]["addr"]
                        if not addr.startswith("127."):
                            allips.append(addr)
                    except:
                        pass

                msg = b'ruarobot'

                # Scan each interface
                for ip in allips:
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                        # Timeout is short so we can loop and retry sending
                        sock.settimeout(0.5)
                        sock.bind((ip, 0))

                        # 2. SEND MULTIPLE TIMES: Send the broadcast 3 times per interface
                        #    This accounts for packet loss or collisions on WiFi
                        for _ in range(3):
                            sock.sendto(msg, ("255.255.255.255", 5000))

                            # Listen for responses after each send
                            start_time = time.time()
                            while time.time() - start_time < 1.0:  # Listen for 1 second window
                                try:
                                    data, address = sock.recvfrom(1024)

                                    if b"iamarobot" in data:
                                        _, robot_model, robot_name, server_port = data.decode("utf-8").split(";")

                                        # 3. FILTER DUPLICATES: Only callback if we haven't seen this IP yet
                                        if address[0] not in found_ips:
                                            found_ips.add(address[0])

                                            # Filter by model if requested
                                            if CONTEXT["robot_model"]:
                                                if robot_model == CONTEXT["robot_model"]:
                                                    cb(robot_name, "http://%s:%s" % (address[0], server_port))
                                            else:
                                                cb(robot_name, "http://%s:%s" % (address[0], server_port))

                                except socket.timeout:
                                    # No packet received in this short window, continue loop
                                    pass
                                except Exception as e:
                                    print(f"Socket error: {e}")
                                    break

                        sock.close()
                    except Exception as e:
                        print(f"Interface error: {e}")
                        pass

                # Optional: slight sleep before rescanning interfaces to save CPU
                time.sleep(1)

            except Exception as e:
                print(f"Scan error: {e}")
                pass

    CONTEXT["scanning_robots"] = True
    t = threading.Thread(target=scan_robots_runnable)
    t.start()


# Start the scan
scan_robots(callback)