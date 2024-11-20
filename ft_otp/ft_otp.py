import os
import argparse
from datetime import datetime
from cryptography.fernet import Fernet
import hashlib
import hmac

# Using symmetric encryption: same key used to encrypt data is also usable for decryption.
# The fernet library is built on top of the AES algorithm.

# Encryption: you can retrieve the original data once you have the key
# vs Hashing functions: you cannot-> one-way encryption.

#---------------------------------------------------------------------------------------------------------------
# --> this goes into a separate script execute only once to generate an encryption key that will be used to encrypt the master key
# problem: how to securely store the key? env?
# solution: generate and save a symmetric key once before you run the program and just hardcode it in here
def generate_symmetric_key():
    key = Fernet.generate_key()  # Save this securely, e.g., in an environment variable
    with open("encryption.key", "wb") as key_file:
        key_file.write(key)

# Load the symmetric key
def load_key():
    return open("encryption.key", "rb").read()

#---------------------------------------------------------------------------------------------------------------

def save_encrypted_key(key, output_file="ft_otp.key"):
    encryption_key = load_key()
    #initilaizes the Fernet class with the key
    f = Fernet(encryption_key)
    #encode converts python str to bytes to make suitable for encryption
    encrypted_data = f.encrypt(key.encode())
    with open(output_file, "rb") as file:
        file.write(encrypted_data)
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
    else:
        key = input_value.strip()
    validate_hex_key(key)
    save_encrypted_key(key)

#---------------------------------------------------------------------------------------------------------------

def decrypt(filename, key):
    f = Fernet(key)
    if os.path.exists(filename):
        if not os.access(filename, os.R_OK):
            raise PermissionError("Master key file is not readable.")
    with open(filename, "rb") as file:
        encrypted_data = file.read()
    decrypted_data = f.decrypt(encrypted_data)
    return decrypted_data.decode()

def hmac_sha1(key, message):
    # Block size for SHA1 is 64 bytes
    block_size = 64

    # Step 1: Adjust key length
    if len(key) > block_size:
        key = hashlib.sha1(key).digest()  # Hash key if longer than block size
    if len(key) < block_size:
        key = key.ljust(block_size, b'\x00')  # Pad key with zeros to make it block_size

    # Step 2: Create inner and outer padded keys
    ipad = bytes((x ^ 0x36) for x in key)
    opad = bytes((x ^ 0x5C) for x in key)

    # Step 3: Calculate inner hash
    inner_hash = hashlib.sha1(ipad + message).digest()

    # Step 4: Calculate final HMAC
    hmac_result = hashlib.sha1(opad + inner_hash).digest()

    return hmac_result

def generate_totp(master_key):
    time_interval = 30 # seconds
    #convert the time to a 64-bit counter value (number of 30-second intervals since Unix epoch):
    time_counter = int(datetime.now().timestamp() / time_interval)
    # Convert the secret key to bytes:
    secret_bytes = bytes.fromhex(master_key)
    # same as secret_bytes = base64.b32decode(master_key)??
    #generate HMAC-SHA-1 hash with the master key and the current time converted to 8byte big endian value:
    #hmac_hash = hmac.new(secret_bytes, time_counter.to_bytes(8, byteorder="big"), hashlib.sha1).digest()
    hmac_hash = hmac_sha1(secret_bytes, time_counter.to_bytes(8, byteorder="big"))
    # Apply dynamic truncation
    offset = hmac_hash[-1] & 0x0F  # Use the last byte of the HMAC to get the offset
    truncated_bytes = hmac_hash[offset:offset+4]  # Extract 4 bytes starting at the offset
    # Convert 4 bytes to a 32-bit integer (big-endian)
    truncated_hash = 0
    for byte in truncated_bytes:
        truncated_hash = (truncated_hash << 8) | byte  # Shift left and add the next byte
    truncated_hash &= 0x7FFFFFFF  # Ignore the most significant bit to ensure it's positive
    #convert the 4-byte code to a 6-digit decimal code taking the binary code modulo 10^6
    otp = truncated_hash % 10**6  # 6 digits
    return otp

def process_k_option(key_file):
    print(f"Generating OTP using key file: {key_file}")
    #check the passed file is ft_otp.key
    if key_file != "ft_otp.key":
        raise ValueError("Invalid master key file.")
    #read the key from the file & decrypt it
    master_key = decrypt(key_file, load_key())
    if not validate_hex_key(master_key):
        raise ValueError("Invalid master key.")
    print(f"TOTP: {generate_totp(master_key)}")

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