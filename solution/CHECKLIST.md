# Checklist hoàn thành Lab Day 27 — Data Siege

Ngày rà soát: 15/10/2026. Checklist được lập từ nội dung checkout hiện tại.

Đây là tài liệu theo dõi bổ sung, **không phải deliverable được chấm điểm**. Đặt trong `solution/` để tuân thủ giới hạn chỉnh sửa của `RULES.md`. Chỉ đánh dấu `[x]` khi có bằng chứng; `[ ]` là chưa hoàn thành hoặc chưa xác minh. Các bước “khuyến nghị” hỗ trợ chất lượng bài làm, không phải yêu cầu nộp thêm của đề.

## 1. Nguồn yêu cầu và phạm vi

- [x] Đọc `README.md`: mô hình xử lý stream tuần tự, setup, scoring, ba phase và hai file cần triển khai.
- [x] Đọc `RULES.md`: private là phase tính điểm; các hành vi bị cấm; phạm vi sửa file.
- [x] Đọc `docs/SUBMIT.md`: selfcheck → private run → manifest → commit/push.
- [x] Đọc `docs/TOOLKIT_API.md`: RPC, chi phí, baseline, state và debug.
- [x] Đọc `docs/FAULT_PILLARS.md`: bốn nhóm lỗi, năm loại event và lỗi subtle.
- [x] Đối chiếu `solution/defense.py`, `solution/reflection.md`, `submission/manifest.json`, `requirements.txt`, `.gitignore`, `data/baselines.json`.
- [x] Đối chiếu mã hỗ trợ: `harness/child_env/api.py`, `harness/selfcheck.py`, `harness/toolkit/metering.py`, `harness/scoring.py`, `harness/run.py`, `harness/child_env/child_driver.py`, `harness/isolation.py`, `harness/crypto.py`, `harness/signing.py`, `harness/toolkit/__init__.py`.

Không đọc nội dung key, không tự giải mã schedule. `phases/practice_answer_key.json` được đề cho phép dùng **sau practice run** để đối chiếu; đã đối chiếu sau practice run trong đợt hoàn thành lab. Không tìm thấy rubric, slide Day 27, GUIDE hoặc bộ test riêng trong danh sách file hiện tại. `FAULT_PILLARS.md` có nhắc deck nhưng repo không kèm deck; không suy diễn thêm yêu cầu từ tài liệu chưa có.

## 2. Yêu cầu nộp bài chính thức

Nguồn: `RULES.md`, `docs/SUBMIT.md`, `README.md`.

- [x] Hoàn thiện `solution/defense.py`: logic phát hiện tổng quát, xử lý từng event khi được dispatch.
- [x] Hoàn thiện `solution/reflection.md`, tối đa một trang: loại lỗi khó nhất và lý do; điều muốn thay đổi về đánh đổi cost/coverage.
- [x] Tạo `solution/private_report.json` bằng private run chính thức; giữ nguyên kết quả và chữ ký harness tạo.
- [x] Điền `submission/manifest.json`: `team_or_student` và đúng ba đường dẫn file bài nộp.
- [x] Chạy selfcheck trên phiên bản cuối trước private run.
- [ ] Commit và push `solution/`, `submission/` lên git theo hướng dẫn nộp bài; xác nhận commit đã có trên remote.

Ba file được chấm là `defense.py`, `reflection.md`, `private_report.json`. Manifest là bước thủ tục nộp bài. Practice/public report và checklist này là tài liệu hỗ trợ; public không tính vào điểm. Tài liệu hiện có không đặt điểm đạt tối thiểu, không yêu cầu TPR tuyệt đối hoặc cost_overage bằng 0 như điều kiện đạt.

## 3. Môi trường và giới hạn thực hiện

- [x] Xác minh Python chạy được: Python 3.11.9 tại thời điểm rà soát.
- [x] Xác minh dependency `cryptography` import được: phiên bản 50.0.1; `requirements.txt` chỉ khai báo `cryptography`.
- Không áp dụng (khuyến nghị): dùng Python/dependency hiện có đã xác minh; không tạo `.venv` ngoài hai thư mục được phép chỉnh sửa.
- [x] Chỉ chỉnh sửa file trong `solution/` và `submission/`; không sửa harness, baseline, rules hoặc dữ liệu phase.
- [x] Trong defense, chỉ dùng API hợp lệ: `ctx.tools`, `ctx.baseline`, `ctx.state`, `ctx.on`, `Verdict` và stdlib được cho phép.
- [x] Không đọc file/key/schedule/harness từ defense; không tự decrypt, gọi RPC ngoài bảng tài liệu hoặc vượt sandbox.
- [x] Không hardcode đáp án theo `event_id`, seed hoặc run cụ thể, kể cả sau khi xem practice answer key.
- [x] Không `print()` ra stdout từ defense vì stdout là kênh RPC; nếu debug, dùng stderr theo API guide.
- [x] Không phụ thuộc thư viện ngoài allowlist trong defense; dependency của harness không có nghĩa defense được phép import.

