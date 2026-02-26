
import streamlit as st
import tempfile
from pathlib import Path

from notebook_runner import run_reliability_notebook, zip_dir

st.set_page_config(page_title="Dataset Reliability Evaluator", layout="wide")

st.title("Dataset 기반 평가 도구 (Reliability Test)")

st.markdown("""
이 도구는 **영상(mp4) + 라벨(json)** 파일들을 업로드하면, 내부에서 아래 구조를 자동으로 구성한 뒤
노트북 파일(`reliability_test.ipynb`)을 실행해서 `reports/` 결과물을 생성합니다.

자동 생성되는 구조:

```
aihub/raw/videos/*.mp4
aihub/raw/labels/*.json
```

> 권장: 영상/라벨 파일명을 1:1로 매칭할 수 있도록 동일한 베이스 이름 규칙을 유지하세요.
""")

st.subheader("1) 데이터 업로드 (드래그 앤 드롭)")

videos = st.file_uploader(
    "영상 파일들 (mp4) - 여러 개 선택/드래그 가능",
    type=["mp4"],
    accept_multiple_files=True
)

labels = st.file_uploader(
    "라벨 파일들 (json) - 여러 개 선택/드래그 가능",
    type=["json"],
    accept_multiple_files=True
)

if (not videos) or (not labels):
    st.info("영상(mp4)과 라벨(json)을 모두 업로드하면 실행 버튼이 활성화됩니다.")

st.subheader("2) 옵션")
col1, col2, col3 = st.columns(3)
with col1:
    max_videos = st.number_input("MAX_VIDEOS (0이면 전체)", min_value=0, value=0, step=1)
with col2:
    max_images_total = st.number_input("MAX_IMAGES_TOTAL (0이면 전체)", min_value=0, value=0, step=1)
with col3:
    skip_existing = st.checkbox("SKIP_EXISTING", value=True)

notebook_path = st.text_input(
    "노트북 파일 경로",
    value=str(Path(__file__).resolve().parent / "reliability_test.ipynb"),
    help="기본값은 현재 폴더에 있는 reliability_test.ipynb 입니다."
)

run_btn = st.button("3) 평가 실행", type="primary", disabled=(not videos or not labels))

if run_btn:
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)

        # Build dataset structure expected by the notebook
        base = tmp / "base"
        videos_dir = base / "aihub" / "raw" / "videos"
        labels_dir = base / "aihub" / "raw" / "labels"
        videos_dir.mkdir(parents=True, exist_ok=True)
        labels_dir.mkdir(parents=True, exist_ok=True)

        st.info("업로드 파일 저장 중...")
        # Write uploaded files to disk
        for vf in videos:
            (videos_dir / vf.name).write_bytes(vf.getvalue())
        for lf in labels:
            (labels_dir / lf.name).write_bytes(lf.getvalue())

        st.success(f"업로드 완료: videos={len(videos)}, labels={len(labels)}")

        mv = None if int(max_videos) == 0 else int(max_videos)
        mit = None if int(max_images_total) == 0 else int(max_images_total)

        st.info("노트북 실행 중... (환경에 따라 시간이 걸릴 수 있음)")
        log_box = st.empty()

        def on_log(line: str):
            state = st.session_state.get("_log_lines", [])
            state.append(line.rstrip("\n"))
            state = state[-250:]
            st.session_state["_log_lines"] = state
            log_box.code("\n".join(state), language="text")

        try:
            reports_dir = run_reliability_notebook(
                notebook_path=Path(notebook_path),
                base_dir=base,
                max_videos=mv,
                max_images_total=mit,
                skip_existing=bool(skip_existing),
                on_log=on_log,
            )
        except Exception as e:
            st.exception(e)
            st.stop()

        st.success(f"완료: {reports_dir}")

        report_md = Path(reports_dir) / "report.md"
        if report_md.exists():
            st.subheader("요약 리포트 (report.md)")
            st.markdown(report_md.read_text(encoding="utf-8", errors="replace"))

        out_zip = tmp / "reports.zip"
        zip_dir(Path(reports_dir), out_zip)

        st.download_button(
            "reports.zip 다운로드",
            data=out_zip.read_bytes(),
            file_name="reports.zip",
            mime="application/zip"
        )

        st.subheader("생성된 파일 목록")
        files = sorted([p.relative_to(reports_dir).as_posix() for p in Path(reports_dir).rglob("*") if p.is_file()])
        st.code("\n".join(files), language="text")
