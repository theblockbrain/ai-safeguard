# Normalize individual operations
# In case of a PUSH operation, `data_categories` is a list of strings describing how the immediate value is used
# The return value is the normalized string representation of the operation, including a newline
# unless the operation should be normalized out entirely, in that case it is an empty string
def normalize_op(op, data_categories):
    if op.name[:3] == "LOG": # Normalize LOG* operations to LOGX
        return "LOGX\n"
    elif op.name[:4] == "PUSH":
        # Normalize `PUSH* 0x...` to `PUSHX [Data|ArithData|...]`
        # If data_categories is available and contains exactly one usage type, we
        # normalize the immediate value to it, otherwise we normalize it to just "Data"
        cat_str = "Data"
        if data_categories != None:
            if len(data_categories) == 1:
                cat_str = data_categories[0]
        return "PUSHX " + cat_str + "\n"
    elif op.name[:3] == "DUP" or op.name[:4] == "SWAP" or op.name == "POP":
        # Eliminate all DUPs, SWAPs and POPs
        return ""
    else:
        # All other operations will be maintained as-is.
        return op.name + "\n"