Gợi ý setup trên PowerShell (từ thư mục gốc repo):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Các lệnh kiểm tra ở dưới dùng `python`; nếu sử dụng `.venv`, thay bằng `.\.venv\Scripts\python.exe`. README có lệnh tương đương cho Linux. Không có yêu cầu bắt buộc WSL/Docker/cloud trong tài liệu lab này.

## 4. Hoàn thiện giao diện và logic phát hiện

Nguồn: `README.md`, `docs/FAULT_PILLARS.md`, `docs/TOOLKIT_API.md`, `harness/child_env/api.py`, starter `solution/defense.py`.

- [x] Starter có `register(ctx)` đăng ký đủ 5/5 event type; selfcheck đã xác nhận.
- [x] Thay toàn bộ TODO/`alert=False` cố định bằng logic phát hiện thực tế.
- [x] Mỗi handler trả về đối tượng `Verdict`, với `alert` là quyết định cho event hiện tại và `pillar` phù hợp.
- [x] Xử lý kết quả RPC có khóa `error` trước khi truy cập các trường dữ liệu; không để lỗi handler âm thầm trở thành bỏ sót.
- [x] Chỉ truy vấn ID đã được dispatch; không dò event tương lai.
- [x] Khuyến nghị: dùng `reason`/`confidence` có ý nghĩa để hỗ trợ chẩn đoán; đây không phải thành phần trực tiếp trong công thức điểm.

| Event / pillar | RPC và tham số từ payload | Chi phí/lần | Tín hiệu cần triển khai và kiểm tra |
|---|---|---:|---|
| `data_batch` / `checks` | `batch_profile(payload["batch_id"])` | 1.0 | Volume, null customer ID, mean/distribution amount, freshness/staleness |
| `contract_checkpoint` / `contracts` | `contract_diff(payload["contract_id"], payload["checkpoint_batch_id"])` | 1.5 | Danh sách vi phạm schema/type và `freshness_delay_min` |
| `lineage_run` / `lineage` | `lineage_graph_slice(payload["run_id"])` | 1.0 | Thiếu upstream, orphaned output/downstream bất thường và runtime; đối chiếu kỳ vọng khi payload cung cấp, không tự bịa giá trị chuẩn |
| `feature_materialization` / `ai_infra` | `feature_drift(payload["feature_view"], payload["batch_id"])` | 2.0 | Training-serving skew qua `mean_shift_sigma` và thống kê train/serve |
| `embedding_batch` / `ai_infra` | `embedding_drift(payload["corpus"], payload["chunk_batch_id"])` | 2.0 | Centroid drift và tuổi tài liệu corpus |

- [x] Hoàn thiện và kiểm tra handler `check_data_batch`.
- [x] Hoàn thiện và kiểm tra handler `check_contract_checkpoint`.
- [x] Hoàn thiện và kiểm tra handler `check_lineage_run`.
- [x] Hoàn thiện và kiểm tra handler `check_feature_materialization`.
- [x] Hoàn thiện và kiểm tra handler `check_embedding_batch`.
- [x] Khuyến nghị: đánh giá lỗi gần biên/subtle, kết hợp tín hiệu hoặc thống kê có cơ sở; tránh chỉ tối ưu trường hợp lỗi lớn trong practice.
- [x] Khuyến nghị: dùng `ctx.state` để lưu trạng thái/cache trong một run nếu cần; không giả định state tồn tại qua nhiều run.

### Baseline công bố tại thời điểm rà soát

Nguồn: `data/baselines.json`; trong defense đọc từ `ctx.baseline`, không mở file này.

| Khóa | Giá trị |
|---|---:|
| `row_count_min` / `row_count_max` | 435.4732 / 561.2948 |
| `null_rate_max` | 0.0109 |
| `mean_amount_min` / `mean_amount_max` | 72.7645 / 90.6053 |
| `staleness_min_max` | 8.418 |
| `freshness_delay_max_min` | 11.1141 |
| `lineage_duration_ms_max` | 5134.9804 |
| `feature_mean_shift_sigma_max` | 0.4095 |
| `embedding_centroid_shift_max` | 0.0435 |
| `corpus_avg_doc_age_days_max` | 49.7955 |

