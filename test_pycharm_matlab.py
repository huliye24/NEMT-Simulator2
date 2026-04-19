import sys
sys.path.insert(0, "E:/NEMT Simulator")

from pycharm_mcp_server import (
    get_matlab_info,
    call_matlab_engine,
    eval_matlab_expression,
    get_matlab_variable,
    set_matlab_variable,
    list_matlab_variables
)

print("=== Test 1: matlab_info ===")
result = get_matlab_info()
print(result)

print("\n=== Test 2: matlab_eval('1 + 2') ===")
result = eval_matlab_expression("1 + 2")
print(result)

print("\n=== Test 3: matlab_execute('b = 10 * 2') ===")
result = call_matlab_engine("b = 10 * 2")
print(result)

print("\n=== Test 4: matlab_get_variable('b') ===")
result = get_matlab_variable("b")
print(result)

print("\n=== Test 5: matlab_set_variable('c', 42) ===")
result = set_matlab_variable("c", 42)
print(result)

print("\n=== Test 6: matlab_list_variables ===")
result = list_matlab_variables()
print(result)

print("\nAll tests completed!")
