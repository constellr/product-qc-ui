import fsspec

fs_pt = fsspec.filesystem("s3", profile="ProductTest")
fs_sp = fsspec.filesystem("s3", profile="SoftwareProduction")


def copy_file(source_path, destination_path):
    with fsspec.open(source_path, mode='rb', profile='ProductTest') as source_file:
        with fsspec.open(destination_path, mode='wb', profile='SoftwareProduction') as destination_file:
            destination_file.write(source_file.read())

