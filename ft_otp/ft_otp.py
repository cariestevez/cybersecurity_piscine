import os
import argparse
from datetime import datetime
from cryptography.fernet import Fernet
import hashlib
import hmac
from colorama import init, Fore
import base64
import sys
import subprocess

init(autoreset=True)

# Using symmetric encryption: same key used to encrypt data is also usable for decryption.
# The fernet library is built on top of the AES algorithm.

# Encryption: you can retrieve the original data once you have the key
# vs Hashing functions: you cannot-> one-way encryption.

#---------------------------------------------------------------------------------------------------------------

# --> this should be a separate script executed only once to generate the seed used to encrypt the master key to be stored in ft_otp.key
def generate_symmetric_key():
    key = Fernet.generate_key()
    with open("seed.key", "wb") as key_file:
        key_file.write(key)
    if not os.path.exists("seed.key"):
        raise OSError(f"File to store the seed couldn't be created.")
    print(Fore.LIGHTYELLOW_EX + f"Seed generated and successfully saved.")

#---------------------------------------------------------------------------------------------------------------

def generate_key_with_openssl(script_path="./hex_string_generator.sh"):
    try:
        subprocess.run(["bash", script_path], check=True)
        print(Fore.LIGHTMAGENTA_EX + "Key generated using OpenSSL and saved to key.hex")
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error executing the script: {e}")

#---------------------------------------------------------------------------------------------------------------

# Load the seed used for encryption of the master key
def load_seed():
    return open("seed.key", "rb").read()

#---------------------------------------------------------------------------------------------------------------

def save_encrypted_key(key, output_file="ft_otp.key"):
    try:
        seed = load_seed()
        f = Fernet(seed)
        encrypted_data = f.encrypt(key)

        with open(output_file, "wb") as file:
            file.write(encrypted_data)

        print(Fore.LIGHTGREEN_EX + f"Key saved securely in {output_file}")
    except Exception as e:
        raise Exception(f"Error saving the key: {e}")

def validate_hex_key(key):

    clean_key = b''.join(key.split())
    if len(clean_key) % 2 != 0:
        raise ValueError("Input must have an even number of characters (full bytes).")
    try:
        int(clean_key.decode(), 16)
    except ValueError:
        raise ValueError("Key must be a hexadecimal string.")
    
    if len(clean_key) < 64:
        raise ValueError("Key must be at least 64 characters long.")
    
    print(Fore.LIGHTGREEN_EX + "Key is valid.")
    return clean_key

def process_g_option(input_value):

    if os.path.exists(input_value) & os.path.isfile(input_value):
        if not os.access(input_value, os.R_OK):
            raise PermissionError("File is not readable.")
        with open(input_value, "rb") as file:
            key = file.read()
    else:
        raise ValueError("No key provided")
    clean_key = validate_hex_key(key)
    save_encrypted_key(clean_key)

#---------------------------------------------------------------------------------------------------------------

# def hmac_sha1(key, message):
#     # Block size for SHA1 is 64 bytes
#     block_size = 64

#     # Step 1: Adjust key length
#     # Hash key if longer than block size
#     if len(key) > block_size:
#         key = hashlib.sha1(key).digest()
#     # Pad key with zeros to make it block_size bytes long
#     if len(key) < block_size:
#         key = key.ljust(block_size, b'\x00')

#     # Step 2: Create inner and outer padded keys
#     ipad = bytes((x ^ 0x36) for x in key)
#     opad = bytes((x ^ 0x5C) for x in key)

#     # Step 3: Calculate inner hash
#     inner_hash = hashlib.sha1(ipad + message).digest()

#     # Step 4: Calculate final HMAC
#     hmac_result = hashlib.sha1(opad + inner_hash).digest()

#     return hmac_result

def generate_totp(master_key):
    
    time_interval = 30
    # converts the time to a 64-bit counter value (number of 30-second intervals since Unix epoch)
    time_counter = int(datetime.now().timestamp() / time_interval)
    # converts the secret key (passed as string) to bytes
    secret_bytes = bytes.fromhex(master_key.decode())
    # generates HMAC-SHA-1 hash with the master key and the current time converted to 8byte big endian value
    hmac_hash = hmac.new(secret_bytes, time_counter.to_bytes(8, byteorder="big"), hashlib.sha1).digest()
    # hmac_hash = hmac_sha1(secret_bytes, time_counter.to_bytes(8, byteorder="big"))
    # applies dynamic truncation to obtain a 4-byte code, extracting 4 bytes starting at the offset
    offset = hmac_hash[-1] & 0x0F
    truncated_bytes = hmac_hash[offset:offset+4]
    # converts the 4 bytes to a 32-bit integer (big-endian)
    truncated_hash = 0
    # shifts left and adds the next byte
    for byte in truncated_bytes:
        truncated_hash = (truncated_hash << 8) | byte
    # ignores the most significant bit to ensure it's positive
    truncated_hash &= 0x7FFFFFFF
    # converts the 4-byte code to a 6-digit decimal code taking the binary code modulo 10^6
    otp = truncated_hash % 10**6
    return otp

def decrypt(encrypted_data, seed):
    try:

        f = Fernet(seed)
        decrypted_data = f.decrypt(encrypted_data)
    except Exception as e:
        raise Exception(f"Error decrypting the key: {e}")

    return decrypted_data

# assumes the decrypted master key is a valid hexadecimal string
def process_k_option(key_file):

    if key_file != "ft_otp.key":
        raise ValueError("Invalid master key file.")
    
    if os.path.exists(key_file) & os.path.isfile(key_file):
        if not os.access(key_file, os.R_OK):
            raise PermissionError("Master key file is not readable.")
    with open(key_file, "rb") as file:
        encrypted_data = file.read().strip()

    master_key = decrypt(encrypted_data, load_seed())

    totp = generate_totp(master_key)
    totp_str = str(totp).zfill(6)
    print(Fore.LIGHTCYAN_EX + f"TOTP: {totp_str}")

#---------------------------------------------------------------------------------------------------------------

def main():

    parser = argparse.ArgumentParser(description="TOTP Generator", usage="%(prog)s [-h] [-g KEY_FILE or KEY_STRING] [-k MASTER_KEY_FILE]")
    parser.add_argument("-g", help="Generate and store an encrypted master key", type=str)
    parser.add_argument("-k", help="Generate a TOTP using the stored master key", type=str)
    parser.add_argument("-s", help="Generate a symmetric key (seed) for master key encription. Make sure to store it safely! File will be overwritten when executing again with -s flag.", action="store_true")
    parser.add_argument("-m", help="Generate a random hexadecimal key using OpenSSL", action="store_true")

    args = parser.parse_args()

    try:
        if args.g:
            print(Fore.GREEN + "Storing encrypted master key...")
            process_g_option(args.g)

        elif args.k:
            print(Fore.CYAN + f"Generating TOTP using encrypted key in file: {args.k}.")
            process_k_option(args.k)
        elif args.s:
            print(Fore.YELLOW + "Generating symmetric key...")
            generate_symmetric_key()
        elif args.m:
            print(Fore.MAGENTA + "Generating random hexadecimal key for you...")
            generate_key_with_openssl()
        else:
            parser.print_help()
    except ValueError as e:
        print(Fore.RED + f"Validation error: {e}")
        sys.exit(1)
    except PermissionError as e:
        print(Fore.RED + f"Permission error: {e}")
        sys.exit(1)
    except OSError as e:
        print(Fore.RED + f"OS Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(Fore.RED + f"Exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()