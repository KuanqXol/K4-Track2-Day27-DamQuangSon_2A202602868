# Reflection — Data Siege

## Loại lỗi khó nhất

Defense xử lý đủ năm loại event bằng một truy vấn metered cho mỗi event mới,
đối chiếu baseline công bố và topology được khai báo ngay trong event. Practice
cuối đạt 50/50: bắt đủ 33 lỗi, không cảnh báo sai, dùng 180/220 credits. Khi phát
triển, việc chỉ kiểm tra upstream rỗng đã bỏ sót hai lỗi missing-upstream.
`inputs` chỉ khai báo một phần lineage, nên cần kết hợp khai báo với topology
đã quan sát của cùng job trong `ctx.state`. Cách này bắt được hai lỗi trên mà
không hardcode topology/ID. Kiểm thử riêng xác nhận mất input, mất upstream đã
quan sát, tách trạng thái giữa job và schema version. Job chưa có lịch sử vẫn
có thể bỏ sót dependency không nằm trong khai báo.

Thách thức còn lại là các sai lệch subtle gần vùng biến thiên sạch. Public đạt
43,84/50, TPR 92,31%, FPR 1,65%; private đạt 31,48/50, TPR 62,96%, FPR 0%,
cost_overage 0. Khoảng cách này cho thấy ngưỡng bảo thủ có coverage chưa đủ trên
stream private. Report private không cung cấp breakdown theo loại lỗi, nên tôi
không thể kết luận chính xác pillar nào bị bỏ sót hoặc khẳng định mọi FN đều là
subtle. Bản sửa lineage xuất phát từ FP/FN practice; report private cuối được
tạo lại sau thay đổi này. Defense không chứa bảng đáp án theo seed/event ID.

## Đánh đổi cost/coverage và hướng cải thiện

Một truy vấn/event giúp kiểm tra mọi pillar; cache theo method và arguments tránh
tính phí lại khi cùng ref được xử lý lặp. Public dùng 240/220 credits, bị phạt
overage 9,09%; private không bị phạt. Tôi giữ coverage thay vì ngừng truy vấn khi
hết budget public. Lỗi RPC trả verdict confidence 0 với reason rõ ràng, không bị
coi mặc định là fault dữ liệu.

Nếu có vòng phát triển tiếp, tôi sẽ so sánh baseline với mô hình robust cập nhật
online trong `ctx.state`, kết hợp nhiều tín hiệu yếu và chọn ngưỡng bằng dữ liệu
holdout được phép, đo đồng thời TPR/FPR/cost. Cần kiểm soát warm-up, contamination
do fault và false alarms; không tùy tiện hạ ngưỡng để khớp một stream. Bản hiện
tại giữ baseline đã công bố; 14 kiểm thử hồi quy đạt nhưng không chứng minh đã
bắt hết các lỗi tinh vi. Điểm tối đa theo công thức lab là 50.
