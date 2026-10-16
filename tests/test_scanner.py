from analyzer.file_scanner import scan_repository


repository_path = "."


files = scan_repository(repository_path)


print("Files found:")

for file in files:
    print(file)