Baseline là hằng số hiệu chuẩn từ clean stream, hữu ích cho sai lệch lớn; không bảo đảm bắt mọi fault subtle.

## 5. Chi phí và tối ưu điểm

Nguồn: `README.md`, `harness/scoring.py`, `harness/run.py`, toolkit guide.

```text
score = 100 × (0.5 × TPR − 0.3 × FPR − 0.2 × min(cost_overage, 1))
TPR = TP / (TP + FN)
FPR = FP / (FP + TN)
cost_overage = max(0, (cost_ledger − budget) / budget)
```

Budget hiện tại: practice = 220, public = 220, private = 320 credits. `spend_so_far()` và `budget_remaining()` miễn phí. Budget âm gây phạt điểm, không tự làm run crash. Theo công thức hiện tại, điểm lý tưởng là **50**, không phải 100; tài liệu không đưa thêm quy đổi điểm môn học.

- [x] Khuyến nghị: đo TPR, FPR và cost_overage cùng nhau; không dùng “alert mọi event” hoặc “luôn im lặng” làm lời giải cuối.
- [x] Khuyến nghị: tránh gọi cùng RPC lặp lại vô ích; cân nhắc cache kết quả theo đúng event/ref đã thấy.
- Không áp dụng (khuyến nghị): không có truy vấn metered bổ sung; chi phí được kiểm tra qua report, public vượt 20 credits và private không vượt ngân sách.
- [x] Khuyến nghị: lưu kết quả so sánh các chiến lược trong `solution/` nếu cần, không thêm yêu cầu báo cáo ngoài đề.

## 6. Xác minh theo thứ tự

### A. Selfcheck

```powershell
python -B harness/selfcheck.py
```

- [x] Chạy selfcheck trên starter: exit code 0, `OK: register(ctx) ran cleanly, 5/5 event types have a handler.`
- [x] Chạy lại trên defense đã hoàn thiện; xác nhận đủ 5/5 handler, không chỉ dựa vào exit code.

**Giới hạn bằng chứng:** selfcheck chỉ import module và chạy `register(ctx)`, không dispatch event, không gọi tool để kiểm tra thuật toán, không chứng minh sandbox runtime hoặc chất lượng phát hiện. Thiếu handler chỉ phát WARNING trong mã hiện tại. Starter ban đầu pass selfcheck dù luôn `alert=False`; bản cuối đã được kiểm thử và chạy cả ba phase.

### B. Practice — học và kiểm tra, khuyến nghị

```powershell
python -B harness/run.py --phase practice --defense solution/defense.py --out solution/practice_report.json
```

- [x] Chạy thành công toàn bộ stream bằng harness chuẩn; không tự giải mã schedule.
- [x] Xác nhận report có `result`, `signature`, `result.phase == "practice"` và `verdicts`.
- [x] Đối chiếu verdicts với `phases/practice_answer_key.json` theo `seq`; phân tích FP/FN theo lỗi/pillar khi answer key có thông tin tương ứng.
- [x] Kiểm tra các lỗi runtime/tool và quyết định gần baseline; chỉnh logic tổng quát rồi chạy lại practice khi cần.
- [x] Ghi nhận score, TPR, FPR, `cost_ledger`, budget, cost_overage và band từng pillar từ report.

### C. Public — tùy chọn, không tính điểm

```powershell
python -B harness/run.py --phase public --defense solution/defense.py --out solution/public_report.json
```

- [x] Nếu dùng public để đánh giá, chạy bằng harness chuẩn và lưu report.
- [x] Dùng score/cost và `per_pillar_band` (`high`/`medium`/`low`) để đánh giá tổng quát; không suy ra answer key hoặc hardcode theo stream.
- [x] Không xem public pass/điểm cao là bằng chứng private đã hoàn thành.

### D. Private — phase tính điểm, bắt buộc

```powershell
python -B harness/selfcheck.py
python -B harness/run.py --phase private --defense solution/defense.py --out solution/private_report.json
```

- [x] Xác nhận phase private được giảng viên cho phép chạy/key đã phát hành theo lịch; sự hiện diện của file trong checkout không tự xác nhận lịch phát hành.
- [x] Chạy private với defense cuối cùng, sau selfcheck.
- [x] Report do harness tạo có `result.phase == "private"`, `score`, `tpr`, `fpr`, `cost_overage` và `signature`.
- [x] Không chỉnh/sinh lại chữ ký thủ công hoặc sửa nội dung kết quả; không đọc key để tự xác minh chữ ký.
- [x] Giữ defense nộp bài tương ứng với phiên bản đã tạo private report; nếu thay logic, cần báo cáo hợp lệ tương ứng và tuân thủ quy định số lượt của lớp.

