import sys
sys.path.insert(0, "E:/NEMT Simulator")
import matlab.engine

# Test correct API
print("Testing start_matlab() API...")
eng = matlab.engine.start_matlab()
print("MATLAB engine started!")

# Test simple calculation
print("\nTesting simple calculation...")
result = eng.eval("1 + 2")
print(f"1 + 2 = {result}")

# Test variable assignment
print("\nTesting variable assignment...")
eng.eval("a = 5 * 3", nargout=0)
a_value = eng.workspace["a"]
print(f"a = {a_value}")

# Test disp
print("\nTesting disp...")
eng.eval("disp('Hello from MATLAB!')", nargout=0)

# Stop engine
eng.quit()
print("\nAll tests passed!")
