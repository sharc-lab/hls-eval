import io
import tarfile
from pathlib import Path


def copy_file_to_container(container, src: Path, dst_dir: str) -> None:
    """
    Copy a file from anywhere on the host into an existing directory
    inside a Docker container.

    dst_dir: path inside the container (str)
    """
    src = src.expanduser().resolve()

    if not src.is_file():
        raise ValueError(f"Source is not a file: {src}")

    tar_stream = io.BytesIO()

    with tarfile.open(fileobj=tar_stream, mode="w") as tar:
        tar.add(str(src), arcname=src.name)

    tar_stream.seek(0)
    container.put_archive(dst_dir, tar_stream)


def copy_dir_to_container(
    container,
    src_dir: Path,
    dst_dir: str,
    copy_contents: bool = False,
) -> None:
    """
    Copy a directory from anywhere on the host into an existing directory
    inside a Docker container.

    dst_dir: path inside the container (str)

    If copy_contents=False:
        /host/data -> /container/dst/data/...

    If copy_contents=True:
        /host/data/* -> /container/dst/...
    """
    src = src_dir.expanduser().resolve()

    if not src.is_dir():
        raise ValueError(f"Source is not a directory: {src}")

    tar_stream = io.BytesIO()

    with tarfile.open(fileobj=tar_stream, mode="w") as tar:
        if copy_contents:
            for item in src.iterdir():
                tar.add(str(item), arcname=item.name)
        else:
            tar.add(str(src), arcname=src.name)

    tar_stream.seek(0)
    container.put_archive(dst_dir, tar_stream)


def copy_file_from_container(container, src: str, dst_dir: Path) -> None:
    """
    Copy a single file from inside a Docker container to a directory on the host.

    src: path inside the container (str)
    """
    dst_dir = dst_dir.expanduser().resolve()
    dst_dir.mkdir(parents=True, exist_ok=True)

    bits, _ = container.get_archive(src)

    tar_stream = io.BytesIO()
    for chunk in bits:
        tar_stream.write(chunk)
    tar_stream.seek(0)

    with tarfile.open(fileobj=tar_stream) as tar:
        members = tar.getmembers()
        if not members:
            raise ValueError(f"No content found at container path: {src}")
        member = members[0]
        member.name = Path(member.name).name
        tar.extract(member, path=str(dst_dir))


def copy_dir_from_container(
    container,
    src_dir: str,
    dst_dir: Path,
    copy_contents: bool = False,
) -> None:
    """
    Copy a directory from inside a Docker container to a directory on the host.

    src_dir: path inside the container (str)

    If copy_contents=False:
        /container/data -> /host/dst/data/...

    If copy_contents=True:
        /container/data/* -> /host/dst/...
    """
    dst_dir = dst_dir.expanduser().resolve()
    dst_dir.mkdir(parents=True, exist_ok=True)

    bits, _ = container.get_archive(src_dir)

    tar_stream = io.BytesIO()
    for chunk in bits:
        tar_stream.write(chunk)
    tar_stream.seek(0)

    with tarfile.open(fileobj=tar_stream) as tar:
        if copy_contents:
            src_prefix = Path(src_dir).name + "/"
            for member in tar.getmembers():
                rel = member.name
                if rel.startswith(src_prefix):
                    member.name = rel[len(src_prefix) :]
                elif rel == Path(src_dir).name:
                    continue
                if member.name:
                    tar.extract(member, path=str(dst_dir))
        else:
            tar.extractall(path=str(dst_dir))
