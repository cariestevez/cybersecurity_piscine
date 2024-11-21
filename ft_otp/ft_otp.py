import os
import argparse
from datetime import datetime
from cryptography.fernet import Fernet
import hashlib
import hmac
from colorama import init, Fore
import base64

init(autoreset=True)

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
    with open("seed.key", "wb") as key_file:
        key_file.write(key)

#---------------------------------------------------------------------------------------------------------------

# Load the symmetric key
def load_key():
    return open("seed.key", "rb").read()

def save_encrypted_key(key, output_file="ft_otp.key"):
    seed = load_key()
    #initilaizes the Fernet class with the key
    f = Fernet(seed)
    encrypted_data = f.encrypt(key)

    # base32_key = base64.b32encode(encrypted_data)

    with open(output_file, "wb") as file:
        file.write(encrypted_data)

    print(Fore.LIGHTGREEN_EX + f"Key saved securely in {output_file}")

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

def validate_hex_key(key):
    print("Validating key...")
    
    # Remove spaces, newlines, and other non-hex characters
    clean_key = b''.join(key.split())  # Removes whitespace from bytes
    
    # Ensure the cleaned key is valid hex
    if len(key) % 2 != 0:
        raise ValueError("Input must have an even number of characters (full bytes).")
    try:
        int(clean_key.decode(), 16)  # Check if it's a valid hex string
    except ValueError:
        raise ValueError("Key must be a hexadecimal string.")
    
    if len(clean_key) < 64:
        raise ValueError("Key must be at least 64 characters long (after cleaning).")
    
    print(Fore.LIGHTGREEN_EX + "Key is valid.")
    return clean_key

#---------------------------------------------------------------------------------------------------------------

def decrypt(filename, seed):
    f = Fernet(seed)
    if os.path.exists(filename):
        if not os.access(filename, os.R_OK):
            raise PermissionError("Master key file is not readable.")
    with open(filename, "rb") as file:
        encrypted_data = file.read().strip()
    decrypted_data = f.decrypt(encrypted_data)
    # print(Fore.LIGHTGREEN_EX + f"Master key decrypted: {decrypted_data}")
    # Decode the decrypted base32 string to get the original key
    # try:
    # print("Before decoding")
    # decoded_key = base64.b32decode(decrypted_data)
    # print("After decoding")
    #base32_key = base64.b32encode(encrypted_data).decode('utf-8')
    # except ValueError as e:
    #     raise ValueError(f"Invalid base32 encoding: {e}")

    return decrypted_data

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
    print(Fore.LIGHTMAGENTA_EX + f"Master key: {master_key}")
    #decoded_key = master_key.decode()
    # print(Fore.LIGHTMAGENTA_EX + f"Master key decoded: {decoded_key}")
    secret_bytes = bytes.fromhex(master_key.decode())
    #print(Fore.LIGHTMAGENTA_EX + f"Master key decrypted: {master_key}")
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
    #check the passed file is ft_otp.key
    if key_file != "ft_otp.key":
        raise ValueError("Invalid master key file.")
    #read the key from the file & decrypt it
    master_key = decrypt(key_file, load_key())
    print(Fore.CYAN + f"Master key decrypted: {master_key}")
    # if not validate_hex_key(master_key):
    #     raise ValueError("Invalid master key.")
    totp = generate_totp(master_key)
    print(Fore.LIGHTCYAN_EX + f"TOTP: {totp}")

def main():
    #generate_symmetric_key()
    parser = argparse.ArgumentParser(description="TOTP Generator", usage="%(prog)s [-h] [-g KEY_FILE or KEY_STRING] [-k MASTER_KEY_FILE]")
    parser.add_argument("-g", help="Generate and store an encrypted master key", type=str)
    parser.add_argument("-k", help="Generate a TOTP using the stored master key", type=str)

    args = parser.parse_args()

    try:
        if args.g:
            print(Fore.GREEN + "Generating master key...")
            process_g_option(args.g)

        elif args.k:
            print(Fore.CYAN + f"Generating OTP using key file: {args.k}")
            process_k_option(args.k)
        else:
            parser.print_help()
    except Exception as e:
        print(Fore.RED + f"Error: {e}")
        # sys.exit(1)  # Exit with an error code

if __name__ == "__main__":
    main()