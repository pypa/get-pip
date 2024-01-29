# Import necessary modules
import io
import re
from zipfile import ZipFile, ZipInfo
from pathlib import Path

# Function to update all get-pip.py scripts
def update_get_pip_scripts():
    # Version check - 0 means "don't check"
    major = 0
    minor = 0

    # Open the original wheel file
    with ZipFile(io.BytesIO(original_wheel)) as src:
        for info in src.infolist():
            # Ignore all content apart from the "pip" subdirectory
            if info.filename.startswith("pip/"):
                data = src.read(info)
                dest.writestr(info, data)
            # Check Python version requirement from .dist-info/METADATA file
            elif info.filename.endswith(".dist-info/METADATA"):
                data = bytes_to_json(src.read(info))
                if "requires_python" in data:
                    py_req = data["requires_python"]
                    py_req = py_req.replace(" ", "")
                    m = re.match(r"^>=(\d+)\.(\d+)$", py_req)
                    if m:
                        major, minor = map(int, m.groups())
                        console.log(f"  Zipapp requires Python {py_req}")
                    else:
                        console.log(f"  Python requirement {py_req} too complex - check skipped")

    # Write the main script
    main_info = ZipInfo()
    main_info.filename = "__main__.py"
    main_info.create_system = 0
    template = Path("templates") / "zipapp_main.py"
    zipapp_main = template.read_text(encoding="utf-8").format(major=major, minor=minor)
    dest.writestr(main_info, zipapp_main)

# Main function
def main():
    console = Console()

    # Fetch all available pip versions
    with console.status("Fetching pip versions..."):
        pip_versions = get_all_pip_versions()
        console.log(f"Found {len(pip_versions)} available pip versions.")
        console.log(f"Latest version: {max(pip_versions)}")

    # Generate scripts based on predefined script constraints
    with console.status("Generating scripts...") as status:
        for variant, mapping in populated_script_constraints(SCRIPT_CONSTRAINTS):
            status.update(f"Working on [magenta]{variant}")
            console.log(f"[magenta]{variant}")
            generate_one(variant, mapping, console=console, pip_versions=pip_versions)

    # Generate 'moved' scripts
    if MOVED_SCRIPTS:
        console.log("[magenta]Generating 'moved' scripts...")
        with console.status("Generating 'moved' scripts...") as status:
            for legacy, current in MOVED_SCRIPTS.items():
                status.update(f"Working on [magenta]{legacy}")
                generate_moved(legacy, console=console, location=current)

    # Generate zipapp with the maximum pip version
    with console.status("Generating zipapp...") as status:
        generate_zipapp(max(pip_versions), console=console, pip_versions=pip_versions)

# Run the main function
if __name__ == "__main__":
    main()
