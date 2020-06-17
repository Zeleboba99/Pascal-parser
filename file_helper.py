class FileHelper:

    @staticmethod
    def write_to_file(filename, content):
        f = open(filename, "w")
        f.write(content)
        f.close()

    @staticmethod
    def read_from_file(filename) -> str:
        f = open(filename, "r")
        return f.read()
