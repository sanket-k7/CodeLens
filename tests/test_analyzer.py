from analyzer.code_analyzer import analyze_file


file_path = "backend/main.py"


result = analyze_file(file_path)


print("\n===== CodeLens Analysis =====\n")

print("File:")
print(result["file"])

print("\nLanguage:")
print(result["language"])

print("\nLines:")
print(result["lines"])

print("\nClasses:")
for class_name in result["classes"]:
    print(" -", class_name)

print("\nFunctions:")
for function_name in result["functions"]:
    print(" -", function_name)

print("\nImports:")
for import_name in result["imports"]:
    print(" -", import_name)