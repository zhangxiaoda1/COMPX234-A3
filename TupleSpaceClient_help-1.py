import socket
import sys
import os

def receive_n(sock, n):
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            break
        data += chunk
    return data

def main():
    if len(sys.argv) != 4:
        print("Usage: python tuple_space_client.py <server-hostname> <server-port> <input-file>")
        sys.exit(1)

    hostname = sys.argv[1]
    port = int(sys.argv[2])
    input_file_path = sys.argv[3]

    if not os.path.exists(input_file_path):
        print(f"Error: Input file '{input_file_path}' does not exist.")
        sys.exit(1)

    with open(input_file_path, 'r') as file:
        lines = file.readlines()

    # create and connect socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((hostname, port))

    try:
        for line in lines:
            line = line.strip()
            if not line:
                continue

            parts = line.split(" ", 2)
            cmd = parts[0].upper()
            if cmd not in ("READ", "GET", "PUT"):
                print(f"Invalid command: {line}")
                continue

            op = cmd[0]
            key = parts[1] if len(parts) > 1 else ""

            if op in ('R', 'G'):
                if len(parts) != 2 or len(key) > 999:
                    print(f"Invalid format: {line}")
                    continue
                size = 6 + len(key)
                if size > 999:
                    print(f"Message too long: {line}")
                    continue
                message = f"{size:03d} {op} {key}"

            elif op == 'P':
                if len(parts) < 3:
                    print(f"Missing value: {line}")
                    continue
                value = parts[2]
                if len(key) > 999 or len(value) > 999 or len(key + " " + value) > 970:
                    print(f"Key/value too long: {line}")
                    continue
                size = 7 + len(key) + len(value)
                if size > 999:
                    print(f"Message too long: {line}")
                    continue
                message = f"{size:03d} P {key} {value}"

            # send and receive
            sock.sendall(message.encode())
            size_bytes = receive_n(sock, 3)
            if len(size_bytes) < 3:
                print("Server disconnected")
                break
            total_size = int(size_bytes.decode())
            remaining = receive_n(sock, total_size - 3)
            response_buffer = size_bytes + remaining
            response = response_buffer.decode().strip()
            print(f"{line}: {response}")

    except (socket.error, ValueError) as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        sock.close()

if __name__ == "__main__":
    main()