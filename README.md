
# Dataset Reliability Evaluator (WebUI) - Drag & Drop

## What this is
- 팀원이 만든 `reliability_test.ipynb` 노트북을 **그대로 재사용**해서,
- 사용자가 **영상(mp4) + 라벨(json)** 을 드래그해서 업로드하면,
- 내부에서 `aihub/raw/{videos,labels}` 구조를 자동 구성 후 노트북을 실행,
- `reports/` 결과물을 생성하고 `reports.zip`으로 다운로드할 수 있는 Streamlit WebUI 입니다.

## Run
```bash
pip install streamlit nbformat nbclient
streamlit run webui_streamlit_app.py
```

## Notes
- 노트북의 `BASE = Path("/content")` 등을 실행 전에 자동 치환합니다.
- GPU/torch/ultralytics 등 런타임 요구사항은 노트북을 그대로 따릅니다.
- 영상/라벨 파일 수가 많거나 용량이 크면 브라우저 업로드에 시간이 걸릴 수 있습니다.
