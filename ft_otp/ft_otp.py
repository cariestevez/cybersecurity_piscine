import os
import argparse
from datetime import datetime
import hashlib

def save_key_securely(key, output_file="ft_otp.key"):
    # Hash the key using SHA-256 for simplicity
    hashed_key = hashlib.sha256(key.encode()).hexdigest()

    with open(output_file, "w") as file:
        file.write(hashed_key)

    # Set file permissions (readable only by the user)
    os.chmod(output_file, 0o400)
    print(f"Key saved securely in {output_file}")

def validate_hex_key(key):
    if len(key) < 64:
        raise ValueError("Key must be at least 64 characters long.")
    if not all(c in "0123456789abcdefABCDEF" for c in key):
        raise ValueError("Key must be a hexadecimal string.")
    return True


def process_g_option(input_value):
    if os.path.exists(input_value):
        if not os.access(input_value, os.R_OK):
            raise PermissionError("File is not readable.")
        with open(input_value, "r") as file:
            key = file.read().strip()
    else:  # If it's a string
        key = input_value.strip()

    validate_hex_key(key)
    save_key_securely(key)

def process_k_option(key_file):
    print(f"Generating OTP using key file: {key_file}")
    #read the key from the file
        #check permissions, open & read
    #decrypt the key?
        #un-hash the key using SHA-256
        #check if the key is valid (64 characters long, hexadecimal)
    #implement HOTP algorithm combining with time based counter to derive the TOTP
        #generate HMAC-SHA-1 hash with the master key and the current time
            #convert the time to a 64-bit counter value (number of 30-second intervals since Unix epoch)
            #-> counter = current unix time / time step (where time step = 30 seconds)
        #truncate the result to 6 digits extracting a 4-byte dynamic binary code from the HMAC result (dynamic truncation)
        #convert the 4-byte code to a 6-digit decimal code taking the binary code modulo 10^6
    #print the TOTP to the user

def main():
    parser = argparse.ArgumentParser(description="TOTP Generator", usage="%(prog)s [-h] [-g KEY_FILE or KEY_STRING] [-k MASTER_KEY_FILE]")
    parser.add_argument("-g", help="Generate and store an encrypted master key", type=str)
    parser.add_argument("-k", help="Generate a TOTP using the stored master key", type=str)

    args = parser.parse_args()

    try:
        if args.g:
            print(f"Generating master key from: {args.g}")
            process_g_option(args.g)

        elif args.k:
            print(f"Generating OTP using key file: {args.k}")
            process_k_option(args.k)
        else:
            parser.print_help()
    except Exception as e:
        print(f"Error: {e}")
        # sys.exit(1)  # Exit with an error code

if __name__ == "__main__":
    main()