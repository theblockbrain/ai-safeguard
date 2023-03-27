import psycopg2
import binascii

def resolve_sigs(conn, bytecode):
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
        name, err = resolve_sig(conn, selector)
        if err is not None:
            return [], err
        signatures.append(name)

    return signatures, None

# resolve a function selector to a function name
def resolve_sig(conn, bin_sig):
    cur = conn.cursor()
    cur.execute("SELECT Signature FROM signatures WHERE Code = %s", (psycopg2.Binary(bin_sig),))
    rows = cur.fetchall()
    if len(rows) > 0:
        return rows[0][0], None
    else:
        return "0x" + binascii.hexlify(bin_sig).decode(), None

# get the function signatures of a contract
def get_signatures(bytecode):
    try:
        conn = psycopg2.connect(database="signatures", user="postgres", password="derderndrbnr", host="localhost", port="5432")
    except:
        print("I am unable to connect to the database")
        exit(1)

    bytecode = bytes.fromhex(bytecode)
    signatures, err = resolve_sigs(conn, bytecode)
    if err is not None:
        print(err)
        exit(1)
    return signatures