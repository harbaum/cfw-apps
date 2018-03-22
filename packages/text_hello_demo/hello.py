import time, sys

print("Hello World!");
a = 12 + 13
print("12 + 13 is", a);

# small progress bar like thing
length=20
for i in range(length):
    print("\r", end="")
    print("[", end="")
    print("#"*i, end="")
    print("-"*(length-1-i), end="")
    print("] ", end="")
    print(str(int(i*100/(length-1)))+"%", end="")
    sys.stdout.flush()
    time.sleep(5/length)   # 5 seconds

print("")
    
print("")
print("You can replace hello.py with any simple python3 script you like.")
print("You can even rename it.")
print("")
print("Don't forget to change the UUID in the manifest file if you plan")
print("to distribute your program.")
