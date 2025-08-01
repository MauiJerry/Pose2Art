# In a Text DAT, set Execute DAT to run this once on startup or via its Run button.
# a self-contained Python snippet drop into a Text DAT in TouchDesigner
# (run it in the same network as the .toe you want to inspect). 
# It will recurse your entire component tree, 
# dump each operator’s path, type, and all parameter names+values, 
# and write it to a text file.

import os

def dump_touchdesigner_ops(rootCOMP, outPath):
    """
    rootCOMP : the COMP you want to start from (e.g. project1 or op('/'))
    outPath  : full filesystem path to write the dump.txt
    """
    # Ensure directory exists
    folder = os.path.dirname(outPath)
    if not os.path.isdir(folder):
        os.makedirs(folder)
    
    with open(outPath, 'w') as f:
        # Walk all descendants (including rootCOMP)
        for op in rootCOMP.walkChildren():
            # Header line
            f.write(f"Operator: {op.path}, Type: {op.opType}\n")
            # Write each parameter’s name and evaluated value
            for par in op.pars():
                try:
                    val = par.eval()
                except Exception as e:
                    val = f"<error: {e}>"
                f.write(f"    {par.name} = {val}\n")
            f.write("\n")

# Example usage:
# Dump entire project (root is project1) to a file
dump_touchdesigner_ops(op('project1'), r"C:\Users\YourName\Desktop\touch_dump.txt")

# Alternatively, to dump from the network’s root:
# dump_touchdesigner_ops(op('/'), r"C:\temp\td_ops_dump.txt")
