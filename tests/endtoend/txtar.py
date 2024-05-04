import typing
import io
import zipfile


def parse(input: str) -> typing.Dict[str, str]:
    """Parse a txtar string into a map from file name to content."""
    m: typing.Dict[str, str] = {}
    current_file: typing.Optional[str] = None
    for line in input.splitlines():
        line = line.strip()
        file_name = line.removeprefix("-- ").removesuffix(" --")
        # We compare the lengths to check the prefix and suffix we're removed.
        if len(file_name) + 6 == len(line):
            file_name = file_name.strip()
            if file_name != "":
                current_file = file_name
                m[current_file] = ""
                continue
        if current_file is None:
            continue
        m[current_file] = m[current_file] + line + "\n"
    return m


def to_zip(input: str) -> bytes:
    """Converts a txtar string to a zip archive containing the files."""
    output_bytes = io.BytesIO()
    with zipfile.ZipFile(output_bytes, "w") as zip_file:
        for file_name, content in parse(input).items():
            zip_file.writestr(file_name, content)
    return output_bytes.getvalue()
