
from __future__ import annotations
from pathlib import Path
from typing import Callable, Optional
import re
import io
import contextlib

def _patch_notebook_source(nb_text: str, base_dir: Path,
                           max_videos: Optional[int],
                           max_images_total: Optional[int],
                           skip_existing: bool) -> str:
    """
    노트북을 최대한 '그대로' 재사용하기 위해,
    실행 전에 몇 개의 상수(BASE, MAX_VIDEOS, MAX_IMAGES_TOTAL, SKIP_EXISTING)를 지정한 값으로 치환합니다.
    """
    base_dir = Path(base_dir).resolve()

    # BASE = Path("/content") 같은 라인을 교체
    nb_text = re.sub(
        r'BASE\s*=\s*Path\(["\'].*?["\']\)',
        f'BASE = Path(r"{base_dir.as_posix()}")',
        nb_text
    )

    def _replace_int_or_none(txt: str, var: str, val: Optional[int]) -> str:
        repl = "None" if val is None else str(int(val))
        return re.sub(rf'^{var}\s*=\s*.*$', f"{var} = {repl}", txt, flags=re.M)

    nb_text = _replace_int_or_none(nb_text, "MAX_VIDEOS", max_videos)
    nb_text = _replace_int_or_none(nb_text, "MAX_IMAGES_TOTAL", max_images_total)
    nb_text = re.sub(r'^SKIP_EXISTING\s*=\s*.*$', f"SKIP_EXISTING = {str(bool(skip_existing))}", nb_text, flags=re.M)
    return nb_text

def run_reliability_notebook(
    notebook_path: Path,
    base_dir: Path,
    max_videos: Optional[int] = None,
    max_images_total: Optional[int] = None,
    skip_existing: bool = True,
    on_log: Optional[Callable[[str], None]] = None,
) -> Path:
    """
    reliability_test.ipynb 를 실행해서 base_dir/reports 를 생성하고, 그 경로를 반환합니다.
    - notebook_path: 팀원이 만든 ipynb
    - base_dir: 데이터셋이 풀려있는 루트 (aihub/raw/... 가 이 아래 있어야 함)
    """
    notebook_path = Path(notebook_path)
    if not notebook_path.exists():
        raise FileNotFoundError(f"Notebook not found: {notebook_path}")

    nb_text = notebook_path.read_text(encoding="utf-8", errors="replace")
    nb_text = _patch_notebook_source(
        nb_text=nb_text,
        base_dir=base_dir,
        max_videos=max_videos,
        max_images_total=max_images_total,
        skip_existing=skip_existing,
    )

    try:
        import nbformat
        from nbclient import NotebookClient
    except Exception as e:
        raise RuntimeError("nbformat/nbclient 가 필요합니다. 설치: pip install nbformat nbclient") from e

    nb = nbformat.reads(nb_text, as_version=4)
    client = NotebookClient(nb, timeout=None, kernel_name="python3")

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        client.execute()

    if on_log:
        for line in buf.getvalue().splitlines():
            on_log(line + "\n")

    reports_dir = Path(base_dir) / "reports"
    if not reports_dir.exists():
        raise RuntimeError(f"reports 디렉토리가 생성되지 않았습니다. 예상 경로: {reports_dir}")
    return reports_dir

def zip_dir(src_dir: Path, out_zip: Path) -> Path:
    import zipfile
    src_dir = Path(src_dir)
    out_zip = Path(out_zip)
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in src_dir.rglob("*"):
            if p.is_file():
                z.write(p, arcname=p.relative_to(src_dir).as_posix())
    return out_zip