README mô tả private chỉ trả final score; implementation hiện tại còn xuất TPR, FPR và cost_overage, nhưng không có verdicts/per-pillar. Checklist phản ánh cả mô tả và output thực tế, không đòi private phải có chi tiết practice. Repo không nêu rõ số lượt private được phép; không tự đặt quy tắc một lượt hoặc cho rằng được chạy không giới hạn.

## 7. Reflection, manifest và nộp git

- [x] Reflection đã thay nội dung mẫu bằng nhận xét từ các run thực tế; không bịa kết quả chưa đo.
- [x] Giải thích lỗi khó, vì sao khó và đánh đổi giữa coverage, false alarms, cost; giữ trong một trang theo README.
- [x] `team_or_student` chứa định danh chính xác theo lớp; ba đường dẫn manifest trỏ đúng file tồn tại.
- [x] Kiểm tra `git status --short` và `git diff`: các thay đổi bài làm chỉ nằm trong `solution/`, `submission/`; không có key, schedule giải mã hay sửa harness.
- [x] Kiểm tra đúng ba file được chấm đã sẵn sàng và private report là bản tương ứng với defense cuối.
- [ ] Commit/push theo `docs/SUBMIT.md` và xác nhận thành công trên remote.

```powershell
git status --short
git diff -- solution/ submission/
git add solution/ submission/
git commit -m "submission"
git push
```

Trạng thái commit/push được cập nhật theo bằng chứng git ở mục 8.

## 8. Kết quả hoàn thành ngày 15/10/2026

| Hạng mục | Kết quả | Bằng chứng |
|---|---|---|
| Logic phát hiện | Hoàn thiện 5 handler; baseline, topology khai báo + học online theo job, cache RPC và xử lý error | `solution/defense.py` |
| Selfcheck cuối | PASS, 5/5 | `solution/selfcheck.log` |
| Kiểm thử hồi quy | 14/14 PASS | `solution/test_defense.py`, `solution/validation.log` |
| Practice cuối | 50/50; TP=33, FN=0, FP=0, TN=87; cost 180/220 | `solution/practice_report.json`; đối chiếu answer key theo seq |
| Public cuối | 43,84/50; TPR=92,31%, FPR=1,65%; cost 240/220; mọi pillar high | `solution/public_report.json` |
| Private cuối | 31,48/50; TPR=62,96%, FPR=0%, cost_overage=0 | `solution/private_report.json` |
| Reflection | Đã hoàn thiện; nêu giới hạn coverage và tradeoff thực tế | `solution/reflection.md` |
| Manifest | Đã điền DamQuangSon_2A202602868 và kiểm tra ba đường dẫn | `submission/manifest.json` |
| Release private | Đã có bằng chứng phát hành trong git | Commit `29ad49d` — `Release private phase` |
| Hồ sơ xác minh | Counts, báo cáo, SHA-256 defense/report và giới hạn | `solution/validation_summary.json` |
| Commit/push | Đang thực hiện; chưa xác nhận remote | Cập nhật sau khi push |

Private đã chạy hai lần: lần đầu 26,85; sau khi sửa missing-upstream dựa trên hai FN **practice**, lần cuối 31,48. Báo cáo lần đầu được giữ nguyên tại `solution/private_initial_report.json` để truy vết, không phải file chấm điểm trong manifest. Chữ ký các report do harness chuẩn tạo; chỉ kiểm tra cấu trúc, không đọc key để xác minh HMAC độc lập. Một lượt debug practice chỉ chuyển stderr của child ra console, không thay đổi scoring hoặc dữ liệu; debug đã được gỡ khỏi defense cuối.

Giới hạn: private vẫn bỏ sót lỗi, public bị phạt chi phí. Baseline 3σ chưa đủ coverage cho mọi trường hợp subtle. Topology học online có thể chưa biết dependency ở lần đầu, hoặc báo sai nếu producer bỏ dependency hợp lệ mà không đổi version. Không tuyên bố đạt điểm tối đa/private acceptance ngoài kết quả thực đo; kit không nêu điểm đạt tối thiểu hoặc quy đổi điểm môn học. Checklist, test, log, báo cáo practice/public và bản private cũ là tài liệu bổ sung; ba file chấm điểm vẫn theo `docs/SUBMIT.md`.
