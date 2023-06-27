import binascii
import os
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter

def initialize_firebase():
    try:
        firebase_cred = credentials.Certificate(os.environ.get('FIREBASE_CONFIG'))
        if not firebase_admin._apps:
            firebase_admin.initialize_app(firebase_cred)
        global db
        db = firestore.client()
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        exit(1)

def resolve_sigs(bytecode):
    ops = []

    # basic parsing of evm bytecode
    pos = 0
    while pos < len(bytecode):
        op = {}
        # check if the op is a PUSH
        if bytecode[pos] >= 0x60 and bytecode[pos] <= 0x7f:
            if pos+2+int(bytecode[pos]-0x60) > len(bytecode):
                # A push that implies data beyond the end of the bytecode.
                break
            op["Opcode"] = bytecode[pos]
            op["IsPush"] = True
            op["arg"] = bytecode[pos+1 : pos+2+int(bytecode[pos]-0x60)]
            pos += int(bytecode[pos]-0x60) + 1
        else:
            op["Opcode"] = bytecode[pos]
            op["IsPush"] = False
            op["arg"] = b''
        ops.append(op)
        pos += 1

    # search for specific pattern containing the function selector
    selectors = []
    for offset in range(len(ops) - 4):
        # 0x14 = EQ
        # 0x57 = JUMPI
        if ops[offset]["IsPush"] and ops[offset+1]["Opcode"] == 0x14 and ops[offset+2]["IsPush"] and ops[offset+3]["Opcode"] == 0x57:
            selector = ops[offset]["arg"]
            if len(selector) > 4:
                # the pattern must have been misinterpreted, selectors can't be
                # larger than four bytes
                continue
            while len(selector) < 4:
                selector = b'\x00' + selector
            selectors.append(selector)

    signatures = []
    for selector in selectors:
        try:
            name, err = resolve_sig(selector)
            if err is not None:
                print(f"Error resolving signature: {err}")
                continue
            signatures.append((binascii.hexlify(selector).decode(), name))
        except Exception as e:
            print(f"Error processing selector: {e}")
            continue

    return signatures

def resolve_sig(bin_sig):
    try:
        sigs_ref = db.collection(u'Signature')
        sigs = sigs_ref.where(filter=FieldFilter(u'Code', u'==', binascii.hexlify(bin_sig).decode())).stream()
        for sig in sigs:
            return sig.to_dict()['Signature'], None
        print(f"Signature for selector {binascii.hexlify(bin_sig).decode()} not found in Firestore.")
        return "Not found", None
    except Exception as e:
        print(f"Error querying Firestore: {e}")
        return None, e

# get the function signatures of a contract
def get_signatures(bytecode):
    initialize_firebase()
    try:
        bytecode = bytes.fromhex(bytecode)
    except Exception as e:
        print(f"Error processing bytecode: {e}")
        exit(1)

    return resolve_sigs(bytecode)